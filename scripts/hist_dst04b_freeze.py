"""DST-04B step 1 (plan A5): freeze cohorts M and E, classifications, baselines and the audit sample.

Runs entirely on pre-cutoff historical evidence already cached and hash-verified; no outcome
data, no national database. Writes evidence/historical/frozen/* plus FREEZE_MANIFEST.json.

  python -I scripts/hist_dst04b_freeze.py --config config/dst00_targets.json
"""

import argparse
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))  # works under python -I
from fineprint import bulk, config, historical, identity, net, spl  # noqa: E402
from fineprint import historical_eval as he  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402

DRAFT = REPO / "evidence" / "historical" / "dst04a_candidates_draft.json"
OUT = REPO / "evidence" / "historical" / "frozen"
AUDIT_SEED = "fineprint-dst04b-audit"
ALLOWED_SOURCES = ("dailymed.nlm.nih.gov/dailymed/getFile.cfm", "accessdata.fda.gov/spl/data/",
                   "dailymed-data.nlm.nih.gov/public-release-files/dm_spl_monthly_update_",
                   "dailymed.nlm.nih.gov/dailymed/services/v2/", "web.archive.org/")
DECRS_2022 = ("20221014123457", "https://www.accessdata.fda.gov/cder/drls_reg.zip")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_document(root: Path, sid: str, row: dict):
    """Return (parsed doc, provenance dict) for a set's admissible cutoff document, hash-verified."""
    d, status = row.get("document"), row["cutoff_status"]
    if d is None:
        return None, None
    if status == "fetched":
        p = root / "spl" / f"{sid}_v{row['cutoff_version']}.zip"
        data = p.read_bytes()
        if sha256(data) != d["zip_sha256"]:
            raise SystemExit(f"hash mismatch for {p.name}")
        doc = bulk.open_nested(p.name, data)["doc"]
        prov = {"kind": "dailymed_getFile_zip", "sha256": d["zip_sha256"],
                "url": f"https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid={sid}&version={row['cutoff_version']}"}
    elif status == "cutoff_version_by_document_id":
        p = root / "fda_spl" / f"{d['document_id']}.xml"
        data = p.read_bytes()
        if sha256(data) != d["xml_sha256"]:
            raise SystemExit(f"hash mismatch for {p.name}")
        doc = spl.parse_spl(io.BytesIO(data))
        prov = {"kind": "fda_spl_by_document_id", "sha256": d["xml_sha256"],
                "url": historical.FDA_SPL_BY_DOCID.format(docid=d["document_id"])}
    elif status == "cutoff_version_from_monthly_archive":
        arch = d["archive"].rsplit("_", 1)[-1][:-4]
        p = root / "monthly" / arch / d["member"].replace("/", "__")
        data = p.read_bytes()
        if sha256(data) != d["member_sha256"]:
            raise SystemExit(f"hash mismatch for {p.name}")
        doc = bulk.open_nested(d["member"], data)["doc"]
        prov = {"kind": "dailymed_monthly_archive_member", "sha256": d["member_sha256"],
                "url": f"{d['archive']}#{d['member']}", "container_last_modified": d.get("archive_last_modified")}
    else:
        return None, None
    if (doc["set_id"] or "").lower() != sid or str(doc["version"]) != str(row["cutoff_version"]):
        raise SystemExit(f"served document does not match {sid} v{row['cutoff_version']}")
    prov.update(set_id=sid, version=int(doc["version"]), published_date=row["cutoff_version_published"],
                effective_time=doc["effective_time"], xml_sha256=doc["xml_sha256"], cutoff_status=status)
    return doc, prov


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=OUT,
                    help="write elsewhere to re-derive the freeze without touching the sealed files")
    a = ap.parse_args(argv)
    out_dir = a.out_dir
    cutoff = json.loads(a.config.read_text(encoding="utf-8"))["cutoff"]
    cut8 = cutoff.replace("-", "")
    draft_bytes = DRAFT.read_bytes()
    draft = json.loads(draft_bytes)
    root = config.data_dir() / "raw" / "historical" / "frame_reconcile"
    f = historical.Fetcher(root)

    # 1. documents -> per-product classification
    docs, evidence, leakage = {}, {}, []
    for sid, row in sorted(draft["sets"].items()):
        doc, prov = load_document(root, sid, row)
        if doc is None:
            continue
        if prov["published_date"] > cutoff:
            leakage.append(f"{sid}: published {prov['published_date']} after cutoff")
        if (doc["effective_time"] or "")[:8] > cut8:
            leakage.append(f"{sid}: effectiveTime {doc['effective_time']} after cutoff")
        if not any(s in prov["url"] for s in ALLOWED_SOURCES):
            leakage.append(f"{sid}: source outside the historical allow-list: {prov['url']}")
        docs[sid] = prov
        evidence[sid] = he.product_evidence(doc)

    # 2. package rows -> one entry per 11-digit NDC with all provenance
    entries = defaultdict(lambda: {"provenance": []})
    exclusions = Counter(draft["summary"]["excluded"])
    for r in draft["packages"]:
        if r["status"] != "candidate":
            continue
        ev = evidence[r["set_id"]][r["product_ndc_raw"]]
        e = entries[r["package_ndc_11"]]
        e["provenance"].append({
            "set_id": r["set_id"], "version": r["version"], "package_ndc_raw": r["package_ndc_raw"],
            "product_ndc_raw": r["product_ndc_raw"], "sources": r["sources"], "in_may_2023_listing": r["in_d_listing"],
            "classification": he.classify(ev), "rocky_mount_manufacture_locs": ev["rm_mfg_locs"],
            "manufacture_duns": sorted(ev["mfg_duns"]), "rocky_mount_operations": sorted(ev["rm_ops"]),
            "b2": he.injectable(ev["form"], ev["routes"]), "form": ev["form"], "routes": sorted(ev["routes"]),
            "document_sha256": docs[r["set_id"]]["sha256"]})
    cohort_e = {}
    conflicts = []
    for n11, e in sorted(entries.items()):
        classes = [p["classification"] for p in e["provenance"]]
        b2s = {p["b2"] for p in e["provenance"]}
        cls = he.combine(classes)
        if len(set(classes)) > 1:
            conflicts.append({"package_ndc_11": n11, "classifications": classes})
        cohort_e[n11] = {"package_ndc_11": n11, "classification": cls, "graph_flag": cls == "DIRECT",
                         "b2": "INJECTABLE" if "INJECTABLE" in b2s else sorted(b2s)[0],
                         "in_may_2023_listing": any(p["in_may_2023_listing"] for p in e["provenance"]),
                         "provenance": e["provenance"]}
    cohort_m = {k: v for k, v in cohort_e.items() if v["in_may_2023_listing"]}
    m_excluded = [{"package_ndc_raw": u["package"], "reason": u["reason"], "set_id": u.get("set_id")}
                  for u in draft["unresolved_d_packages"]]
    listed_marketing_ended = sorted({p["package_ndc_11"] for p in draft["packages"]
                                     if p["status"] != "candidate" and p["in_d_listing"]})

    # 3. pre-event identity of Rocky Mount (identity only; A2) and FEI sharing in the 2022 capture
    zp, prov = f.get(f"https://web.archive.org/web/{DECRS_2022[0]}id_/{DECRS_2022[1]}",
                     f"decrs/drls_reg_{DECRS_2022[0]}.zip", role="identity_historical")
    rows, member = identity.parse_decrs(zp)
    rm_rows = [r for r in rows if r["DUNS_NUMBER"] == he.ROCKY_MOUNT]
    fei = rm_rows[0]["FEI_NUMBER"] if rm_rows else None
    identity_check = {
        "source": prov["url"], "sha256": prov["sha256"], "fda_generated": member["generated_at"],
        "rocky_mount_rows": [{k: r[k] for k in ("FEI_NUMBER", "DUNS_NUMBER", "FIRM_NAME", "ADDRESS", "EXPIRATION_DATE")}
                             for r in rm_rows],
        "other_duns_sharing_fei": sorted({r["DUNS_NUMBER"] for r in rows if fei and r["FEI_NUMBER"] == fei
                                          and r["DUNS_NUMBER"] != he.ROCKY_MOUNT}),
        "dst00_identity_evidence_sha256": sha256((REPO / "evidence/dst00/identity_evidence.json").read_bytes()),
        "dst00_spl_facility_filing_evidence_sha256": sha256((REPO / "evidence/dst00/historical_spl.json").read_bytes()),
        "caveat": "Identity per the 2022-10-13 registration record; not 2023 registration status (plan A2).",
    }

    # 4. predeclared audit sample (cohort E, seeded order)
    order = sorted(cohort_e, key=lambda k: he.audit_order(AUDIT_SEED, k))
    pick = {"DIRECT": 20, "OTHER_SITE": 10, "CONTROL": 10}
    sample = []
    for k in order:
        c = cohort_e[k]["classification"]
        bucket = c if c in ("DIRECT", "OTHER_SITE") else "CONTROL"
        if pick[bucket] > 0:
            pick[bucket] -= 1
            sample.append({"package_ndc_11": k, "bucket": bucket, "classification": c})

    # 5. baselines (membership only; nothing is scored here)
    def summary(cohort):
        return {"size": len(cohort), "graph_flags": sum(v["graph_flag"] for v in cohort.values()),
                "b2_injectable": sum(v["b2"] == "INJECTABLE" for v in cohort.values()),
                "b2_unclassified": sum(v["b2"] == "UNCLASSIFIED" for v in cohort.values()),
                "classification": dict(Counter(v["classification"] for v in cohort.values()))}

    rows_total = sum(len(e["provenance"]) for e in cohort_e.values())
    reconciliation = {
        "candidate_rows": rows_total, "distinct_package_ndc_11": len(cohort_e),
        "duplicate_rows": rows_total - len(cohort_e),
        "rows_in_may_listing": sum(p["in_may_2023_listing"] for e in cohort_e.values() for p in e["provenance"]),
        "distinct_in_may_listing": len(cohort_m),
        "distinct_not_in_may_listing": len(cohort_e) - len(cohort_m),
        "may_listing_packages_total": draft["summary"]["d_packages"],
        "may_listing_present_in_cutoff_documents": draft["summary"]["d_packages_vs_cutoff_documents"]
        .get("present_in_cutoff_document"),
        "may_listing_present_but_marketing_ended_by_cutoff": len(listed_marketing_ended),
        "may_listing_without_admissible_document": len(m_excluded),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    common = {"plan": "docs/historical_panel_plan.md amendment A5", "cutoff": cutoff,
              "status": "FROZEN before outcome retrieval"}
    files = {
        "cohort_E.json": {**common, "definition": "A5 §2 E", "summary": summary(cohort_e), "packages": cohort_e},
        "cohort_M.json": {**common, "definition": "A5 §2 M", "summary": summary(cohort_m),
                          "packages": sorted(cohort_m), "excluded_listed_packages": m_excluded,
                          "listed_but_marketing_ended_by_cutoff": listed_marketing_ended},
        "documents.json": {**common, "documents": docs, "leakage_violations": leakage},
        "identity.json": {**common, **identity_check},
        "audit_sample.json": {**common, "seed": AUDIT_SEED, "sample": sample},
        "freeze_summary.json": {**common, "reconciliation": reconciliation, "exclusions_E": dict(exclusions),
                                "multi_provenance_conflicts": conflicts, "B3": "NOT EVALUABLE (A5 §5)",
                                "draft_sha256": sha256(draft_bytes)},
    }
    for name, obj in files.items():
        write_json(out_dir / name, obj)
    manifest = {"generated_at": net.utc_now(), **common, "draft_input_sha256": sha256(draft_bytes),
                "files": {name: sha256((out_dir / name).read_bytes()) for name in files},
                "psycopg_loaded": "psycopg" in sys.modules}
    write_json(out_dir / "FREEZE_MANIFEST.json", manifest)
    if manifest["psycopg_loaded"] or leakage:
        raise SystemExit(f"leakage guard failed: psycopg_loaded={manifest['psycopg_loaded']} leakage={leakage}")
    print(json.dumps({"reconciliation": reconciliation, "E": summary(cohort_e), "M": summary(cohort_m),
                      "conflicts": len(conflicts), "identity_other_duns_sharing_fei": identity_check["other_duns_sharing_fei"],
                      "audit_sample": Counter(s["bucket"] for s in sample)}, indent=1, default=str))


if __name__ == "__main__":
    main()
