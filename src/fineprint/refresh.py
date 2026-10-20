"""DST-06: idempotent incremental refresh from an official DailyMed update archive.

Current release state = full-release members + update members − members the update's
files_deleted.txt retracts. Applying the same update twice changes nothing. The diff compares the
operation-edge projection before and after, keyed by (set, product code, DUNS, operation code).
"""

from __future__ import annotations

import zipfile
from pathlib import Path, PurePosixPath

from psycopg.types.json import Jsonb

from . import graph, ingest, safezip

ORDER = {"DIRECT": 0, "TENTATIVE": 1, "UNKNOWN": 2}


def load_retractions(conn, source_file_id: int, path: Path, prefix: str) -> dict:
    with zipfile.ZipFile(path) as zf:
        names = {i.filename for i in zf.infolist()}
        if "files_deleted.txt" not in names:
            return {"listed": 0, "in_scope": 0, "loaded_now": 0, "note": "no files_deleted.txt in archive"}
        lines = safezip.read_member(zf, zf.getinfo("files_deleted.txt"), 64 << 20).decode("utf-8").splitlines()
    rows = [(source_file_id, PurePosixPath(ln.strip()).name, ln.strip()) for ln in lines
            if ln.strip().startswith(prefix)]
    with conn.transaction():
        with conn.cursor() as cur:
            n0 = conn.execute("SELECT count(*) FROM national.release_retraction WHERE update_source_file_id = %s",
                              (source_file_id,)).fetchone()[0]
            cur.executemany("""INSERT INTO national.release_retraction (update_source_file_id, member_basename,
                                   listed_path) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING""", rows)
            n1 = conn.execute("SELECT count(*) FROM national.release_retraction WHERE update_source_file_id = %s",
                              (source_file_id,)).fetchone()[0]
    return {"listed": len(lines), "in_scope": len(rows), "loaded_now": n1 - n0}


def edge_snapshot(conn) -> dict:
    """{key: value} over the current projection; duplicates of a key keep the strongest edge."""
    snap = {}
    for set_key, code, duns, op, conf, ident, fei, ver in conn.execute(
            """SELECT lower(set_id), coalesce(product_ndc_raw, '-'), coalesce(duns, '-'), operation_code,
                      confidence, identity_status, coalesce(fei, '-'), version FROM national.operation_edge"""):
        key = f"{set_key}|{code}|{duns}|{op}"
        val = {"confidence": conf, "identity_status": ident, "fei": fei, "version": ver}
        cur = snap.get(key)
        if cur is None or (ORDER[conf], -ver) < (ORDER[cur["confidence"]], -cur["version"]):
            snap[key] = val
    return snap


def diff(before: dict, after: dict) -> dict:
    out = {"added": [], "removed": [], "modified": [], "carried_forward": []}
    for k in sorted(after.keys() - before.keys()):
        out["added"].append((k, None, after[k]))
    for k in sorted(before.keys() - after.keys()):
        out["removed"].append((k, before[k], None))
    for k in sorted(before.keys() & after.keys()):
        b, a = before[k], after[k]
        core = ("confidence", "identity_status", "fei")
        if any(b[c] != a[c] for c in core):
            out["modified"].append((k, b, a))
        elif b["version"] != a["version"]:
            out["carried_forward"].append((k, b, a))
    return out


def apply_update(conn, *, path: Path, record: dict, advertised: dict, prefix: str, run_id: int,
                 verify: bool = True, log=print) -> dict:
    sid, info = ingest.register_source(conn, kind="dailymed_spl_update", advertised=advertised, record=record,
                                       path=path, release_label=advertised["name"], verify=verify)
    release = conn.execute("SELECT max(release_label) FROM national.source_file "
                           "WHERE kind = 'dailymed_human_rx_full_part'").fetchone()[0]
    with zipfile.ZipFile(path) as zf:
        dates = sorted(PurePosixPath(i.filename).name[:8] for i in zf.infolist() if i.filename.startswith(prefix))
    if release and dates and dates[-1] < release.replace("-", ""):
        raise RuntimeError(f"update {advertised['name']} predates the loaded release {release}; refusing")
    build_before = conn.execute("SELECT max(build_id) FROM national.graph_build WHERE status = 'completed'").fetchone()[0]
    before = edge_snapshot(conn)
    retr = load_retractions(conn, sid, path, prefix)
    st = ingest.ingest_part(conn, source_file_id=sid, path=path, run_id=run_id, member_prefix=prefix, log=log)
    ingest.resolve_published_dates(conn)
    ingest.refresh_operation_types(conn, run_id)
    built = graph.build(conn, log=log)
    after = edge_snapshot(conn)
    changes = diff(before, after)
    counts = {k: len(v) for k, v in changes.items()}
    with conn.transaction():
        rid = conn.execute("""INSERT INTO national.refresh_run (update_source_file_id, build_before, build_after, summary)
                              VALUES (%s, %s, %s, %s) RETURNING refresh_id""",
                           (sid, build_before, built["build_id"], Jsonb({"changes": counts, "ingest": {
                               k: st[k] for k in ("processed", "loaded", "duplicate", "failed", "already_done",
                                                  "skipped_by_prefix")}, "retractions": retr}))).fetchone()[0]
        with conn.cursor() as cur:
            cur.executemany("INSERT INTO national.refresh_change (refresh_id, change, edge_key, before, after) "
                            "VALUES (%s, %s, %s, %s, %s)",
                            [(rid, kind, k, Jsonb(b) if b else None, Jsonb(a) if a else None)
                             for kind, rows in changes.items() for k, b, a in rows])
        conn.execute("UPDATE national.refresh_run SET finished_at = clock_timestamp() WHERE refresh_id = %s", (rid,))
    return {"refresh_id": rid, "source_file_id": sid, "verify": info, "ingest": st, "retractions": retr,
            "build_before": build_before, "build_after": built["build_id"], "changes": counts,
            "selection_status": built["selection_status"], "examples": {k: v[:5] for k, v in changes.items()}}
