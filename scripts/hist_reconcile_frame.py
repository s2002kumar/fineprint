"""Historical plan amendment A1: reconcile source A (DailyMed labeler search) with source D
(archived pre-cutoff FDA NDC Directory) for Hospira labeler segment 0409.

HISTORICAL DOMAIN ONLY: nothing here touches the national database, and no outcome
document is read. Coverage diagnosis only; no frame is frozen.

  python -I scripts/hist_reconcile_frame.py --config config/dst00_targets.json \
      --out evidence/historical/frame_reconcile.json
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
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import bulk, config, dailymed, net, safezip  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402

PAUSE = 0.4
CDX = ("https://web.archive.org/cdx/search/cdx?url=accessdata.fda.gov/cder/ndcxls.zip&from={y0}&to={y1}"
       "&output=json&fl=timestamp,original,statuscode,digest,length")
RAW = "https://web.archive.org/web/{ts}id_/{original}"


class Fetcher:
    def __init__(self, root):
        self.root = root
        self.log = []

    def get(self, url, rel):
        dest = self.root / rel
        if dest.exists() and (dest.with_name(dest.name + ".prov.json")).exists():
            prov = json.loads(dest.with_name(dest.name + ".prov.json").read_text(encoding="utf-8"))
        else:
            r = net.fetch(url, dest)
            time.sleep(PAUSE)
            prov = r.provenance()
            dest.with_name(dest.name + ".prov.json").write_text(json.dumps(prov), encoding="utf-8", newline="\n")
        self.log.append({"url": url, "sha256": prov["sha256"], "bytes": prov["bytes"],
                         "retrieved_at": prov["retrieved_at"]})
        return dest, prov


def history(f, sid):
    rows, page = [], 1
    while True:
        p, _ = f.get(dailymed.HISTORY.format(setid=sid, page=page), f"history/{sid}.p{page}.json")
        d = json.loads(p.read_text(encoding="utf-8"))
        rows += d["data"]["history"]
        if int(d["metadata"]["current_page"]) >= int(d["metadata"]["total_pages"]):
            return sorted(({"version": int(h["spl_version"]),
                            "published_at": dailymed.parse_history_date(h["published_date"])} for h in rows),
                          key=lambda v: v["version"])
        page += 1


def fetch_version(f, sid, version):
    p, prov = f.get(dailymed.GETFILE_VERSION.format(setid=sid, version=version), f"spl/{sid}_v{version}.zip")
    opened = bulk.open_nested(f"historical/{sid}_v{version}.zip", p.read_bytes())
    doc = opened["doc"]
    if doc is None:
        return {"set_id": sid, "version": version, "failure": opened["failure"], "zip_sha256": prov["sha256"]}
    prods = [x["product_ndc_raw"] for x in doc["products"] if x["product_ndc_raw"]]
    pkgs = [k["package_ndc_raw"] for x in doc["products"] for k in x["packages"] if k["package_ndc_raw"]]
    return {"set_id": sid, "version": version, "zip_sha256": prov["sha256"], "xml_sha256": doc["xml_sha256"],
            "document_id": (doc["document_id"] or "").lower(), "served_set_id": doc["set_id"],
            "served_version": doc["version"], "product_ndcs": sorted(set(prods)), "package_ndcs": sorted(set(pkgs)),
            "labeler_segments": sorted({c.split("-")[0] for c in prods})}


def load_d(f, cutoff):
    cp, _ = f.get(CDX.format(y0=int(cutoff[:4]) - 1, y1=cutoff[:4]), "ndc/cdx.json")
    caps = json.loads(cp.read_text(encoding="utf-8"))
    caps = [dict(zip(caps[0], c)) for c in caps[1:]] if caps else []
    ok = sorted((c for c in caps if c["statuscode"] == "200" and c["timestamp"][:8] <= cutoff.replace("-", "")),
                key=lambda c: c["timestamp"])
    cap = ok[-1]
    zp, prov = f.get(RAW.format(ts=cap["timestamp"], original=cap["original"]), f"ndc/ndcxls_{cap['timestamp']}.zip")
    digest_ok = base64.b32encode(hashlib.sha1(zp.read_bytes()).digest()).decode() == cap["digest"]
    tables, mtimes = {}, {}
    with zipfile.ZipFile(zp) as zf:
        for info in zf.infolist():
            lines = safezip.read_member(zf, info, 256 << 20).decode("latin-1").splitlines()
            hdr = lines[0].split("\t")
            tables[info.filename.lower()] = [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:] if ln.strip()]
            mtimes[info.filename.lower()] = "%04d-%02d-%02d" % info.date_time[:3]
    prods = [p for p in tables["product.xls"] if p["PRODUCTNDC"].split("-")[0] == "0409"]
    pkgs = [p for p in tables["package.xls"] if p["NDCPACKAGECODE"].split("-")[0] == "0409"]
    by_doc = defaultdict(lambda: {"product_ndcs": set(), "package_ndcs": set(), "names": set()})
    for p in prods:
        d = by_doc[p["PRODUCTID"].split("_", 1)[1].lower()]
        d["product_ndcs"].add(p["PRODUCTNDC"])
        d["names"].add(p.get("PROPRIETARYNAME", ""))
    for k in pkgs:
        by_doc[k["PRODUCTID"].split("_", 1)[1].lower()]["package_ndcs"].add(k["NDCPACKAGECODE"])
    snapshot = min(mtimes.values())
    return {"capture": cap, "zip_sha256": prov["sha256"], "archive_digest_matches": digest_ok,
            "member_dates": mtimes, "snapshot_date": snapshot, "by_doc": by_doc,
            "n_products": len({p["PRODUCTNDC"] for p in prods}), "n_packages": len({k["NDCPACKAGECODE"] for k in pkgs})}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--labeler", default="Hospira")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    cutoff = json.loads(a.config.read_text(encoding="utf-8"))["cutoff"]
    f = Fetcher(config.data_dir() / "raw" / "historical" / "frame_reconcile")
    started = net.utc_now()

    D = load_d(f, cutoff)
    snap = D["snapshot_date"]
    print("D snapshot", snap, "docs", len(D["by_doc"]), file=sys.stderr)

    hits, page = [], 1
    while True:
        qs = urllib.parse.urlencode({"labeler": a.labeler, "pagesize": 100, "page": page})
        p, _ = f.get(f"{dailymed.SPLS_SEARCH}?{qs}", f"search/labeler_{a.labeler}_p{page}.json")
        d = json.loads(p.read_text(encoding="utf-8"))
        hits += d["data"]
        if int(d["metadata"]["current_page"]) >= int(d["metadata"]["total_pages"]):
            break
        page += 1
    a_sets = sorted({h["setid"] for h in hits})

    A, a_reason = {}, {}
    for sid in a_sets:
        vers = history(f, sid)
        at_snap = dailymed.latest_admissible(vers, snap)
        adm = dailymed.latest_admissible(vers, cutoff)
        if at_snap is None:
            a_reason[sid] = "first_published_after_snapshot" if adm else "first_published_after_cutoff"
            A[sid] = {"versions": vers, "at_snapshot": None}
            continue
        A[sid] = {"versions": vers, "at_snapshot": fetch_version(f, sid, at_snap["version"])}
    print("A fetched", len(A), file=sys.stderr)

    doc_to_set = {v["at_snapshot"]["document_id"]: sid for sid, v in A.items()
                  if v["at_snapshot"] and "document_id" in v["at_snapshot"]}
    prod_to_sets = defaultdict(set)
    for sid, v in A.items():
        for c in (v["at_snapshot"] or {}).get("product_ndcs", []):
            prod_to_sets[c].add(sid)

    rows, neighbor_fetches = [], 0
    for doc_id, dd in sorted(D["by_doc"].items()):
        r = {"d_document_id": doc_id, "d_product_ndcs": sorted(dd["product_ndcs"]),
             "d_package_count": len(dd["package_ndcs"])}
        if doc_id in doc_to_set:
            r.update(cls="matched_document_id", a_set_id=doc_to_set[doc_id])
        else:
            sets = sorted({s for c in dd["product_ndcs"] for s in prod_to_sets.get(c, ())})
            if sets:
                r.update(cls="a_product_ndc_other_version", a_set_ids=sets, neighbor_match=None)
                for sid in sets:  # one look at the neighbouring admissible versions
                    vs = A[sid]["versions"]
                    cur = A[sid]["at_snapshot"]["version"]
                    for nv in [v for v in vs if v["published_at"] <= cutoff and v["version"] != cur]:
                        if abs(vs.index(nv) - [v["version"] for v in vs].index(cur)) != 1:
                            continue
                        neighbor_fetches += 1
                        got = fetch_version(f, sid, nv["version"])
                        if got.get("document_id") == doc_id:
                            r["neighbor_match"] = {"set_id": sid, "version": nv["version"],
                                                   "published_at": nv["published_at"]}
            else:
                r["cls"] = "absent_from_a"
                found = []
                for c in sorted(dd["product_ndcs"]):
                    qs = urllib.parse.urlencode({"ndc": c, "pagesize": 100})
                    p, _ = f.get(f"{dailymed.SPLS_SEARCH}?{qs}", f"search/ndc_{c}.json")
                    for x in json.loads(p.read_text(encoding="utf-8")).get("data", []):
                        found.append({"ndc": c, "set_id": x["setid"], "title_labeler":
                                      (re.search(r"\[([^\]]+)\]\s*$", x["title"] or "") or [None, None])[1]})
                r["current_dailymed_ndc_search"] = found
        rows.append(r)

    cls = Counter(r["cls"] for r in rows)
    absent = [r for r in rows if r["cls"] == "absent_from_a"]
    a_matched = {r["a_set_id"] for r in rows if r["cls"] == "matched_document_id"}
    for sid, v in A.items():
        if sid in a_reason or sid in a_matched:
            continue
        snapv = v["at_snapshot"]
        if snapv.get("failure"):
            a_reason[sid] = "fetch_or_parse_failure"
        elif "0409" not in snapv["labeler_segments"]:
            a_reason[sid] = f"no_0409_ndc (segments {','.join(snapv['labeler_segments']) or 'none'})"
        elif any(sid in r.get("a_set_ids", []) for r in rows):
            a_reason[sid] = "listed_in_d_under_a_different_document_id"
        else:
            a_reason[sid] = "0409_set_not_in_d_snapshot"
    summary = {
        "snapshot_date_fda": snap, "cutoff": cutoff,
        "d_documents_0409": len(D["by_doc"]), "d_products_0409": D["n_products"], "d_packages_0409": D["n_packages"],
        "a_set_ids_returned_now": len(a_sets),
        "a_set_ids_with_version_at_snapshot": sum(1 for v in A.values() if v["at_snapshot"]),
        "d_documents_by_class": dict(cls),
        "d_other_version_resolved_by_neighbor": sum(1 for r in rows if r.get("neighbor_match")),
        "d_absent_from_a": len(absent),
        "d_absent_found_in_current_dailymed_by_ndc": sum(1 for r in absent if r["current_dailymed_ndc_search"]),
        "d_absent_packages": sum(r["d_package_count"] for r in absent),
        "absent_found_under_labelers": dict(Counter(x["title_labeler"] for r in absent
                                                    for x in r["current_dailymed_ndc_search"])),
        "a_sets_not_matched_by_reason": dict(Counter(a_reason.values())),
        "neighbor_version_fetches": neighbor_fetches,
    }
    write_json(a.out, {"run": {"started_at": started, "finished_at": net.utc_now(),
                               "plan": "docs/historical_panel_plan.md amendment A1", "outcome_data_used": False},
                       "d_source": {k: D[k] for k in ("capture", "zip_sha256", "archive_digest_matches",
                                                      "member_dates", "snapshot_date")},
                       "summary": summary, "d_rows": rows,
                       "a_sets": {sid: {"at_snapshot": v["at_snapshot"], "reason_if_unmatched": a_reason.get(sid),
                                        "n_versions": len(v["versions"])} for sid, v in A.items()},
                       "fetch_log": f.log})
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
