"""Population-level structured facts behind the coverage denominators (research workstream C3 support).

Reads every canonical label (hash-verified, from the release parts) with the independent XML walk and records, per
product, facts the current parser does not store:
  * source NDCs cited through asEquivalentEntity (repackager / relabeler labels pointing at the original product), and
    whether that source product is in the current graph with a DIRECT, TENTATIVE or UNKNOWN manufacturing status;
  * unscoped MANUFACTURE in the label and the number of products in it;
  * whether the narrative text contains a manufacturing-role statement at all (pattern presence only, no reading).
Nothing here changes the graph. Output is counts by stratum (docs/research/population_scan.json) plus a per-product
CSV kept outside the repository ($FINEPRINT_DATA/research/population_scan_products.csv).

  python -I scripts/research/population_scan.py --db fineprint [--limit N]
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "research"))
import coverage_diagnose as cd  # noqa: E402
import verify_audit_sample as raw  # noqa: E402
from fineprint import db  # noqa: E402  database access only

MFG = "C43360"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    t0 = time.time()
    with db.connect(a.db) as c:
        c.execute("CREATE TEMP TABLE tmp_status AS SELECT * FROM national.v_product_manufacturing_status")
        status_by_54 = defaultdict(set)
        for n54, st in c.execute("SELECT ndc_product_5_4, manufacturing_status FROM tmp_status WHERE ndc_product_5_4 IS NOT NULL"):
            status_by_54[n54].add(st)
        docs = c.execute(
            """SELECT d.document_pk, d.set_id, d.version, f.name, d.member_name, d.xml_member_name, m.member_sha256, d.xml_sha256,
                      array_agg(v.ndc_raw ORDER BY v.ndc_raw), array_agg(v.manufacturing_status ORDER BY v.ndc_raw),
                      array_agg(v.evidence_status ORDER BY v.ndc_raw)
               FROM national.set_version_selection s
               JOIN national.spl_document d ON d.document_pk = s.document_pk
               JOIN national.archive_member m ON m.document_pk = d.document_pk AND m.status = 'loaded'
               JOIN national.source_file f ON f.source_file_id = m.source_file_id
               JOIN tmp_status v ON v.set_id = s.set_id AND v.version = s.selected_version
               GROUP BY 1, 2, 3, 4, 5, 6, 7, 8 ORDER BY f.name, d.member_name""").fetchall()
    if a.limit:
        docs = docs[: a.limit]
    parts = {p.name: p for p in (raw.DATA / "raw" / "dailymed" / "human_rx_full").glob("*/dm_spl_release_human_rx_part*.zip")}
    out_csv = raw.DATA / "research" / "population_scan_products.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    tally = defaultdict(Counter)
    n_docs = 0
    cur_part, zf = None, None
    with out_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["set_id", "version", "ndc_raw", "manufacturing_status", "evidence_status", "products_in_label",
                    "source_ndcs", "source_status", "unscoped_manufacture_duns", "free_text_roles", "label_has_text_hit"])
        for pk, set_id, ver, part, member, xml_member, msha, xsha, ndcs, statuses, evidences in docs:
            if part != cur_part:
                if zf:
                    zf.close()
                zf, cur_part = zipfile.ZipFile(parts[part]), part
            data = zf.read(member)
            if raw.sha256(data) != msha:
                tally["_errors"]["member_hash"] += 1
                continue
            with zipfile.ZipFile(io.BytesIO(data)) as inner:
                xml = inner.read(xml_member)
            if raw.sha256(xml) != xsha:
                tally["_errors"]["xml_hash"] += 1
                continue
            try:
                root = raw.parse_xml(xml)
            except Exception:
                tally["_errors"]["parse"] += 1
                continue
            perfs = raw.performances(root)
            prods = raw.products(root)
            unscoped_mfg = sorted({d for p in perfs if p["in_author"] and not p["product_codes"] and p["code"] == MFG for d in p["duns"]})
            hits = cd.free_text_hits(cd.section_texts(root))
            roles = Counter(h["role"] for h in hits)
            by_code = {p["code"]: p for p in prods}
            n_docs += 1
            for ndc, st, ev in zip(ndcs, statuses, evidences):
                stratum = ev if st == "NO_MANUFACTURE_EVIDENCE" else st
                p = by_code.get(ndc)
                srcs = [s for s in (p["source_ndcs"] if p else []) if s]
                src_status = sorted({x for s in srcs for x in status_by_54.get(raw.to_5_4(s), {"NOT_IN_GRAPH"})})
                t = tally[stratum]
                t["products"] += 1
                if srcs:
                    t["has_source_ndc"] += 1
                    if "DIRECT" in src_status:
                        t["source_ndc_is_DIRECT_in_graph"] += 1
                    elif "TENTATIVE" in src_status:
                        t["source_ndc_is_TENTATIVE_in_graph"] += 1
                    elif "UNKNOWN_SITE" in src_status:
                        t["source_ndc_is_UNKNOWN_SITE_in_graph"] += 1
                    elif "NO_MANUFACTURE_EVIDENCE" in src_status:
                        t["source_ndc_has_NO_MANUFACTURE_EVIDENCE"] += 1
                    else:
                        t["source_ndc_not_in_graph"] += 1
                if unscoped_mfg:
                    t["label_has_unscoped_manufacture"] += 1
                    if len(prods) == 1:
                        t["label_has_unscoped_manufacture_and_single_product"] += 1
                if hits:
                    t["label_has_free_text_role_statement"] += 1
                if roles.get("MANUFACTURED_BY") or roles.get("MANUFACTURER"):
                    t["label_says_manufactured_by"] += 1
                if roles.get("MANUFACTURED_FOR"):
                    t["label_says_manufactured_for"] += 1
                if roles.get("DISTRIBUTED_BY"):
                    t["label_says_distributed_by"] += 1
                if roles.get("MADE_IN") or roles.get("PRODUCT_OF"):
                    t["label_says_made_in"] += 1
                w.writerow([set_id, ver, ndc, st, ev, len(prods), ";".join(srcs), ";".join(src_status), ";".join(unscoped_mfg),
                            ";".join(f"{k}:{v}" for k, v in sorted(roles.items())), bool(hits)])
            if n_docs % 2000 == 0:
                print(f"{n_docs}/{len(docs)} documents {time.time() - t0:.0f}s", file=sys.stderr)
    if zf:
        zf.close()
    out = {"generated_at": raw.utc_now(), "documents_scanned": n_docs, "documents_in_scope": len(docs), "seconds": round(time.time() - t0),
           "per_product_csv_outside_repo": "FINEPRINT_DATA/research/population_scan_products.csv",
           "tally_by_stratum": {k: dict(v) for k, v in sorted(tally.items())}}
    (REPO / "docs" / "research" / "population_scan.json").write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(out["tally_by_stratum"], indent=1))


if __name__ == "__main__":
    sys.exit(main())
