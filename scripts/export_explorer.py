"""Deterministic static datasets for the Facility Evidence Explorer (site/).

  python -I scripts/export_explorer.py --db fineprint           # (re)write site/data/
  python -I scripts/export_explorer.py --db fineprint --verify  # re-export in memory; must equal the files on disk
  python -I scripts/export_explorer.py --check                  # no database: manifest checksums vs files

Two datasets, never mixed:
  current/     the CURRENT graph (DailyMed release + FDA registration files loaded in the database).
               MANUFACTURE edges for every establishment DUNS, sharded by the first two DUNS digits, plus
               all operations for the two example facilities.
  historical/  the frozen 2023 Rocky Mount replay, derived only from evidence/historical/ (no database).

Output depends only on database contents and committed evidence: rows are ordered by natural keys,
timestamps are UTC, and no wall-clock time is written. Personal contact fields are never stored in
the database, so they cannot be exported; no label text or raw archive is exported.
"""

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))  # works under python -I

OUT = REPO / "site" / "data"
HIST = REPO / "evidence" / "historical"
EXAMPLES = {"093132819": "Hospira Rocky Mount, NC", "030606222": "Hospira McPherson, KS"}
ATTRIBUTION = "Courtesy of the U.S. National Library of Medicine"
CURRENCY = ("These datasets are dated snapshots. They do not reflect the most current/accurate data available "
            "from NLM. Current labels: https://dailymed.nlm.nih.gov/")
INDEPENDENCE = ("fineprint is an independent project. It is not affiliated with or endorsed by NLM, NIH, FDA, HHS, "
                "Pfizer or Hospira. Not medical advice; says nothing about current drug availability.")

EDGE_COLUMNS = ["evidence_id", "duns", "operation", "confidence", "reasons", "product", "scope",
                "operation_product_code", "set_id", "loc"]
PRODUCT_COLUMNS = ["ndc_5_4", "ndc_raw", "name", "dosage_form", "packages_11"]
DOCUMENT_COLUMNS = ["version", "document_id", "published_date", "effective_date", "selection_class",
                    "selection_status", "labelers", "part", "member", "xml_member", "xml_sha256"]
INDEX_COLUMNS = ["duns", "status", "fei", "firm_name", "address", "as_of", "expires", "identity_source",
                 "identity_line", "fei_changed", "fei_other_duns", "spl_names", "mfg_direct", "mfg_tentative",
                 "mfg_unknown", "mfg_products", "other_operations", "labeler_documents", "example"]


def jdump(obj) -> bytes:
    def conv(o):
        if isinstance(o, dt.datetime):
            return o.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if isinstance(o, dt.date):
            return o.isoformat()
        raise TypeError(type(o))
    return (json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=conv) + "\n").encode("utf-8")


# ---------------------------------------------------------------------------------------- current graph
EDGE_SQL = """
SELECT e.assertion_pk, e.duns, e.operation_name, e.confidence, e.confidence_reasons, e.report_product_pk,
       e.product_scope, e.product_ndc_raw, e.set_id, e.loc
FROM national.operation_edge e WHERE {where}
ORDER BY e.duns, e.set_id COLLATE "C", e.loc COLLATE "C", e.operation_name, e.product_ndc_raw COLLATE "C",
         e.assertion_pk"""


def _edges(conn, where, params=()):
    return [list(r) for r in conn.execute(EDGE_SQL.format(where=where), params).fetchall()]


def _products(conn, pks):
    if not pks:
        return {}
    rows = conn.execute("""
        SELECT p.product_pk, p.ndc_product_5_4, p.ndc_raw, p.name, p.dosage_form,
               coalesce((SELECT array_agg(DISTINCT k.ndc_package_5_4_2 ORDER BY k.ndc_package_5_4_2)
                         FROM national.package k WHERE k.product_pk = p.product_pk
                           AND k.ndc_package_5_4_2 IS NOT NULL), '{}')
        FROM national.product p WHERE p.product_pk = ANY(%s)""", (sorted(pks),)).fetchall()
    return {str(r[0]): list(r[1:]) for r in sorted(rows)}


def _documents(conn, set_ids):
    if not set_ids:
        return {}
    rows = conn.execute("""
        SELECT s.set_id, s.selected_version, d.document_id, s.published_date, d.effective_date, s.selection_class,
               s.selection_status,
               coalesce((SELECT array_agg(DISTINCT o.name ORDER BY o.name) FROM national.organization_mention o
                         WHERE o.document_pk = d.document_pk AND o.role = 'labeler'), '{}'),
               f.name, d.member_name, d.xml_member_name, d.xml_sha256
        FROM national.set_version_selection s
        JOIN national.spl_document d ON d.document_pk = s.document_pk
        JOIN national.source_file f ON f.source_file_id = d.source_file_id
        WHERE s.set_id = ANY(%s)""", (sorted(set_ids),)).fetchall()
    return {r[0]: list(r[1:]) for r in sorted(rows)}


def _bundle(conn, edges, **head):
    return {**head, "edge_columns": EDGE_COLUMNS, "edges": edges,
            "product_columns": PRODUCT_COLUMNS, "products": _products(conn, {e[5] for e in edges if e[5]}),
            "document_columns": DOCUMENT_COLUMNS, "documents": _documents(conn, {e[8] for e in edges})}


def current_files(conn) -> dict:
    conn.execute("SET TIME ZONE 'UTC'")
    files = {}
    q = lambda sql, p=(): conn.execute(sql, p).fetchall()  # noqa: E731
    sources = {str(r[0]): {"kind": r[1], "name": r[2], "url": r[3], "label": r[4], "generated_at": r[5],
                           "captured_at": r[6], "sha256": r[7]}
               for r in q("""SELECT source_file_id, kind, name, url, release_label, generated_at, captured_at, sha256
                             FROM national.source_file WHERE kind LIKE 'fda_decrs%%' ORDER BY source_file_id""")}
    mfg = defaultdict(lambda: [0, 0, 0, set()])
    for duns, conf, pk in q("SELECT duns, confidence, report_product_pk FROM national.operation_edge "
                            "WHERE is_manufacture AND duns IS NOT NULL"):
        m = mfg[duns]
        m[("DIRECT", "TENTATIVE", "UNKNOWN").index(conf)] += 1
        if pk:
            m[3].add(pk)
    other = defaultdict(dict)
    for duns, op, n in q("""SELECT duns, operation_name, count(*) FROM national.operation_edge
                            WHERE NOT is_manufacture AND duns IS NOT NULL GROUP BY 1, 2 ORDER BY 1, 2"""):
        other[duns][op] = n
    labeler = dict(q("""SELECT o.duns, count(DISTINCT o.document_pk) FROM national.organization_mention o
                        JOIN national.set_version_selection s ON s.document_pk = o.document_pk
                        WHERE o.role = 'labeler' AND o.duns IS NOT NULL GROUP BY 1"""))
    fei_duns = {fei: duns for fei, duns in q("SELECT fei, duns FROM national.facility")}
    rows = []
    for (duns, status, fei, firm, addr, as_of, exp, src, line, changed, names) in q("""
            SELECT i.duns, i.status, i.fei, i.firm_name, i.address, i.evidence_as_of, i.evidence_expiration,
                   i.evidence_source_file_id, r.line_no, i.fei_changed, i.spl_names
            FROM national.duns_identity i LEFT JOIN national.registration_record r USING (registration_pk)
            ORDER BY i.duns"""):
        m = mfg.get(duns, [0, 0, 0, set()])
        rows.append([duns, status, fei, firm, addr, as_of, exp, str(src) if src else None, line, changed,
                     sorted(d for d in fei_duns.get(fei, []) if d != duns), sorted(names or []),
                     m[0], m[1], m[2], len(m[3]), other.get(duns, {}), labeler.get(duns, 0), duns in EXAMPLES])
    files["current/facilities.json"] = {"dataset": "current", "kind": "facility_index",
                                        "identity_sources": sources, "columns": INDEX_COLUMNS, "rows": rows}

    by_shard = defaultdict(list)
    for e in _edges(conn, "e.is_manufacture AND e.duns IS NOT NULL"):
        by_shard[e[1][:2]].append(e)
    for shard in sorted(by_shard):
        files[f"current/manufacture/{shard}.json"] = _bundle(
            conn, by_shard[shard], dataset="current", kind="manufacture_edges", shard=shard)
    for duns, label in EXAMPLES.items():
        files[f"current/examples/{duns}.json"] = _bundle(
            conn, _edges(conn, "e.duns = %s", (duns,)), dataset="current", kind="all_operations_example",
            duns=duns, label=label)
    return files


def current_manifest(conn) -> dict:
    from fineprint import db, graph
    conn.execute("SET TIME ZONE 'UTC'")
    q = lambda sql: conn.execute(sql).fetchall()  # noqa: E731
    parts = [{"name": r[0], "url": r[1], "bytes": r[2], "sha256": r[3], "md5_matches_advertised": r[4]}
             for r in q("""SELECT name, url, bytes, sha256, md5_matches_advertised FROM national.source_file
                           WHERE kind = 'dailymed_human_rx_full_part' ORDER BY name""")]
    meta = q("SELECT name, url, sha256 FROM national.source_file WHERE kind = 'dailymed_zip_metadata'")
    build = q("""SELECT build_id, rule_version, code_commit, finished_at FROM national.graph_build
                 WHERE status = 'completed' ORDER BY build_id DESC LIMIT 1""")[0]
    updates = q("SELECT count(*) FROM national.source_file WHERE kind = 'dailymed_spl_update'")[0][0]
    rel = q("SELECT max(release_label) FROM national.source_file WHERE kind = 'dailymed_human_rx_full_part'")[0][0]
    reg = q("SELECT max(release_label) FROM national.source_file WHERE kind = 'fda_decrs_registration'")[0][0]
    return {
        "description": "Current-release provenance graph: what the loaded DailyMed labels and FDA registration "
                       "files assert. Not a historical state and not live data.",
        "dailymed_release": rel, "release_parts": parts,
        "zip_metadata": [{"name": n, "url": u, "sha256": s} for n, u, s in meta],
        "daily_updates_applied": updates,
        "fda_registration_as_of": reg,
        "graph_build": {"build_id": build[0], "rule_version": build[1], "code_commit": build[2],
                        "finished_at": build[3]},
        "fingerprints": {**db.fingerprint(conn), **graph.fingerprint(conn)},
        "scope": "MANUFACTURE edges for every establishment DUNS; all operations for the two example facilities",
        "not_exported": ["label text", "raw archives", "products whose labels assert no manufacturing site "
                         "(they have no facility edge to show; see docs/ARCHITECTURE.md)"],
    }


# ---------------------------------------------------------------------------------------- historical replay
HIST_INPUTS = ["frozen/FREEZE_MANIFEST.json", "frozen/cohort_E.json", "frozen/cohort_M.json",
               "frozen/documents.json", "frozen/identity.json", "evaluation_results.json"]
PACKAGE_COLUMNS = ["package_ndc_11", "classification", "graph_flag", "b2", "in_may_2023_listing",
                   "on_warning_list", "provenance"]
PROVENANCE_COLUMNS = ["set_id", "version", "product_ndc_raw", "package_ndc_raw", "form", "routes", "sources",
                      "manufacture_duns", "rocky_mount_manufacture_locs", "document_kind", "document_url",
                      "published_date", "effective_time", "xml_sha256"]


def historical_files() -> dict:
    """Pure function of the committed, frozen evidence (stdlib only; never touches the database)."""
    load = lambda p: json.loads((HIST / p).read_text(encoding="utf-8"))  # noqa: E731
    E, M, docs, ident, res = (load("frozen/cohort_E.json"), load("frozen/cohort_M.json"),
                              load("frozen/documents.json")["documents"], load("frozen/identity.json"),
                              load("evaluation_results.json"))
    positives = set(res["cohorts"]["E"]["positives_in_cohort"]) | set(res["uncovered_positives"])
    rows = []
    for ndc11 in sorted(E["packages"]):
        p = E["packages"][ndc11]
        prov = []
        for v in p["provenance"]:
            d = docs[v["set_id"]]
            prov.append([v["set_id"], int(v["version"]), v["product_ndc_raw"], v["package_ndc_raw"], v["form"],
                         v["routes"], v["sources"], v["manufacture_duns"], v["rocky_mount_manufacture_locs"],
                         d["kind"], d["url"], d["published_date"], d["effective_time"], d["xml_sha256"]])
        rows.append([ndc11, p["classification"], p["graph_flag"], p["b2"], p["in_may_2023_listing"],
                     ndc11 in positives, prov, None])
    for ndc11, why in sorted(res["uncovered_positives"].items()):
        rows.append([ndc11, "NOT_IN_COHORT", False, None, None, True, [], why])
    return {"historical/rocky_mount_2023.json": {
        "dataset": "historical", "kind": "frozen_replay",
        "event": "2023-07-19 tornado at Pfizer/Hospira Rocky Mount, NC", "cutoff": E["cutoff"],
        "site": {"duns": "093132819", "fei": ident["rocky_mount_rows"][0]["FEI_NUMBER"],
                 "address": ident["rocky_mount_rows"][0]["ADDRESS"], "identity_source": ident["source"],
                 "identity_source_sha256": ident["sha256"], "identity_fda_generated": ident["fda_generated"],
                 "caveat": ident["caveat"]},
        "seal": res["seal"],
        "outcome": {k: res["outcome"][k] for k in ("url", "sha256", "retrieved_at", "last_modified",
                                                    "distinct_package_ndc_11")},
        "metrics": {c: res["cohorts"][c]["metrics"] for c in ("E", "M")},
        "cohort_sizes": {"E": E["summary"]["size"], "M": len(M["packages"])},
        "flagged_not_listed": {c: res["cohorts"][c]["flagged_not_listed"] for c in ("E", "M")},
        "b3": res["cohorts"]["E"]["B3_already_short"],
        "exploratory_post_hoc_not_preregistered": res["exploratory_post_hoc_not_preregistered"],
        "caveats": res["caveats"],
        "package_columns": PACKAGE_COLUMNS + ["note"], "provenance_columns": PROVENANCE_COLUMNS,
        "packages": rows}}


def historical_manifest() -> dict:
    E = json.loads((HIST / "frozen/cohort_E.json").read_text(encoding="utf-8"))
    res = json.loads((HIST / "evaluation_results.json").read_text(encoding="utf-8"))
    return {
        "description": "Frozen historical replay: SPL versions published on or before the cutoff, scored against "
                       "Pfizer's July 21, 2023 low-inventory warning list after the outcome was unsealed. "
                       "Separate from the current graph.",
        "cutoff": E["cutoff"], "seal": res["seal"],
        "inputs": {f"evidence/historical/{p}": hashlib.sha256((HIST / p).read_bytes()).hexdigest()
                   for p in HIST_INPUTS},
    }


# ---------------------------------------------------------------------------------------- manifest / io
def git_head():
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True,
                              check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", "src", "scripts", "migrations"],
                                    cwd=REPO, capture_output=True, text=True, check=True).stdout.strip())
        return head, dirty
    except (OSError, subprocess.CalledProcessError):
        return None, None


def script_sha256() -> str:
    """Hash of this script as git stores it (LF line endings), so it is the same on every checkout."""
    return hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def count_rows(obj):
    return len(obj.get("rows") or obj.get("edges") or obj.get("packages") or [])


def build_all(conn):
    data = {**current_files(conn), **historical_files()}
    blobs = {p: jdump(o) for p, o in sorted(data.items())}
    head, dirty = git_head()
    manifest = {
        "name": "fineprint Facility Evidence Explorer datasets",
        "attribution": ATTRIBUTION, "currency": CURRENCY, "independence": INDEPENDENCE,
        "license": {"code": "MIT (LICENSE); covers fineprint's code and documentation only",
                    "data": "Third-party data keeps its own terms: DailyMed/NLM terms and conditions; FDA content "
                            "is public domain unless noted. See NOTICE.md."},
        "privacy": "No personal contact fields (they are dropped at parse time and never stored), no label text, "
                   "no raw archives.",
        "generated_by": {"script": "scripts/export_explorer.py",
                         "script_sha256": script_sha256(),
                         "command": "python -I scripts/export_explorer.py --db <database>",
                         "code_commit": head, "code_dirty": dirty,
                         "deterministic": "data files depend only on database contents and committed evidence"},
        "datasets": {"current": current_manifest(conn), "historical": historical_manifest()},
        "csv": "CSV files are produced in the browser from these JSON rows (site/explorer-core.js). Cells that "
               "start with = + - @ are prefixed with ' to stop spreadsheet formula execution.",
        "files": {p: {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b), "rows": count_rows(data[p])}
                  for p, b in blobs.items()},
    }
    blobs["manifest.json"] = jdump(manifest)
    return blobs


def check(out: Path) -> list:
    """No database needed: every manifest entry matches its file and no unlisted data file exists."""
    problems = []
    man = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    for p, meta in man["files"].items():
        f = out / p
        if not f.exists():
            problems.append(f"missing {p}")
        elif hashlib.sha256(f.read_bytes()).hexdigest() != meta["sha256"]:
            problems.append(f"checksum differs {p}")
    on_disk = {f.relative_to(out).as_posix() for f in out.rglob("*.json")} - {"manifest.json"}
    problems += [f"not in manifest {p}" for p in sorted(on_disk - set(man["files"]))]
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--verify", action="store_true", help="re-export in memory and compare with the files")
    ap.add_argument("--check", action="store_true", help="checksums only; no database")
    a = ap.parse_args(argv)
    if a.check:
        problems = check(a.out)
        print("\n".join(problems) or f"ok: {a.out} matches its manifest")
        return 1 if problems else 0
    if not a.db:
        ap.error("--db is required unless --check")
    from fineprint import db
    conn = db.connect(a.db)
    try:
        blobs = build_all(conn)
    finally:
        conn.close()
    if a.verify:
        diffs = [p for p, b in blobs.items() if p != "manifest.json"
                 and (not (a.out / p).exists() or (a.out / p).read_bytes() != b)]
        man = json.loads((a.out / "manifest.json").read_text(encoding="utf-8"))
        fresh = json.loads(blobs["manifest.json"])
        if man["files"] != fresh["files"] or man["datasets"] != fresh["datasets"]:
            diffs.append("manifest.json (files/datasets)")
        print("\n".join(f"DIFFERS {p}" for p in diffs) or f"ok: {len(blobs) - 1} data files are byte-identical "
                                                             "to a fresh export")
        return 1 if diffs else 0
    for p in list((a.out / "current").rglob("*.json")) if (a.out / "current").exists() else []:
        p.unlink()  # shards that no longer exist must not linger
    for p, b in blobs.items():
        f = a.out / p
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b)
    total = sum(len(b) for b in blobs.values())
    print(json.dumps({"files": len(blobs), "bytes": total,
                      "edges": sum(v["rows"] for k, v in json.loads(blobs["manifest.json"])["files"].items()
                                   if k.startswith("current/manufacture/"))}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
