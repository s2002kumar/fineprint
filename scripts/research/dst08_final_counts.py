"""DST-08 final validation: every count in DST_08_FINAL_VALIDATION.md, rule v1 beside rule v2.

  python -I scripts/research/dst08_final_counts.py --db fineprint_dst08
Output: docs/research/dst08/final_counts.json

Reads the lineage schema of the scratch database after a build and lineage.validate_v2. The v1 figures are recomputed
from the v1 tables (unchanged since c8ded0f) so they can be set beside v2 without reference to any earlier report.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from fineprint import db  # noqa: E402

OUT = REPO / "docs" / "research" / "dst08" / "final_counts.json"
SAMPLE = REPO / "docs" / "research" / "dst08" / "sample_manifest.json"

TIER = {"v1": ("lineage.source_resolution", "lineage.source_linked_evidence", "lineage.v_product_coverage"),
        "v2": ("lineage.resolution_v2", "lineage.source_linked_evidence_v2", "lineage.v_product_coverage_v2")}


def rule_counts(c, rule: str) -> dict:
    res, ev, cov = TIER[rule]
    one = lambda sql: c.execute(sql).fetchone()[0]  # noqa: E731
    pairs = lambda sql: {str(k): v for k, v in c.execute(sql).fetchall()}  # noqa: E731
    total = one(f"SELECT count(*) FROM {cov}")
    tiers = pairs(f"SELECT coverage_tier, count(*) FROM {cov} GROUP BY 1")
    linked = tiers.get("SOURCE_LINKED", 0)
    return {
        "eligible_references": one(f"SELECT count(*) FROM {res} WHERE status = 'ELIGIBLE'"),
        "eligible_on_direct_products": one(
            f"""SELECT count(*) FROM {res} x JOIN lineage.source_reference r USING (reference_pk)
                JOIN {cov} v ON v.product_pk = r.product_pk WHERE x.status = 'ELIGIBLE' AND v.direct_tier_status = 'DIRECT'"""),
        "evidence_rows": one(f"SELECT count(*) FROM {ev}"),
        "source_linked_products": linked,
        "source_linked_from": pairs(f"SELECT direct_tier_status, count(*) FROM {cov} WHERE coverage_tier = 'SOURCE_LINKED' GROUP BY 1"),
        "distinct_source_products": one(f"SELECT count(DISTINCT source_product_pk) FROM {ev}"),
        "distinct_source_sites": one(f"SELECT count(DISTINCT duns) FROM {ev}"),
        "products_by_number_of_source_sites": pairs(
            f"""SELECT CASE WHEN n >= 5 THEN '5+' ELSE n::text END, count(*) FROM (
                    SELECT linked_product_pk, count(DISTINCT duns) n FROM {ev} GROUP BY 1) t GROUP BY 1"""),
        "max_source_sites": one(f"SELECT max(n) FROM (SELECT count(DISTINCT duns) n FROM {ev} GROUP BY linked_product_pk) t"),
        "coverage_tiers": tiers,
        "products": total,
        "share": {"direct": round(tiers.get("DIRECT", 0) / total, 4), "source_linked": round(linked / total, 4),
                  "direct_or_source_linked": round((tiers.get("DIRECT", 0) + linked) / total, 4)},
    }


def frozen_sample(c) -> dict:
    """The 96 references frozen at 43b3c5b, by stratum: v1 status, v2 status and the current physical outcome."""
    out: dict[str, dict] = {}
    for s in json.loads(SAMPLE.read_text(encoding="utf-8"))["sample"]:
        row = c.execute(
            """SELECT x.status, v.status, coalesce(p.outcome, '-') FROM lineage.source_reference r
               JOIN national.spl_document d USING (document_pk) JOIN lineage.source_resolution x USING (reference_pk)
               JOIN lineage.resolution_v2 v USING (reference_pk) LEFT JOIN lineage.physical_check p USING (reference_pk)
               WHERE lower(d.set_id) = lower(%s) AND d.version = %s AND r.loc = %s""",
            (s["set_id"], int(s["version"]), s["ref_loc"])).fetchone()
        key = " / ".join(row)
        out.setdefault(s["stratum"], {}).setdefault(key, 0)
        out[s["stratum"]][key] += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint_dst08")
    a = ap.parse_args()
    with db.connect(a.db) as c:
        q = lambda sql: [list(r) for r in c.execute(sql).fetchall()]  # noqa: E731
        one = lambda sql: c.execute(sql).fetchone()[0]  # noqa: E731
        build = c.execute("SELECT build_id, rule_version, code_commit, code_dirty, finished_at FROM lineage.build").fetchone()
        val = c.execute("SELECT rule_version, manifest_sha256, finished_at FROM lineage.validation_v2").fetchone()
        out = {
            "lineage_build": {"rule": build[1], "code_commit": build[2], "code_dirty": build[3], "finished_at": build[4]},
            "validation_v2": {"rule": val[0], "manifest_sha256": val[1], "finished_at": val[2]},
            "references": one("SELECT count(*) FROM lineage.source_reference"),
            "references_on_kit_parts": one("SELECT count(*) FROM lineage.source_reference WHERE product_kind = 'kit_part'"),
            "resolved_unique_source": one("SELECT count(*) FROM lineage.source_resolution WHERE resolution = 'RESOLVED'"),
            "direct_tier": dict(c.execute("SELECT direct_tier_status, count(*) FROM lineage.v_product_coverage GROUP BY 1").fetchall()),
            "direct_tier_identical_under_v2": q(
                "SELECT direct_tier_status, count(*) FROM lineage.v_product_coverage GROUP BY 1 ORDER BY 1") == q(
                "SELECT direct_tier_status, count(*) FROM lineage.v_product_coverage_v2 GROUP BY 1 ORDER BY 1"),
            "v1": rule_counts(c, "v1"),
            "v2": rule_counts(c, "v2"),
            "transitions_v1_to_v2": q(
                """SELECT x.status, v.status, v.basis, count(*) FROM lineage.source_resolution x
                   JOIN lineage.resolution_v2 v USING (reference_pk) GROUP BY 1, 2, 3 ORDER BY 1, 2, 3"""),
            "physical_basis_of_v2_eligible": q(
                """SELECT CASE WHEN v.basis = 'version_check' THEN 'version check: ' || c.classification
                               ELSE coalesce(p.outcome, 'no physical comparison') END, count(*)
                   FROM lineage.resolution_v2 v LEFT JOIN lineage.physical_check p USING (reference_pk)
                   LEFT JOIN lineage.version_check c USING (reference_pk)
                   WHERE v.status = 'ELIGIBLE' GROUP BY 1 ORDER BY 2 DESC"""),
            "version_check": {
                "references": one("SELECT count(*) FROM lineage.version_check"),
                "by_class_and_v2": q(
                    """SELECT c.classification, v.status, v.reasons, count(*) FROM lineage.version_check c
                       JOIN lineage.resolution_v2 v USING (reference_pk) GROUP BY 1, 2, 3 ORDER BY 1, 2, 3"""),
                "by_class_and_why": q(
                    """SELECT classification, CASE WHEN detail LIKE '%%matches source version%%' THEN 'matches another source version'
                              WHEN detail LIKE '%%not retrievable%%' THEN 'other versions not retrievable'
                              ELSE split_part(detail, ':', 1) END, count(*)
                       FROM lineage.version_check GROUP BY 1, 2 ORDER BY 1, 3 DESC"""),
                "by_conflicting_characteristic": q(
                    """SELECT array_to_string(conflicting, '+'), count(*) FROM lineage.version_check GROUP BY 1 ORDER BY 2 DESC"""),
                "by_class_and_conflicting": q(
                    """SELECT classification, array_to_string(conflicting, '+'), count(*) FROM lineage.version_check
                       GROUP BY 1, 2 ORDER BY 1, 3 DESC"""),
                "source_label_newer_than_citing": q(
                    """SELECT source_published_now > citing_published_at, count(*) FROM lineage.version_check GROUP BY 1 ORDER BY 1"""),
                "citing_date_basis": q("SELECT citing_date_basis, count(*) FROM lineage.version_check GROUP BY 1"),
                "citing_history_date_equals_release_metadata": q(
                    """SELECT c.citing_published_at = d.published_date, count(*) FROM lineage.version_check c
                       JOIN lineage.source_reference r USING (reference_pk) JOIN national.spl_document d ON d.document_pk = r.document_pk
                       GROUP BY 1 ORDER BY 1"""),
                "source_history_date_equals_release_metadata": q(
                    """SELECT h.published_at = c.source_published_now, count(*) FROM lineage.version_check c
                       JOIN lineage.source_version_document h ON h.set_id = c.source_set_id AND h.version = c.source_version_now
                       GROUP BY 1 ORDER BY 1"""),
                "applicable_is_current_version": q(
                    """SELECT applicable_version = source_version_now, count(*) FROM lineage.version_check GROUP BY 1 ORDER BY 1"""),
                "canonical_xml_matches_release": q(
                    "SELECT canonical_xml_matches_release, count(*) FROM lineage.version_check GROUP BY 1 ORDER BY 1"),
                "distinct_source_sets": one("SELECT count(DISTINCT source_set_id) FROM lineage.version_check"),
                "accepted_sites": q(
                    """SELECT c.classification, sum(cardinality(c.sites_now_direct)), sum(cardinality(c.continuing_sites))
                       FROM lineage.version_check c WHERE c.continuing_sites IS NOT NULL GROUP BY 1 ORDER BY 1"""),
            },
            "frozen_sample_v1_v2": frozen_sample(c),
            "manifest_documents": q("SELECT status, count(*) FROM lineage.source_version_document GROUP BY 1 ORDER BY 2 DESC"),
            "eligible_v2_source_label_newer_than_citing": q(
                """SELECT sd.published_date > cd.published_date, count(*) FROM lineage.resolution_v2 v
                   JOIN lineage.source_reference r USING (reference_pk) JOIN lineage.source_resolution x USING (reference_pk)
                   JOIN national.spl_document cd ON cd.document_pk = r.document_pk
                   JOIN national.spl_document sd ON sd.document_pk = x.source_document_pk
                   WHERE v.status = 'ELIGIBLE' GROUP BY 1 ORDER BY 1"""),
        }
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("v1", "v2")}, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
