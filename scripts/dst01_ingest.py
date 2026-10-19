"""DST-01: ingest verified current human-Rx release parts into PostgreSQL (schema "national").

  python -I scripts/dst01_ingest.py --manifest evidence/dst01/release_manifest.json \
      --db fineprint --out evidence/dst01/ingest_run_full.json
Re-running is idempotent: completed members are skipped and nothing is duplicated.
Test hooks: --crash-after N (hard exit with an open batch), --limit N, --reset (drops schema).
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import bulk, db, ingest, net  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--db", default="fineprint")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--parts", nargs="*", help="part names (default: every part in the manifest)")
    ap.add_argument("--batch-size", type=int, default=200)
    ap.add_argument("--limit", type=int, help="process at most N new members per part")
    ap.add_argument("--crash-after", type=int, help="TEST: os._exit after N members with a batch open")
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--no-verify", action="store_true", help="skip re-hashing source files (not for real runs)")
    ap.add_argument("--reset", action="store_true", help="DROP the national schema first (clean rebuild)")
    a = ap.parse_args(argv)

    t0 = time.perf_counter()
    conn = db.connect(a.db, autocommit=True)
    if a.reset:
        db.reset_national(conn)
    applied = db.migrate(conn)
    args = {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(a).items()}
    run_id = ingest.start_run(conn, args)
    log = lambda m: print(m, file=sys.stderr, flush=True)  # noqa: E731
    out = {"run_id": run_id, "database": a.db, "migrations_applied_now": applied, "started_at": net.utc_now(),
           "parts": {}, "sources": {}}
    status = "failed"
    try:
        inputs = ingest.release_inputs(a.manifest)
        out["release_label"] = inputs["release_label"]
        mi = inputs["zip_metadata"]
        if mi:
            sid, info = ingest.register_source(conn, kind="dailymed_zip_metadata", advertised=mi["advertised"],
                                               record=mi["record"], path=mi["path"],
                                               release_label=inputs["release_label"], verify=not a.no_verify)
            out["sources"]["zip_metadata"] = {"source_file_id": sid, **info,
                                              **ingest.load_zip_metadata(conn, sid, mi["path"])}
        else:
            out["sources"]["zip_metadata"] = {"error": "no metadata file in manifest; published_date stays NULL"}
        any_failed = False
        for p in inputs["parts"]:
            name = p["advertised"]["name"]
            if a.parts and name not in a.parts:
                continue
            if "error" in p:
                out["parts"][name] = {"error": p["error"]}
                any_failed = True
                continue
            sid, info = ingest.register_source(conn, kind="dailymed_human_rx_full_part", advertised=p["advertised"],
                                               record=p["record"], path=p["path"],
                                               release_label=inputs["release_label"], verify=not a.no_verify)
            log(f"{name}: source_file_id={sid} verified={info['verified']} ({info.get('verify_seconds')}s)")
            st = ingest.ingest_part(conn, source_file_id=sid, path=p["path"], run_id=run_id,
                                    batch_size=a.batch_size, retry_failed=a.retry_failed, limit=a.limit,
                                    crash_after=a.crash_after, log=log)
            out["parts"][name] = {"source_file_id": sid, "verify": info, **st,
                                  "advertised_number_of_files": p["advertised"]["advertised_number_of_files"]}
            any_failed |= st["failed"] > 0
        out["published_dates"] = ingest.resolve_published_dates(conn)
        out["operation_types"] = ingest.refresh_operation_types(conn, run_id)
        conn.execute("ANALYZE")
        status = "completed_with_failures" if any_failed else "completed"
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
        raise
    finally:
        out["wall_seconds"] = round(time.perf_counter() - t0, 2)
        out["peak_rss_bytes"] = bulk.peak_rss_bytes()
        out["database_bytes"] = conn.execute("SELECT pg_database_size(current_database())").fetchone()[0]
        out["table_counts"] = db.table_counts(conn)
        out["status"] = status
        out["finished_at"] = net.utc_now()
        ingest.finish_run(conn, run_id, status, {k: v for k, v in out.items() if k != "operation_types"})
        if a.out:
            write_json(a.out, out)
        conn.close()
    print(json.dumps({"run_id": run_id, "status": status, "wall_seconds": out["wall_seconds"],
                      "table_counts": out["table_counts"]}, indent=1))


if __name__ == "__main__":
    main()
