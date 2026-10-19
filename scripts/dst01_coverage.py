"""DST-01: measured row counts and coverage of the national ingest (pure SQL over the database).

  python -I scripts/dst01_coverage.py --db fineprint --out evidence/dst01/coverage.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import db, net  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402

Q = {
    "documents": """SELECT count(*) total,
        count(*) FILTER (WHERE has_establishment_block) with_establishment_block,
        count(*) FILTER (WHERE NOT has_establishment_block) without_establishment_block,
        count(*) FILTER (WHERE published_date IS NOT NULL) with_published_date,
        count(*) FILTER (WHERE effective_date IS NULL) effective_date_unparsed,
        count(*) FILTER (WHERE member_name_date = published_date) member_date_equals_published,
        count(*) FILTER (WHERE jsonb_array_length(anomalies) > 0) with_anomalies,
        count(DISTINCT set_id) distinct_set_ids,
        sum(xml_bytes) xml_bytes FROM national.spl_document""",
    "document_types": """SELECT document_type_code || ' | ' || coalesce(upper(document_type_name),'') k, count(*)
        FROM national.spl_document GROUP BY 1 ORDER BY 2 DESC""",
    "anomaly_kinds": """SELECT a->>'kind', count(*) FROM national.spl_document, jsonb_array_elements(anomalies) a
        GROUP BY 1 ORDER BY 2 DESC""",
    "version_conflicts": "SELECT count(*) FROM national.v_version_conflicts",
    "sets_with_multiple_versions": """SELECT count(*) FROM (SELECT set_id FROM national.spl_document
        GROUP BY set_id HAVING count(DISTINCT version) > 1) t""",
    "members_by_source_and_status": """SELECT s.name, m.status, count(*) FROM national.archive_member m
        JOIN national.source_file s USING (source_file_id) GROUP BY 1, 2 ORDER BY 1, 2""",
    "members_vs_advertised": """SELECT s.name, s.advertised_files, count(m.*) FROM national.source_file s
        LEFT JOIN national.archive_member m USING (source_file_id)
        WHERE s.kind = 'dailymed_human_rx_full_part' GROUP BY 1, 2 ORDER BY 1""",
    "dead_letters_by_stage_kind": """SELECT stage || ' | ' || error_kind, count(*) FROM national.dead_letter
        GROUP BY 1 ORDER BY 2 DESC""",
    "dead_letters": """SELECT s.name, x.member_name, x.stage, x.error_kind, left(x.error_detail, 300)
        FROM national.dead_letter x JOIN national.source_file s USING (source_file_id) ORDER BY 1, 2 LIMIT 100""",
    "products": """SELECT count(*) total, count(*) FILTER (WHERE kind='product') products,
        count(*) FILTER (WHERE kind='kit_part') kit_parts,
        count(*) FILTER (WHERE ndc_raw IS NULL) without_ndc,
        count(*) FILTER (WHERE ndc_raw IS NOT NULL AND ndc_product_5_4 IS NULL) ndc_not_normalizable,
        count(DISTINCT ndc_product_5_4) FILTER (WHERE kind='product') distinct_product_5_4
        FROM national.product""",
    "product_ndc_patterns": """SELECT coalesce(ndc_pattern,'<none>'), count(*) FROM national.product
        WHERE kind='product' GROUP BY 1 ORDER BY 2 DESC""",
    "product_codes_in_multiple_documents": """SELECT count(*) FROM (SELECT ndc_product_5_4 FROM national.product
        WHERE kind='product' AND ndc_product_5_4 IS NOT NULL GROUP BY 1 HAVING count(DISTINCT document_pk) > 1) t""",
    "packages": """SELECT count(*) total, count(*) FILTER (WHERE ndc_raw IS NULL) without_ndc,
        count(*) FILTER (WHERE ndc_raw IS NOT NULL AND ndc_package_5_4_2 IS NULL) ndc_not_normalizable,
        count(DISTINCT ndc_package_5_4_2) distinct_package_11,
        count(*) FILTER (WHERE segments_match_product IS FALSE) segments_mismatch_product
        FROM national.package""",
    "package_ndc_patterns": """SELECT coalesce(ndc_pattern,'<none>'), count(*) FROM national.package
        GROUP BY 1 ORDER BY 2 DESC""",
    "package_codes_in_multiple_documents": """SELECT count(*) FROM (SELECT ndc_package_5_4_2 FROM national.package
        WHERE ndc_package_5_4_2 IS NOT NULL GROUP BY 1 HAVING count(DISTINCT document_pk) > 1) t""",
    "organizations_by_role": "SELECT role, count(*) FROM national.organization_mention GROUP BY 1 ORDER BY 2 DESC",
    "establishments": """SELECT count(*) mentions, count(*) FILTER (WHERE duns IS NULL) without_duns,
        count(*) FILTER (WHERE cardinality(duns_all) > 1) multiple_duns, count(DISTINCT duns) distinct_duns,
        count(*) FILTER (WHERE cardinality(fei_all) > 0) with_fei, count(*) FILTER (WHERE address IS NOT NULL) with_address
        FROM national.organization_mention WHERE role = 'establishment'""",
    "distinct_labeler_duns": "SELECT count(DISTINCT duns) FROM national.organization_mention WHERE role='labeler'",
    "duns_as_both_labeler_and_establishment": """SELECT count(*) FROM (SELECT duns FROM national.organization_mention
        WHERE duns IS NOT NULL GROUP BY duns HAVING bool_or(role='labeler') AND bool_or(role='establishment')) t""",
    "assertions": """SELECT count(*) total, count(*) FILTER (WHERE duns IS NULL) without_duns,
        count(*) FILTER (WHERE operation_code IS NULL) without_operation_code,
        count(DISTINCT duns) FILTER (WHERE operation_code='C43360') distinct_manufacture_duns,
        count(DISTINCT document_pk) documents_with_assertions FROM national.operation_assertion""",
    "assertions_by_scope": "SELECT product_scope, count(*) FROM national.operation_assertion GROUP BY 1 ORDER BY 2 DESC",
    "assertions_by_operation": """SELECT a.operation_code || ' ' || coalesce(t.canonical_name,'?'), count(*)
        FROM national.operation_assertion a LEFT JOIN national.operation_type t USING (operation_code)
        GROUP BY 1 ORDER BY 2 DESC""",
    "operation_types": """SELECT operation_code, canonical_name, assertions, jsonb_object_length(observed_names),
        observed_names FROM national.operation_type ORDER BY assertions DESC""",
    "product_evidence_status": """SELECT evidence_status, count(*) FROM national.v_product_establishment_evidence
        WHERE kind = 'product' GROUP BY 1 ORDER BY 2 DESC""",
    "documents_by_establishment_presence_and_manufacture": """SELECT has_establishment_block,
        EXISTS (SELECT 1 FROM national.operation_assertion a WHERE a.document_pk = d.document_pk
                AND a.operation_code='C43360' AND a.duns IS NOT NULL) has_manufacture, count(*)
        FROM national.spl_document d GROUP BY 1, 2 ORDER BY 1, 2""",
    "table_bytes": """SELECT c.relname, pg_total_relation_size(c.oid) FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname='national' AND c.relkind='r' ORDER BY 2 DESC""",
    "database_bytes": "SELECT pg_database_size(current_database())",
    "runs": """SELECT run_id, status, started_at, finished_at, code_commit, code_dirty FROM national.ingest_run
        ORDER BY run_id""",
}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    out = {"generated_at": net.utc_now(), "database": a.db}
    with db.connect(a.db) as c:
        for k, sql in Q.items():
            cur = c.execute(sql)
            cols = [d.name for d in cur.description]
            rows = cur.fetchall()
            if len(rows) == 1 and len(cols) > 1 and k not in ("runs",):
                out[k] = dict(zip(cols, rows[0]))
            elif len(cols) == 1:
                out[k] = rows[0][0]
            elif len(cols) == 2:
                out[k] = {str(r[0]): r[1] for r in rows}
            else:
                out[k] = [list(r) for r in rows]
        out["fingerprint"] = db.fingerprint(c)
        out["table_counts"] = db.table_counts(c)
    write_json(a.out, json.loads(json.dumps(out, default=str)))
    print(json.dumps({k: out[k] for k in ("documents", "products", "packages", "establishments", "assertions",
                                          "product_evidence_status")}, indent=1, default=str))


if __name__ == "__main__":
    main()
