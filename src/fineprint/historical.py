"""HISTORICAL-domain helpers (pre-2023-07-18 evidence). Never used by the national schema.

Every fetch is cached on disk with its provenance, so reruns are reproducible and the
historical source manifest lists exactly what was read. Outcome documents are refused.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import time
import urllib.error
import zipfile
from pathlib import Path

from . import bulk, dailymed, net, safezip, spl

PAUSE = 0.4
FDA_SPL_BY_DOCID = "https://www.accessdata.fda.gov/spl/data/{docid}/{docid}.xml"
SEALED = ("fda.gov/media/170647",)  # Pfizer outcome appendix: sealed until the frame freeze


class Sealed(RuntimeError):
    pass


class Fetcher:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.log: list[dict] = []

    def get(self, url: str, rel: str, *, role: str, missing_ok: bool = False):
        if any(s in url for s in SEALED):
            raise Sealed(f"refusing sealed outcome source: {url}")
        dest = self.root / rel
        prov_path = dest.with_name(dest.name + ".prov.json")
        if dest.exists() and prov_path.exists():
            prov = json.loads(prov_path.read_text(encoding="utf-8"))
        elif prov_path.exists() and json.loads(prov_path.read_text(encoding="utf-8")).get("missing"):
            prov = json.loads(prov_path.read_text(encoding="utf-8"))
        else:
            try:
                r = net.fetch(url, dest)
                prov = r.provenance()
            except urllib.error.HTTPError as e:
                if not missing_ok:
                    raise
                prov = {"url": url, "status": e.code, "missing": True, "retrieved_at": net.utc_now()}
            time.sleep(PAUSE)
            prov_path.parent.mkdir(parents=True, exist_ok=True)
            prov_path.write_text(json.dumps(prov), encoding="utf-8", newline="\n")
        self.log.append({"url": url, "role": role, "status": prov.get("status"), "sha256": prov.get("sha256"),
                         "bytes": prov.get("bytes"), "retrieved_at": prov.get("retrieved_at"),
                         "missing": bool(prov.get("missing"))})
        return (None if prov.get("missing") else dest), prov


def history(f: Fetcher, set_id: str) -> list[dict] | None:
    """All versions with DailyMed published dates, or None if the service has no history."""
    rows, page = [], 1
    while True:
        p, _ = f.get(dailymed.HISTORY.format(setid=set_id, page=page), f"history/{set_id}.p{page}.json",
                     role="documentation", missing_ok=True)
        if p is None:
            return None
        d = json.loads(p.read_text(encoding="utf-8"))
        hist = (d.get("data") or {}).get("history") or []
        rows += hist
        meta = d.get("metadata") or {}
        if not hist or int(meta.get("current_page", 1)) >= int(meta.get("total_pages", 1)):
            break
        page += 1
    if not rows:
        return None
    return sorted(({"version": int(h["spl_version"]), "published_at": dailymed.parse_history_date(h["published_date"])}
                   for h in rows), key=lambda v: v["version"])


def summarize(doc: dict, *, labeler_segment: str) -> dict:
    """Package-level view of one parsed SPL (raw values kept)."""
    edges = spl.operation_edges(doc)
    mfg_codes = {e["product_code"] for e in edges if e["operation_code"] == spl.MANUFACTURE_CODE and e["duns"]}
    products = []
    for p in doc["products"]:
        code = p["product_ndc_raw"]
        products.append({
            "product_ndc_raw": code, "name": p["name"], "form": p["form"],
            "routes": [r["display_name"] for r in p["routes"]], "marketing": p["marketing"],
            "has_manufacture_assertion": code in mfg_codes,
            "packages": [{"package_ndc_raw": k["package_ndc_raw"], "level": k["level"], "form": k["form"],
                          "marketing": k["marketing"]} for k in p["packages"]],
            "in_scope": bool(code) and code.split("-")[0] == labeler_segment,
        })
    return {"set_id": doc["set_id"], "version": doc["version"], "document_id": (doc["document_id"] or "").lower(),
            "effective_time": doc["effective_time"], "xml_sha256": doc["xml_sha256"],
            "has_establishment_block": bool(spl.establishments(doc)), "products": products}


def fetch_version(f: Fetcher, set_id: str, version: int, *, labeler_segment: str) -> dict:
    p, prov = f.get(dailymed.GETFILE_VERSION.format(setid=set_id, version=version), f"spl/{set_id}_v{version}.zip",
                    role="historical", missing_ok=True)
    if p is None:
        return {"failure": f"http_{prov.get('status')}"}
    opened = bulk.open_nested(f"historical/{set_id}_v{version}.zip", p.read_bytes())
    if opened["doc"] is None:
        return {"failure": opened["failure"], "zip_sha256": prov["sha256"]}
    s = summarize(opened["doc"], labeler_segment=labeler_segment)
    s.update(zip_sha256=prov["sha256"], served_matches_request=(
        (s["set_id"] or "").lower() == set_id.lower() and str(s["version"]) == str(version)))
    return s


def fetch_by_document_id(f: Fetcher, docid: str, *, labeler_segment: str) -> dict:
    p, prov = f.get(FDA_SPL_BY_DOCID.format(docid=docid), f"fda_spl/{docid}.xml", role="historical", missing_ok=True)
    if p is None:
        return {"failure": f"http_{prov.get('status')}"}
    try:
        doc = spl.parse_spl(io.BytesIO(p.read_bytes()))
    except Exception as e:  # recorded per document, never fatal
        return {"failure": f"{type(e).__name__}: {e}", "xml_sha256": prov.get("sha256")}
    s = summarize(doc, labeler_segment=labeler_segment)
    s["served_matches_request"] = s["document_id"] == docid.lower()
    return s


def load_ndc_directory(f: Fetcher, cutoff: str, labeler_segment: str) -> dict:
    cdx_url = ("https://web.archive.org/cdx/search/cdx?url=accessdata.fda.gov/cder/ndcxls.zip"
               f"&from={int(cutoff[:4]) - 1}&to={cutoff[:4]}&output=json&fl=timestamp,original,statuscode,digest,length")
    cp, _ = f.get(cdx_url, "ndc/cdx.json", role="documentation")
    caps = json.loads(cp.read_text(encoding="utf-8"))
    caps = [dict(zip(caps[0], c)) for c in caps[1:]] if caps else []
    cap = sorted((c for c in caps if c["statuscode"] == "200" and c["timestamp"][:8] <= cutoff.replace("-", "")),
                 key=lambda c: c["timestamp"])[-1]
    zp, prov = f.get(f"https://web.archive.org/web/{cap['timestamp']}id_/{cap['original']}",
                     f"ndc/ndcxls_{cap['timestamp']}.zip", role="historical")
    digest_ok = base64.b32encode(hashlib.sha1(zp.read_bytes()).digest()).decode() == cap["digest"]
    tables, mtimes = {}, {}
    with zipfile.ZipFile(zp) as zf:
        for info in zf.infolist():
            lines = safezip.read_member(zf, info, 256 << 20).decode("latin-1").splitlines()
            hdr = lines[0].split("\t")
            tables[info.filename.lower()] = [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:] if ln.strip()]
            mtimes[info.filename.lower()] = "%04d-%02d-%02d" % info.date_time[:3]
    by_doc: dict[str, dict] = {}
    for k in tables["package.xls"]:
        if k["NDCPACKAGECODE"].split("-")[0] != labeler_segment:
            continue
        d = by_doc.setdefault(k["PRODUCTID"].split("_", 1)[1].lower(), {"product_ndcs": set(), "packages": {}})
        d["product_ndcs"].add(k["PRODUCTNDC"])
        d["packages"][k["NDCPACKAGECODE"]] = {"start": k.get("STARTMARKETINGDATE"), "end": k.get("ENDMARKETINGDATE")}
    return {"capture": cap, "zip_sha256": prov["sha256"], "archive_digest_matches": digest_ok, "member_dates": mtimes,
            "snapshot_date": min(mtimes.values()), "by_doc": by_doc}
