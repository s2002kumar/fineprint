"""DST-00 pilot permitted by docs/historical_panel_plan.md section 8 (no frame freeze).

Source A: DailyMed v2 spls.json?labeler=<name> (all pages) -> per-set history ->
          does an admissible (published <= cutoff) version exist?  Set-ID level only.
Source D: FDA NDC Directory capture (Internet Archive) taken on/before the cutoff ->
          count package NDCs with raw labeler segment 0409.
No SPL XML is downloaded, nothing is linked to a facility, and no outcome document
is touched.

Usage:
  python -I scripts/dst00_frame_pilot.py --config config/dst00_targets.json \
      --labeler Hospira --data-dir <dir> --out evidence/dst00/frame_pilot.json
"""

import argparse
import base64
import hashlib
import json
import re
import sys
import time
import urllib.parse
import zipfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import dailymed, net, safezip  # noqa: E402
from fineprint.manifest import source_record, write_json  # noqa: E402

PAUSE_S = 0.4
NDC_CDX = ("https://web.archive.org/cdx/search/cdx?url=accessdata.fda.gov/cder/{name}"
           "&from={y0}&to={y1}&output=json&fl=timestamp,original,statuscode,digest,length")
WAYBACK_RAW = "https://web.archive.org/web/{ts}id_/{original}"


def source_a(labeler, cutoff, data_dir, sources):
    hits, page = [], 1
    while True:
        qs = urllib.parse.urlencode({"labeler": labeler, "pagesize": 100, "page": page})
        r = net.fetch(f"{dailymed.SPLS_SEARCH}?{qs}", data_dir / "search" / f"labeler_{labeler}_p{page}.json")
        time.sleep(PAUSE_S)
        sources.append(source_record(r, kind="dailymed_spls_search_json", role="documentation",
                                     data_dir=data_dir, query={"labeler": labeler, "page": page}))
        d = json.loads(Path(r.path).read_text(encoding="utf-8"))
        hits += d["data"]
        if int(d["metadata"]["current_page"]) >= int(d["metadata"]["total_pages"]):
            total = d["metadata"]["total_elements"]
            break
        page += 1
    rows = []
    for h in hits:
        sid = h["setid"]
        r = net.fetch(dailymed.HISTORY.format(setid=sid, page=1), data_dir / "history" / f"{sid}.json")
        time.sleep(PAUSE_S)
        hd = json.loads(Path(r.path).read_text(encoding="utf-8"))
        if int(hd["metadata"]["total_pages"]) > 1:
            raise RuntimeError(f"history paging >1 for {sid}; extend pilot")
        versions = [{"version": int(x["spl_version"]), "published_at": dailymed.parse_history_date(x["published_date"])}
                    for x in hd["data"]["history"]]
        adm = dailymed.latest_admissible(versions, cutoff)
        m = re.search(r"\[([^\]]+)\]\s*$", h["title"] or "")
        rows.append({"set_id": sid, "title_labeler": m.group(1) if m else None,
                     "current_version": int(h["spl_version"]), "versions_listed": len(versions),
                     "history_sha256": r.sha256,
                     "latest_admissible": adm, "first_published": min(v["published_at"] for v in versions)})
    return total, rows


def source_d(cutoff, data_dir, sources):
    y0, y1 = int(cutoff[:4]) - 1, cutoff[:4]
    caps = []
    for name in ("ndcxls.zip", "ndctext.zip"):
        r = net.fetch(NDC_CDX.format(name=name, y0=y0, y1=y1))
        sources.append(source_record(r, kind="internet_archive_cdx_listing", role="documentation"))
        rows = json.loads(r.body.decode("utf-8"))
        caps += [dict(zip(rows[0], c)) for c in rows[1:]] if rows else []
    ok = sorted((c for c in caps if c["statuscode"] == "200" and c["timestamp"][:8] <= cutoff.replace("-", "")),
                key=lambda c: c["timestamp"])
    if not ok:
        return {"failure": "no HTTP-200 NDC Directory capture on/before cutoff", "captures": caps}
    cap = ok[-1]
    ts = cap["timestamp"]
    captured = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}T{ts[8:10]}:{ts[10:12]}:{ts[12:14]}Z"
    r = net.fetch(WAYBACK_RAW.format(ts=ts, original=cap["original"]),
                  data_dir / "ndc_archived" / f"{Path(cap['original']).name}_{ts}.zip")
    digest_ok = base64.b32encode(hashlib.sha1(Path(r.path).read_bytes()).digest()).decode() == cap["digest"]
    members = {}
    with zipfile.ZipFile(r.path) as zf:
        scan = safezip.scan_directory(zf)
        for info in zf.infolist():
            raw = safezip.read_member(zf, info, 256 << 20)
            members[info.filename.lower()] = (info, raw)
    sources.append(source_record(r, kind="fda_ndc_directory_archived_copy", role="historical", data_dir=data_dir,
                                 captured_at=captured, published_at=None,
                                 published_at_basis="not stated; FDA member zip_mtime recorded",
                                 archive_cdx_digest_sha1_b32=cap["digest"], archive_digest_matches=digest_ok,
                                 original_url=cap["original"],
                                 members={k: {"bytes": v[0].file_size,
                                              "zip_mtime": "%04d-%02d-%02dT%02d:%02d:%02d" % v[0].date_time,
                                              "sha256": hashlib.sha256(v[1]).hexdigest()} for k, v in members.items()}))

    def table(stem):
        key = next(k for k in members if k.startswith(stem))
        lines = members[key][1].decode("latin-1").splitlines()
        hdr = lines[0].split("\t")
        return [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:] if ln.strip()]

    prods = {p["PRODUCTID"]: p for p in table("product")}
    pk = [p for p in table("package") if p["NDCPACKAGECODE"].split("-")[0] == "0409"]
    cut = cutoff.replace("-", "")
    ended = [p for p in pk if p.get("ENDMARKETINGDATE") and p["ENDMARKETINGDATE"] <= cut]
    types = Counter(prods.get(p["PRODUCTID"], {}).get("PRODUCTTYPENAME") for p in pk)
    labelers = Counter(prods.get(p["PRODUCTID"], {}).get("LABELERNAME") for p in pk)
    return {
        "captured_at": captured, "original_url": cap["original"], "sha256": r.sha256,
        "archive_digest_matches": digest_ok, "zip_scan_flagged": scan["flagged"],
        "member_mtimes": {k: "%04d-%02d-%02dT%02d:%02d:%02d" % v[0].date_time for k, v in members.items()},
        "packages_labeler_segment_0409": len(pk),
        "distinct_package_ndcs_0409": len({p["NDCPACKAGECODE"] for p in pk}),
        "distinct_product_ndcs_0409": len({p["PRODUCTNDC"] for p in pk}),
        "distinct_spl_document_ids_0409": len({p["PRODUCTID"].split("_", 1)[-1] for p in pk}),
        "packages_with_end_marketing_on_or_before_cutoff": len(ended),
        "package_ndc_patterns": dict(Counter("-".join(str(len(s)) for s in p["NDCPACKAGECODE"].split("-")) for p in pk)),
        "product_type_of_0409_packages": dict(types),
        "labeler_names_of_0409_packages": dict(labelers),
        "caveat": ("Archived copy of the FDA NDC Directory (listed, finished, non-excluded products) "
                   "~2.5 months before cutoff; a listing census, not a DailyMed label census."),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--labeler", default="Hospira")
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    cutoff = json.loads(a.config.read_text(encoding="utf-8"))["cutoff"]
    sources = []
    started = net.utc_now()
    total, rows = source_a(a.labeler, cutoff, a.data_dir, sources)
    adm = [r for r in rows if r["latest_admissible"]]
    a_summary = {
        "query": {"labeler": a.labeler}, "search_total_elements": total, "set_ids_returned": len(rows),
        "set_ids_with_admissible_version": len(adm),
        "set_ids_first_published_after_cutoff": len(rows) - len(adm),
        "title_labelers": dict(Counter(r["title_labeler"] for r in rows)),
        "title_labelers_with_admissible_version": dict(Counter(r["title_labeler"] for r in adm)),
        "latest_admissible_published_year": dict(sorted(Counter(r["latest_admissible"]["published_at"][:4]
                                                                for r in adm).items())),
        "caveat": ("Set IDs DailyMed serves in 2026 only; set IDs retired before 2026 are invisible here "
                   "(survivorship). Labeler segment 0409 is unknown until each admissible XML is fetched."),
    }
    d_summary = source_d(cutoff, a.data_dir, sources)
    write_json(a.out, {"run": {"started_at": started, "finished_at": net.utc_now(), "cutoff": cutoff,
                               "plan": "docs/historical_panel_plan.md section 8"},
                       "source_a": a_summary, "source_a_rows": rows, "source_d": d_summary, "sources": sources})
    print(json.dumps({"source_a": {k: v for k, v in a_summary.items() if k != "caveat"},
                      "source_d": {k: v for k, v in d_summary.items() if k not in ("caveat",)}}, indent=1))


if __name__ == "__main__":
    main()
