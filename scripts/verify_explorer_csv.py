"""Check that the explorer's CSV downloads match the graph, row for row and field for field.

  python -I scripts/verify_explorer_csv.py --db fineprint [--out evidence/explorer/csv_verification.json]

The CSVs are produced by the site's own JavaScript (scripts/explorer_csv.mjs under Node) from the
published JSON files. The expected values come from SQL written here independently of
scripts/export_explorer.py. Historical CSV rows are checked against the frozen cohort files.
"""

import argparse
import csv
import io
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))  # works under python -I
from fineprint.manifest import write_json  # noqa: E402

EXAMPLES = {"093132819", "030606222"}
EXPECTED_SQL = """
SELECT e.assertion_pk::text, e.confidence, e.confidence_reasons, e.operation_name, e.duns, i.status, i.fei,
       i.firm_name, i.address, p.ndc_product_5_4, p.ndc_raw, p.name, p.dosage_form,
       ARRAY(SELECT DISTINCT k.ndc_package_5_4_2 FROM national.package k
             WHERE k.product_pk = p.product_pk AND k.ndc_package_5_4_2 IS NOT NULL ORDER BY 1),
       ARRAY(SELECT DISTINCT o.name FROM national.organization_mention o
             WHERE o.document_pk = d.document_pk AND o.role = 'labeler' ORDER BY 1),
       e.set_id, d.version::text, d.document_id, d.published_date::text, d.effective_date::text,
       s.selection_class, e.product_scope, e.product_ndc_raw, e.loc, f.name, d.member_name, d.xml_member_name,
       d.xml_sha256, e.identity_status
FROM national.operation_edge e
JOIN national.spl_document d ON d.document_pk = e.document_pk
JOIN national.set_version_selection s ON s.document_pk = e.document_pk
JOIN national.source_file f ON f.source_file_id = d.source_file_id
LEFT JOIN national.product p ON p.product_pk = e.report_product_pk
LEFT JOIN national.duns_identity i ON i.duns = e.duns
WHERE (e.is_manufacture OR e.duns = ANY(%s)) AND e.duns IS NOT NULL"""
COLUMNS = ["evidence_id", "confidence", "reasons", "operation", "establishment_duns", "identity_status", "fei",
           "registered_firm_name", "registered_address", "product_ndc_5_4", "product_ndc_raw", "product_name",
           "dosage_form", "package_ndcs_11", "labelers", "set_id", "version", "document_id", "published_date",
           "effective_date", "version_selection", "product_scope", "operation_product_code", "xml_location",
           "source_part", "archive_member", "xml_member", "xml_sha256"]


def cell(v) -> str:
    """The documented CSV cell rule (site/explorer-core.js `cell`), applied to expected values."""
    if v is None:
        return ""
    s = "; ".join(v) if isinstance(v, list) else str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@", "\t", "\r") else s


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--site", type=Path, default=REPO / "site")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)

    produced = json.loads(subprocess.run(["node", str(REPO / "scripts" / "explorer_csv.mjs"), str(a.site)],
                                         capture_output=True, check=True, encoding="utf-8").stdout)
    from fineprint import db
    conn = db.connect(a.db)
    expected = {}
    identity_mismatch = 0
    for r in conn.execute(EXPECTED_SQL, (sorted(EXAMPLES),)).fetchall():
        *vals, edge_identity_status = r
        identity_mismatch += edge_identity_status != vals[5]  # edge copy vs duns_identity must agree
        expected[vals[0]] = dict(zip(COLUMNS, (cell(v) for v in vals)))
    conn.close()

    seen, mismatched_fields, rows = set(), Counter(), 0
    examples_of_mismatch = []
    url_errors = 0
    for duns, text in produced["current"].items():
        for row in csv.DictReader(io.StringIO(text, newline="")):
            rows += 1
            eid = row["evidence_id"]
            if eid in seen:
                mismatched_fields["duplicate_evidence_id"] += 1
            seen.add(eid)
            exp = expected.get(eid)
            if exp is None or row["establishment_duns"] != duns:
                mismatched_fields["row_not_in_graph_or_wrong_facility"] += 1
                continue
            for c in COLUMNS:
                if row[c] != exp[c]:
                    mismatched_fields[c] += 1
                    if len(examples_of_mismatch) < 5:
                        examples_of_mismatch.append({"evidence_id": eid, "column": c})
            url_errors += row["dailymed_label_url"] != f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={row['set_id']}"
            url_errors += row["fda_spl_xml_url"] != (f"https://www.accessdata.fda.gov/spl/data/{row['document_id']}/"
                                                     f"{row['document_id']}.xml")
    missing = sorted(set(expected) - seen)

    # historical: every CSV row must agree with the frozen cohort file
    E = json.loads((REPO / "evidence/historical/frozen/cohort_E.json").read_text(encoding="utf-8"))["packages"]
    hist = list(csv.DictReader(io.StringIO(produced["historical"], newline="")))
    hist_bad = 0
    for h in hist:
        p = E.get(h["package_ndc_11"])
        if p is None:
            hist_bad += h["classification"] != "NOT_IN_COHORT"
            continue
        hist_bad += (h["classification"] != p["classification"] or h["graph_flag"] != str(p["graph_flag"]).lower()
                     or h["set_id"] not in {v["set_id"] for v in p["provenance"]})
    hist_pk = {h["package_ndc_11"] for h in hist}
    result = {
        "current": {"facilities": len(produced["current"]), "csv_rows": rows, "graph_edges_expected": len(expected),
                    "rows_missing_from_csv": len(missing), "field_mismatches": dict(mismatched_fields),
                    "mismatch_examples": examples_of_mismatch, "url_errors": url_errors,
                    "edge_vs_identity_status_disagreements": identity_mismatch,
                    "columns_compared": COLUMNS},
        "historical": {"csv_rows": len(hist), "packages": len(hist_pk), "cohort_E_packages": len(E),
                       "flagged": len({h["package_ndc_11"] for h in hist if h["graph_flag"] == "true"}),
                       "on_warning_list": len({h["package_ndc_11"] for h in hist if h["on_warning_list"] == "true"}),
                       "rows_disagreeing_with_frozen_cohort": hist_bad},
    }
    ok = (not missing and not mismatched_fields and not url_errors and not identity_mismatch and rows == len(expected)
          and not hist_bad and len(hist_pk - {"00409-5816-11", "00409-5816-31"}) == len(E))
    result["ok"] = ok
    if a.out:
        write_json(a.out, result)
    print(json.dumps(result, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
