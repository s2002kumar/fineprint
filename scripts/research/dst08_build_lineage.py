"""DST-08: build the source-NDC lineage prototype in a scratch database and record every check of it.

  python -I scripts/research/dst08_build_lineage.py --db fineprint_dst08 --production fineprint

The scratch database must be a copy of the production database (CREATE DATABASE fineprint_dst08 TEMPLATE fineprint);
the production database is only read. The script

  1. proves the scratch copy equals production (ingest fingerprints, every DIRECT edge, every product status);
  2. builds the lineage schema twice and requires identical fingerprints (reproducibility);
  3. proves no national row changed (the same three checks after the build);
  4. compares every reference with the independent raw-XML inventory (references.csv from dst08_source_inventory.py)
     on validity, resolution, resolved source set and chain, and explains each consistency difference;
  5. reports coverage before and after with the DIRECT tier separate, and times the main queries.

With ``--manifest`` (rule v2) each build is followed by lineage.validate_v2 over the frozen history manifest; both v2
runs must give identical fingerprints, and the v1 tables must still equal the v1 record at c8ded0f
(lineage_build.json), so v1's counts and evidence stay measurable beside v2.

Output: docs/research/dst08/lineage_build.json (v1), or lineage_build_v2.json with ``--manifest``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "research"))
import verify_audit_sample as raw  # noqa: E402
from fineprint import db, ingest, lineage  # noqa: E402

OUT = REPO / "docs" / "research" / "dst08" / "lineage_build.json"
INVENTORY = REPO / "docs" / "research" / "dst08" / "source_inventory.json"
REFERENCES = raw.DATA / "research" / "dst08" / "references.csv"
CHAIN_NAMES = {"ENDS_UNRESOLVED": "ENDS_AT_UNRESOLVED_REFERENCE", "UNRESOLVED": "NOT_APPLICABLE"}


def national_state(c) -> dict:
    h = hashlib.sha256()
    for row in c.execute("SELECT assertion_pk, product_pk, report_product_pk, duns, fei, confidence, confidence_reasons "
                         "FROM national.operation_edge ORDER BY assertion_pk"):
        h.update(json.dumps(row, default=str).encode() + b"\n")
    s = hashlib.sha256()
    for row in c.execute("SELECT product_pk, manufacturing_status, evidence_status FROM national.v_product_manufacturing_status "
                         "ORDER BY product_pk"):
        s.update(json.dumps(row, default=str).encode() + b"\n")
    return {"ingest_fingerprint": db.fingerprint(c), "operation_edge_sha256": h.hexdigest(),
            "product_status_sha256": s.hexdigest(),
            "graph_build": c.execute("SELECT max(build_id) FROM national.graph_build WHERE status = 'completed'").fetchone()[0]}


def compare_inventory(c) -> dict:
    data = REFERENCES.read_bytes()
    if hashlib.sha256(data).hexdigest() != json.loads(INVENTORY.read_text(encoding="utf-8"))["references_csv_sha256"]:
        raise SystemExit("references.csv does not match source_inventory.json")
    inv = {(r["set_id"].lower(), int(r["version"]), r["ref_loc"]): r for r in csv.DictReader(data.decode("utf-8").splitlines())}
    proto = {}
    for row in c.execute(
            """SELECT lower(d.set_id), d.version, r.loc, r.validity, x.resolution, lower(x.source_set_id), x.chain,
                      x.consistency, x.status, r.product_kind
               FROM lineage.source_reference r JOIN lineage.source_resolution x USING (reference_pk)
               JOIN national.spl_document d ON d.document_pk = r.document_pk"""):
        proto[row[:3]] = row[3:]
    out = Counter()
    examples: dict[str, list] = {}
    out["inventory_only"] = len(inv.keys() - proto.keys())
    out["prototype_only"] = len(proto.keys() - inv.keys())
    for k in sorted(inv.keys() & proto.keys()):
        i, (validity, resolution, src_set, chain, consistency, status, kind) = inv[k], proto[k]
        out["matched"] += 1
        for name, a, b in (("validity", i["validity"], validity), ("resolution", i["resolution"], resolution),
                           ("product_kind", i["product_kind"], kind),
                           ("chain", CHAIN_NAMES.get(i["chain"], i["chain"]), chain)):
            if a != b:
                out[f"{name}_differs:{a}->{b}"] += 1
                examples.setdefault(f"{name}_differs", []).append(list(k))
        if resolution == "RESOLVED" and (i["candidate_set_ids"] or "").lower() != (src_set or ""):
            out["resolved_source_set_differs"] += 1
        if resolution == "RESOLVED":
            inv_cons = ("FORM_DIFFERS" if i["form_match"] != "True" else
                        "ACTIVE_DIFFERS" if i["active_match"] != "True" else "CONSISTENT")
            if inv_cons != consistency:
                out[f"consistency:{inv_cons}->{consistency}"] += 1
                examples.setdefault(f"consistency:{inv_cons}->{consistency}", []).append(list(k))
    return {"counts": dict(sorted(out.items())), "examples": {k: v[:5] for k, v in sorted(examples.items())}}


def timed(c, sql, params=()) -> dict:
    plan = c.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql, params).fetchone()[0][0]
    return {"execution_ms": round(plan["Execution Time"], 1), "planning_ms": round(plan["Planning Time"], 1)}


def coverage(c) -> dict:
    q = lambda sql: {r[0]: r[1] for r in c.execute(sql).fetchall()}  # noqa: E731
    total = c.execute("SELECT count(*) FROM lineage.v_product_coverage").fetchone()[0]
    before = q("SELECT direct_tier_status, count(*) FROM lineage.v_product_coverage GROUP BY 1")
    after = q("SELECT coverage_tier, count(*) FROM lineage.v_product_coverage GROUP BY 1")
    moved = [list(r) for r in c.execute(
        "SELECT direct_tier_status, count(*) FROM lineage.v_product_coverage WHERE coverage_tier = 'SOURCE_LINKED' "
        "GROUP BY 1 ORDER BY 1").fetchall()]
    sites = [list(r) for r in c.execute(
        """SELECT n_sites, count(*) FROM (SELECT linked_product_pk, count(DISTINCT duns) AS n_sites
               FROM lineage.source_linked_evidence GROUP BY 1) t GROUP BY 1 ORDER BY 1""").fetchall()]
    return {"products": total, "direct_tier": before, "with_source_linked_tier": after,
            "source_linked_by_direct_tier_status": moved,
            "source_linked_products_by_number_of_direct_source_sites": sites}


V1_TABLES = ("source_reference", "source_resolution", "source_linked_evidence")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint_dst08")
    ap.add_argument("--production", default="fineprint")
    ap.add_argument("--manifest", type=Path, help="rule v2: the frozen source history manifest")
    ap.add_argument("--cache", type=Path, default=raw.DATA / "research" / "dst08" / "history")
    a = ap.parse_args()
    commit, dirty = ingest.code_version()
    v1_record = json.loads(OUT.read_text(encoding="utf-8"))["build"]["fingerprint"] if a.manifest else None
    with db.connect(a.production) as p:
        prod = national_state(p)
    with db.connect(a.db, autocommit=True) as c:
        before = national_state(c)
        if before != prod:
            raise SystemExit("the scratch database is not an exact copy of production; recreate it from the template")
        builds, v2 = [], []
        for _ in range(2):
            builds.append(lineage.build(c, code_commit=commit, code_dirty=dirty, log=print))
            if a.manifest:
                v2.append(lineage.validate_v2(c, a.manifest, a.cache, log=print))
        after = national_state(c)
        repro = builds[0]["fingerprint"] == builds[1]["fingerprint"] and (not v2 or v2[0]["fingerprint"] == v2[1]["fingerprint"])
        v1_preserved = (all(builds[-1]["fingerprint"][k] == v1_record[k] for k in V1_TABLES) and
                        lineage.fingerprint(c) == builds[-1]["fingerprint"]) if a.manifest else None
        n54 = c.execute("SELECT r.product_ndc_5_4 FROM lineage.source_linked_evidence e JOIN lineage.source_reference r "
                        "USING (reference_pk) ORDER BY r.reference_pk LIMIT 1").fetchone()[0]
        perf = {"build_seconds": [b["seconds"] for b in builds],
                "evidence_chain_query": timed(c, lineage.CHAIN_SQL, (n54,)),
                "coverage_view_aggregate": timed(c, "SELECT coverage_tier, count(*) FROM lineage.v_product_coverage GROUP BY 1"),
                "source_linked_for_one_product": timed(
                    c, "SELECT * FROM lineage.source_linked_evidence e JOIN lineage.source_reference r USING (reference_pk) "
                       "WHERE r.product_ndc_5_4 = %s", (n54,))}
        t = time.time()
        lineage.evidence_chain(c, n54)
        perf["evidence_chain_with_xml_reread_seconds"] = round(time.time() - t, 2)
        result = {
            "generated_at": raw.utc_now(), "rule_version": lineage.RULE_VERSION, "code_commit": commit, "code_dirty": dirty,
            "scratch_database": a.db, "production_database_read_only": a.production,
            "scratch_equals_production_before": before == prod, "national_unchanged_after": after == prod,
            "national_state": prod, "reproducible": repro, "build": builds[1], "coverage": coverage(c),
            "inventory_comparison": compare_inventory(c), "performance": perf,
        }
        if a.manifest:
            perf["v2_seconds"] = [r["seconds"] for r in v2]
            result.update(rule_version_v2=lineage.V2_RULE_VERSION, v1_tables_equal_c8ded0f_record=v1_preserved,
                          manifest=a.manifest.name, manifest_sha256=hashlib.sha256(a.manifest.read_bytes()).hexdigest(),
                          v2=v2[1])
    text = json.dumps(result, indent=1, default=str) + "\n"
    (OUT.with_name("lineage_build_v2.json") if a.manifest else OUT).write_text(text, encoding="utf-8", newline="\n")
    keys = ("scratch_equals_production_before", "national_unchanged_after", "reproducible") + (
        ("v1_tables_equal_c8ded0f_record",) if a.manifest else ())
    print(json.dumps({k: result[k] for k in keys}))
    return 0 if result["national_unchanged_after"] and repro and v1_preserved is not False else 1


if __name__ == "__main__":
    sys.exit(main())
