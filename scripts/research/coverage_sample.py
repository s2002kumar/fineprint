"""Freeze the 120-product diagnostic sample for the manufacturing-coverage investigation (research workstream C1).

Strata (by the published reference denominators, graph build 8 on DailyMed release 2026-10-16):
  25 OTHER_OPERATIONS_ONLY, 25 NO_ESTABLISHMENT_BLOCK, 25 ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT,
  15 ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT (the four NO_MANUFACTURE_EVIDENCE reasons),
  15 UNKNOWN_SITE, 10 TENTATIVE, 5 DIRECT (positive controls).

Deterministic: rows of each stratum are ordered by natural key (set_id, product NDC, XML location) and sampled with
random.Random(SEED).sample, so the same database contents give the same sample regardless of surrogate keys. The
manifest records the dataset version (graph build, fingerprints, source-file hashes) and every sampled product's
source location (release part, archive member, member and XML SHA-256). A FREEZE file holds the manifest's hash.

Small strata are deliberately oversampled: raw sample proportions are NOT population prevalence.

  python -I scripts/research/coverage_sample.py --db fineprint
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from fineprint import db, graph  # noqa: E402  (database access only; no classification logic is reused)

SEED = "fineprint-coverage-diagnosis-2026-10-22"
PLAN = [("OTHER_OPERATIONS_ONLY", "evidence", 25), ("NO_ESTABLISHMENT_BLOCK", "evidence", 25),
        ("ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT", "evidence", 25),
        ("ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT", "evidence", 15),
        ("UNKNOWN_SITE", "status", 15), ("TENTATIVE", "status", 10), ("DIRECT", "status", 5)]
REFERENCE = {"products": 80508, "DIRECT": 24614, "TENTATIVE": 435, "UNKNOWN_SITE": 1002,
             "NO_MANUFACTURE_EVIDENCE": 54457, "OTHER_OPERATIONS_ONLY": 28123, "NO_ESTABLISHMENT_BLOCK": 18453,
             "ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT": 7762, "ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT": 119}

ROW_SQL = """
SELECT v.product_pk, v.set_id, v.version, v.selection_class, v.ndc_raw, v.ndc_product_5_4, v.name,
       v.manufacturing_status, v.evidence_status, p.loc, p.dosage_form, p.routes, p.generic_name,
       d.document_id, d.xml_sha256, d.member_name, d.xml_member_name, d.effective_time_raw, d.published_date,
       d.n_products, d.n_establishments, d.n_operation_assertions, d.document_type_name,
       f.name AS part, f.sha256 AS part_sha256, m.member_sha256,
       (SELECT array_agg(DISTINCT o.name ORDER BY o.name) FROM national.organization_mention o
         WHERE o.document_pk = p.document_pk AND o.role = 'labeler') AS labeler_names,
       (SELECT array_agg(DISTINCT o.duns ORDER BY o.duns) FROM national.organization_mention o
         WHERE o.document_pk = p.document_pk AND o.role = 'labeler' AND o.duns IS NOT NULL) AS labeler_duns
FROM tmp_status v
JOIN national.product p ON p.product_pk = v.product_pk
JOIN national.spl_document d ON d.document_pk = p.document_pk
JOIN national.archive_member m ON m.document_pk = d.document_pk AND m.status = 'loaded'
JOIN national.source_file f ON f.source_file_id = m.source_file_id
WHERE {where}
ORDER BY v.set_id, v.ndc_raw, p.loc
"""

EDGE_SQL = """
SELECT e.assertion_pk, e.operation_code, e.operation_name, e.product_scope, e.product_ndc_raw, e.duns,
       e.identity_status, e.fei, e.confidence, e.confidence_reasons, e.loc
FROM national.operation_edge e WHERE e.report_product_pk = %s ORDER BY e.assertion_pk
"""


def git_head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint")
    ap.add_argument("--out-dir", default=str(REPO / "docs" / "research"))
    a = ap.parse_args()
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with db.connect(a.db) as c:
        build = c.execute("SELECT build_id, finished_at, code_commit, code_dirty, rule_version FROM national.graph_build "
                          "WHERE status = 'completed' ORDER BY build_id DESC LIMIT 1").fetchone()
        refresh = c.execute("SELECT count(*) FROM national.refresh_run").fetchone()[0]
        fp = graph.fingerprint(c)
        fp.update(db.fingerprint(c))
        src = [dict(zip(("source_file_id", "kind", "name", "sha256", "generated_at", "release_label"), r)) for r in c.execute(
            "SELECT source_file_id, kind, name, sha256, generated_at::text, release_label FROM national.source_file ORDER BY 1")]
        # materialize the status view once: joining the aggregate view per stratum re-computes it for every row
        c.execute("CREATE TEMP TABLE tmp_status AS SELECT * FROM national.v_product_manufacturing_status")
        c.execute("CREATE INDEX ON tmp_status (manufacturing_status, evidence_status)")
        c.execute("CREATE INDEX ON tmp_status (product_pk)")
        pop = {}
        for status, n in c.execute("SELECT manufacturing_status, count(*) FROM tmp_status GROUP BY 1"):
            pop[status] = n
        for status, n in c.execute("SELECT evidence_status, count(*) FROM tmp_status "
                                   "WHERE manufacturing_status = 'NO_MANUFACTURE_EVIDENCE' GROUP BY 1"):
            pop[status] = n
        pop["products"] = sum(v for k, v in pop.items() if k in ("DIRECT", "TENTATIVE", "UNKNOWN_SITE", "NO_MANUFACTURE_EVIDENCE"))
        mismatch = {k: (pop.get(k), v) for k, v in REFERENCE.items() if pop.get(k) != v}
        rng = random.Random(SEED)
        sample, n = [], 0
        for stratum, kind, k in PLAN:
            where = ("v.manufacturing_status = 'NO_MANUFACTURE_EVIDENCE' AND v.evidence_status = %s" if kind == "evidence"
                     else "v.manufacturing_status = %s")
            cur = c.execute(ROW_SQL.format(where=where), (stratum,))
            cols = [d.name for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            assert len(rows) == pop[stratum], (stratum, len(rows), pop[stratum])
            for r in rng.sample(rows, k):
                n += 1
                r = {kk: (str(vv) if isinstance(vv, (dt.date, dt.datetime)) else vv) for kk, vv in r.items()}
                ecur = c.execute(EDGE_SQL, (r["product_pk"],))
                ecols = [d.name for d in ecur.description]
                r["graph_edges_for_product"] = [dict(zip(ecols, e)) for e in ecur.fetchall()]
                r["manufacture_edges"] = [e for e in r["graph_edges_for_product"] if e["operation_code"] == "C43360"]
                r["unscoped_operations_in_document"] = [dict(zip(("assertion_pk", "operation_code", "duns"), x)) for x in c.execute(
                    """SELECT a.assertion_pk, a.operation_code, a.duns FROM national.operation_assertion a
                       JOIN national.product p ON p.document_pk = a.document_pk
                       WHERE p.product_pk = %s AND a.product_scope = 'no_product_scope' ORDER BY 1""", (r["product_pk"],))]
                sample.append({"sample_id": f"S{n:03d}", "stratum": stratum, "stratum_population": pop[stratum], **r})
    manifest = {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "purpose": "research workstream C1: frozen diagnostic sample; oversamples small strata, NOT population prevalence",
        "seed": SEED, "plan": [{"stratum": s, "n": k} for s, _, k in PLAN],
        "sampling": "rows ordered by (set_id, ndc_raw, loc); random.Random(seed).sample per stratum, strata in plan order",
        "dataset": {"database": a.db, "graph_build": {"build_id": build[0], "finished_at": str(build[1]),
                                                       "code_commit": build[2], "code_dirty": build[3],
                                                       "rule_version": build[4]},
                    "refresh_runs_applied": refresh, "fingerprints": fp, "source_files": src,
                    "population_counts": pop, "reference_counts": REFERENCE, "reference_mismatch": mismatch},
        "code_commit_at_freeze": git_head(),
        "products": sample,
    }
    mp = out_dir / "coverage_sample_manifest.json"
    body = json.dumps(manifest, indent=1, default=str)
    mp.write_text(body, encoding="utf-8", newline="\n")
    h = hashlib.sha256(mp.read_bytes()).hexdigest()
    freeze = {"frozen_at": manifest["generated_at"], "file": "docs/research/coverage_sample_manifest.json",
              "sha256": h, "seed": SEED, "n": len(sample), "graph_build": build[0], "code_commit": manifest["code_commit_at_freeze"],
              "rule": "The manifest must not change after this freeze; any replacement sample gets a new file and a new freeze."}
    (out_dir / "coverage_sample_FREEZE.json").write_text(json.dumps(freeze, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps({"n": len(sample), "sha256": h, "population": pop, "reference_mismatch": mismatch}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
