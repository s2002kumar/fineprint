"""DST-08: every count in DST_08_SOURCE_NDC_REVIEW.md, from the lineage schema of the scratch database.

  python -I scripts/research/dst08_report_counts.py --db fineprint_dst08
Output: docs/research/dst08/report_counts.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from fineprint import db  # noqa: E402

OUT = REPO / "docs" / "research" / "dst08" / "report_counts.json"

# One primary reason per excluded reference, first match in this order (the full reason lists are in the schema).
PRIMARY = """CASE
    WHEN r.validity <> 'VALID' THEN 'invalid reference: ' || r.validity
    WHEN r.product_kind = 'kit_part' THEN 'citing kit part'
    WHEN x.resolution <> 'RESOLVED' THEN 'unresolved: ' || x.resolution
    WHEN x.source_selection_class NOT IN ('confirmed', 'unconfirmed') THEN 'source version selection: ' || x.source_selection_class
    WHEN x.chain <> 'SINGLE_HOP' THEN 'chain: ' || x.chain
    WHEN x.consistency <> 'CONSISTENT' THEN 'conflict with source: ' || x.consistency
    WHEN NOT x.source_has_direct THEN 'source has no DIRECT manufacture'
    ELSE 'eligible' END"""


def wilson(k: int, n: int, z: float = 1.959964) -> list[float]:
    if n == 0:
        return [0.0, 1.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint_dst08")
    a = ap.parse_args()
    with db.connect(a.db) as c:
        one = lambda sql: c.execute(sql).fetchone()  # noqa: E731
        rows = lambda sql: [list(r) for r in c.execute(sql).fetchall()]  # noqa: E731
        build = one("SELECT build_id, rule_version, graph_build_id, code_commit, code_dirty, finished_at FROM lineage.build "
                    "WHERE status = 'completed' ORDER BY build_id DESC LIMIT 1")
        products = one("SELECT count(*) FROM lineage.v_product_coverage")[0]
        out = {
            "lineage_build": dict(zip(("build_id", "rule_version", "graph_build", "code_commit", "code_dirty", "finished_at"),
                                      build)),
            "products_in_release": products,
            "references": dict(zip(("references", "citing_products_and_parts", "top_level_products", "kit_parts"), one(
                "SELECT count(*), count(DISTINCT product_pk), count(DISTINCT product_pk) FILTER (WHERE product_kind = 'product'), "
                "count(DISTINCT product_pk) FILTER (WHERE product_kind = 'kit_part') FROM lineage.source_reference"))),
            "citing_top_level_products_by_direct_tier_status": rows(
                "SELECT v.direct_tier_status, count(DISTINCT r.product_pk) FROM lineage.source_reference r "
                "JOIN lineage.v_product_coverage v ON v.product_pk = r.product_pk GROUP BY 1 ORDER BY 1"),
            "valid_resolved": dict(zip(("references", "distinct_citing_source_pairs", "distinct_source_products"), one(
                "SELECT count(*), count(DISTINCT (r.product_pk, x.source_product_pk)), count(DISTINCT x.source_product_pk) "
                "FROM lineage.source_reference r JOIN lineage.source_resolution x USING (reference_pk) "
                "WHERE r.validity = 'VALID' AND x.resolution = 'RESOLVED'"))),
            "eligible": dict(zip(("references", "distinct_source_products", "on_products_already_direct"), one(
                "SELECT count(*), count(DISTINCT x.source_product_pk), count(*) FILTER (WHERE v.direct_tier_status = 'DIRECT') "
                "FROM lineage.source_resolution x JOIN lineage.source_reference r USING (reference_pk) "
                "JOIN lineage.v_product_coverage v ON v.product_pk = r.product_pk WHERE x.status = 'ELIGIBLE'"))),
            "source_linked_tier": dict(zip(("products", "distinct_source_products", "distinct_direct_sites", "evidence_rows"), one(
                "SELECT count(DISTINCT e.linked_product_pk), count(DISTINCT e.source_product_pk), count(DISTINCT e.duns), count(*) "
                "FROM lineage.source_linked_evidence e JOIN lineage.v_product_coverage v ON v.product_pk = e.linked_product_pk "
                "WHERE v.coverage_tier = 'SOURCE_LINKED'"))),
            "primary_reason": rows(
                f"SELECT {PRIMARY} AS reason, count(*) FROM lineage.source_reference r "
                "JOIN lineage.source_resolution x USING (reference_pk) GROUP BY 1 ORDER BY 2 DESC, 1"),
            "multiple_candidates_by_site_agreement": rows(
                """SELECT label, count(*) FROM (
                       SELECT s.reference_pk, CASE WHEN count(DISTINCT s.sites) = 1 AND min(s.sites) <> ''
                                                   THEN 'all candidates name the same DIRECT sites'
                                                   WHEN max(s.sites) = '' THEN 'no candidate has DIRECT sites'
                                                   ELSE 'candidates name different DIRECT sites' END AS label
                       FROM (SELECT x.reference_pk, cand,
                                    coalesce((SELECT string_agg(DISTINCT e.duns, ';' ORDER BY e.duns)
                                              FROM national.operation_edge e
                                              WHERE e.report_product_pk = cand AND e.product_pk = cand AND e.is_manufacture
                                                AND e.confidence = 'DIRECT'), '') AS sites
                             FROM lineage.source_resolution x, unnest(x.candidate_product_pks) cand
                             WHERE x.resolution = 'MULTIPLE_CANDIDATES') s
                       GROUP BY s.reference_pk) t GROUP BY 1 ORDER BY 1"""),
            "temporal_eligible": dict(zip(("eligible", "source_version_published_after_citing_version",
                                           "source_version_published_on_or_before", "a_date_missing"), one(
                """SELECT count(*), count(*) FILTER (WHERE sd.published_date > cd.published_date),
                          count(*) FILTER (WHERE sd.published_date <= cd.published_date),
                          count(*) FILTER (WHERE sd.published_date IS NULL OR cd.published_date IS NULL)
                   FROM lineage.source_resolution x JOIN lineage.source_reference r USING (reference_pk)
                   JOIN national.spl_document cd ON cd.document_pk = r.document_pk
                   JOIN national.spl_document sd ON sd.document_pk = x.source_document_pk WHERE x.status = 'ELIGIBLE'"""))),
            "source_linked_products_by_direct_site_count": rows(
                """SELECT CASE WHEN n >= 5 THEN '5 or more' ELSE n::text END, count(*), max(n) FROM (
                       SELECT e.linked_product_pk, count(DISTINCT e.duns) AS n FROM lineage.source_linked_evidence e
                       JOIN lineage.v_product_coverage v ON v.product_pk = e.linked_product_pk
                       WHERE v.coverage_tier = 'SOURCE_LINKED' GROUP BY 1) t GROUP BY 1 ORDER BY 1"""),
            "package_prefix_diagnostic": dict(zip(("package_code_references", "prefix_matches_exactly_one_canonical_product",
                                                   "prefix_matches_several", "prefix_matches_none"), one(
                """SELECT count(*), count(*) FILTER (WHERE n = 1), count(*) FILTER (WHERE n > 1), count(*) FILTER (WHERE n = 0)
                   FROM (SELECT r.reference_pk, (SELECT count(*) FROM national.product p
                           JOIN national.set_version_selection s ON s.document_pk = p.document_pk
                           WHERE p.kind = 'product' AND p.ndc_raw = split_part(r.source_code_raw, '-', 1) || '-' ||
                                 split_part(r.source_code_raw, '-', 2)) AS n
                         FROM lineage.source_reference r WHERE r.validity = 'PACKAGE_CODE_NOT_PRODUCT_CODE') t"""))),
        }
        cov = {r[0]: r[1] for r in c.execute("SELECT coverage_tier, count(*) FROM lineage.v_product_coverage GROUP BY 1")}
        direct = cov.get("DIRECT", 0)
        linked = cov.get("SOURCE_LINKED", 0)
        out["coverage"] = {
            "direct_tier_unchanged": {r[0]: r[1] for r in c.execute(
                "SELECT direct_tier_status, count(*) FROM lineage.v_product_coverage GROUP BY 1 ORDER BY 1")},
            "with_source_linked_tier": dict(sorted(cov.items())),
            "share": {"DIRECT": round(direct / products, 4), "SOURCE_LINKED": round(linked / products, 4),
                      "DIRECT_or_SOURCE_LINKED": round((direct + linked) / products, 4)},
        }
    sample = list(csv.DictReader(
        (REPO / "docs" / "research" / "dst08" / "sample_ai_review.csv").read_text(encoding="utf-8").splitlines()))
    linked_rows = [r for r in sample if r["prototype_status"] == "ELIGIBLE"]
    supported = sum(r["ai_verdict"] in ("LINK_SUPPORTED", "EXCLUDED_BY_DEFECT_FIXED") for r in linked_rows)
    r9 = [r for r in sample if r["stratum"].startswith("R9 ")]
    out["sample_ai_assisted"] = {
        "note": "AI-assisted reading of mechanical raw-XML checks; not a human adjudication",
        "eligible_in_prototype": len(linked_rows), "link_supported": supported,
        "wilson_95": wilson(supported, len(linked_rows)),
        "r9_supported": [sum(r["ai_verdict"] == "LINK_SUPPORTED" for r in r9), len(r9)],
        "r9_wilson_95": wilson(sum(r["ai_verdict"] == "LINK_SUPPORTED" for r in r9), len(r9)),
        "verdicts": dict(Counter(r["ai_verdict"] for r in sample)),
        "human_review_rows": sum(r["human_review_required"] == "True" or r["risk"] == "high" for r in sample),
    }
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
