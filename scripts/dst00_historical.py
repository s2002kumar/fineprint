"""DST-00 step 1-2: fetch exact archived SPL versions and inspect establishment operations.

Usage:
  python -I scripts/dst00_historical.py --config config/dst00_targets.json \
      --data-dir <raw data dir> --out evidence/dst00/historical_spl.json \
      --fixtures tests/fixtures/historical

Only the documented version endpoint (getFile.cfm?type=zip&setid=&version=) is used;
the downloaded XML's own setId/versionNumber must match the request or the
document is reported as a failure. A current label is never used as a stand-in.
"""

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import dailymed, net, safezip, spl  # noqa: E402
from fineprint.manifest import source_record, write_json  # noqa: E402

PAUSE_S = 0.5


def get_history(set_id, data_dir, sources):
    rows, page = [], 1
    while True:
        url = dailymed.HISTORY.format(setid=set_id, page=page)
        r = net.fetch(url, data_dir / "history" / f"{set_id}.p{page}.json")
        time.sleep(PAUSE_S)
        sources.append(source_record(r, kind="dailymed_spl_history_json", role="documentation",
                                     data_dir=data_dir, set_id=set_id))
        d = json.loads(Path(r.path).read_text(encoding="utf-8"))
        rows += d["data"]["history"]
        meta = d["metadata"]
        if int(meta["current_page"]) >= int(meta["total_pages"]):
            title = d["data"]["spl"].get("title")
            break
        page += 1
    versions = sorted(({"version": int(h["spl_version"]),
                        "published_at": dailymed.parse_history_date(h["published_date"])} for h in rows),
                      key=lambda h: h["version"])
    return {"title": title, "db_published_date": meta.get("db_published_date"), "versions": versions}


def resolve_pre_cutoff(history, cutoff):
    return dailymed.latest_admissible(history["versions"], cutoff)


def summarize_org(o):
    ops = {}
    for op in o["operations"]:
        key = f'{op["display_name"]} ({op["code"]})'
        ops.setdefault(key, []).extend(pc["code"] for pc in op["product_codes"])
    return {"role": o["role"], "name": o["name"], "duns": o["duns"], "fei": o["fei"],
            "address": o["address"], "loc": o["loc"],
            "operations": {k: sorted(set(v)) for k, v in sorted(ops.items())}}


def inspect_zip(path, want_set_id, want_version, sites):
    out = {"failures": []}
    with zipfile.ZipFile(path) as zf:
        scan = safezip.scan_directory(zf)
        out["zip_scan"] = {k: scan[k] for k in ("members", "compressed_bytes", "uncompressed_bytes",
                                                "duplicate_names", "flagged")}
        xmls = [i for i in zf.infolist() if i.filename.lower().endswith(".xml")]
        out["xml_members"] = [i.filename for i in xmls]
        if len(xmls) != 1:
            out["failures"].append(f"expected exactly 1 XML member, found {len(xmls)}")
            if not xmls:
                return out, None
        info = xmls[0]
        if scan["flagged"].get(info.filename):
            out["failures"].append(f"unsafe xml member {scan['flagged'][info.filename]}")
            return out, None
        with safezip.open_member(zf, info, safezip.DEFAULT_LIMITS.max_xml_bytes) as fh:
            doc = spl.parse_spl(fh)
        xml_bytes = zf.read(info)
    out["xml"] = {"member": info.filename, "sha256": doc["xml_sha256"], "bytes": doc["xml_bytes"]}
    out["document"] = {k: doc[k] for k in ("document_id", "document_type_code", "document_type",
                                           "set_id", "version", "effective_time")}
    out["identity_check"] = {"set_id_matches": doc["set_id"] == want_set_id,
                             "version_matches": doc["version"] == str(want_version)}
    if not all(out["identity_check"].values()):
        out["failures"].append("served XML does not match requested set_id/version")
    out["organizations"] = [summarize_org(o) for o in doc["organizations"]]
    out["products"] = [{"product_ndc_raw": p["product_ndc_raw"], "name": p["name"], "form": p["form"],
                        "routes": [r["display_name"] for r in p["routes"]],
                        "approvals": p["approvals"], "loc": p["loc"],
                        "packages": [{"package_ndc_raw": k["package_ndc_raw"], "form": k["form"],
                                      "level": k["level"], "contains": k["contains"],
                                      "marketing": k["marketing"]} for k in p["packages"]],
                        "parts": len(p["parts"])} for p in doc["products"]]
    out["anomalies"] = doc["anomalies"]
    edges = spl.operation_edges(doc)
    findings = {}
    for site, ids in sites.items():
        site_edges = [e for e in edges if e["duns"] == ids["duns"]]
        by_op = {}
        for e in site_edges:
            by_op.setdefault(e["operation"], []).append({"product_code": e["product_code"], "loc": e["loc"]})
        findings[site] = {"duns": ids["duns"], "operations": by_op,
                          "manufacture_product_codes": sorted({e["product_code"] for e in site_edges
                                                               if e["operation_code"] == spl.MANUFACTURE_CODE})}
    out["site_findings"] = findings
    product_codes = {p["product_ndc_raw"] for p in doc["products"]}
    mfg_any = {e["product_code"] for e in edges if e["operation_code"] == spl.MANUFACTURE_CODE}
    out["products_without_any_manufacture_operation"] = sorted(c for c in product_codes - mfg_any if c)
    return out, xml_bytes


def fetch_version(label, set_id, version, history, cutoff, data_dir, sources, fixtures, sites, group):
    vinfo = next((v for v in history["versions"] if v["version"] == int(version)), None)
    later = [v for v in history["versions"] if v["version"] > int(version)]
    rec = {"group": group, "label": label, "set_id": set_id, "version": int(version),
           "history_title": history["title"],
           "published_at": vinfo["published_at"] if vinfo else None,
           "published_at_basis": "DailyMed v2 /spls/{setid}/history published_date",
           "admissible_pre_cutoff": bool(vinfo and vinfo["published_at"] <= cutoff),
           "next_version": later[0] if later else None}
    pre = resolve_pre_cutoff(history, cutoff)
    rec["is_latest_pre_cutoff_version"] = bool(pre and pre["version"] == int(version))
    if vinfo is None:
        rec["failures"] = ["version not listed in history service"]
        return rec
    url = dailymed.GETFILE_VERSION.format(setid=set_id, version=version)
    r = net.fetch(url, data_dir / "historical" / f"{set_id}_v{version}.zip")
    time.sleep(PAUSE_S)
    cd = r.headers.get("content-disposition", "")
    fname = cd.split("filename=")[-1].strip('"; ') if "filename=" in cd else None
    sources.append(source_record(r, kind="dailymed_spl_version_zip", role="historical", data_dir=data_dir,
                                 published_at=rec["published_at"], published_at_basis=rec["published_at_basis"],
                                 set_id=set_id, version=int(version), content_disposition_filename=fname))
    rec["zip"] = {"url": url, "sha256": r.sha256, "bytes": r.bytes, "retrieved_at": r.retrieved_at,
                  "content_disposition_filename": fname}
    detail, xml_bytes = inspect_zip(r.path, set_id, version, sites)
    rec.update(detail)
    if xml_bytes is not None and fixtures is not None and not rec["failures"]:
        name = f"{set_id}_v{version}.xml"
        if group == "identity_filing":
            # Registration SPLs name individual contacts; never commit those verbatim.
            xml_bytes = strip_contact_parties(xml_bytes)
            name = f"{set_id}_v{version}.contacts-removed.xml"
            rec["fixture_derivation"] = "contactParty elements removed; original XML sha256 is xml.sha256"
        fx = Path(fixtures) / name
        fx.parent.mkdir(parents=True, exist_ok=True)
        fx.write_bytes(xml_bytes)
        rec["fixture"] = fx.as_posix()
        rec["fixture_sha256"] = hashlib.sha256(xml_bytes).hexdigest()
    return rec


def strip_contact_parties(xml_bytes: bytes) -> bytes:
    return re.sub(rb"<contactParty\b.*?</contactParty>", b"", xml_bytes, flags=re.S)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fixtures", type=Path)
    a = ap.parse_args(argv)
    cfg = json.loads(a.config.read_text(encoding="utf-8"))
    cutoff, sites = cfg["cutoff"], cfg["sites"]
    sources, results = [], []
    run = {"started_at": net.utc_now(), "cutoff": cutoff, "cutoff_rule": cfg["cutoff_rule"]}

    for t in cfg["rocky_mount_targets"]["items"]:
        h = get_history(t["set_id"], a.data_dir, sources)
        results.append(fetch_version(t["label"], t["set_id"], t["version"], h, cutoff, a.data_dir,
                                     sources, a.fixtures, sites, "rocky_mount_target"))
        print(t["label"], "done", file=sys.stderr)

    searches = []
    for s in cfg["mcpherson_controls"]["searches"]:
        qs = urllib.parse.urlencode({"drug_name": s["drug_name"], "labeler": s["labeler"], "pagesize": 100})
        r = net.fetch(f"{dailymed.SPLS_SEARCH}?{qs}", a.data_dir / "search" / f"{s['drug_name']}_{s['labeler']}.json")
        time.sleep(PAUSE_S)
        sources.append(source_record(r, kind="dailymed_spls_search_json", role="documentation",
                                     data_dir=a.data_dir, query=s))
        d = json.loads(Path(r.path).read_text(encoding="utf-8"))
        hits = [{"set_id": x["setid"], "title": x["title"], "current_version": x["spl_version"]} for x in d["data"]]
        searches.append({"query": s, "total_elements": d["metadata"]["total_elements"], "hits": hits})
        for hit in hits:
            h = get_history(hit["set_id"], a.data_dir, sources)
            pre = resolve_pre_cutoff(h, cutoff)
            if pre is None:
                results.append({"group": "mcpherson_control", "label": s["drug_name"], "set_id": hit["set_id"],
                                "failures": ["no version published on or before cutoff"], "history": h})
                continue
            results.append(fetch_version(s["drug_name"], hit["set_id"], pre["version"], h, cutoff, a.data_dir,
                                         sources, a.fixtures, sites, "mcpherson_control"))
            print(s["drug_name"], hit["set_id"], "done", file=sys.stderr)

    for f in cfg["identity_spl_filings"]["items"]:
        h = get_history(f["set_id"], a.data_dir, sources)
        for v in [v for v in h["versions"] if v["published_at"] <= cutoff]:
            rec = fetch_version(f["label"], f["set_id"], v["version"], h, cutoff, a.data_dir,
                                sources, a.fixtures, sites, "identity_filing")
            results.append(rec)
        print(f["label"], "done", file=sys.stderr)

    run["finished_at"] = net.utc_now()
    write_json(a.out, {"run": run, "control_searches": searches, "documents": results, "sources": sources})
    for r in results:
        rm = r.get("site_findings", {}).get("rocky_mount", {}).get("manufacture_product_codes")
        mc = r.get("site_findings", {}).get("mcpherson", {}).get("manufacture_product_codes")
        print(f'{r["group"]:20} {r["label"][:28]:28} v{r.get("version")} pub={r.get("published_at")} '
              f'adm={r.get("admissible_pre_cutoff")} latest_pre={r.get("is_latest_pre_cutoff_version")} '
              f'idok={r.get("identity_check")} RM_MFG={rm} McP_MFG={mc} fail={r.get("failures")}')


if __name__ == "__main__":
    main()
