"""DST-06: apply one official DailyMed update archive to the national graph and report the diff.

Idempotent: re-applying the same archive ingests nothing and reports zero changes.
No scheduling or automation is installed; this is a manual, on-demand command.

  python -I scripts/dst06_refresh.py --db fineprint_refresh --update dm_spl_daily_update_10192026.zip \
      --out evidence/dst06/refresh_10192026.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import config, dailymed, db, download, ingest, net, refresh  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--update", required=True, help="update archive name as advertised on the DailyMed page")
    ap.add_argument("--member-prefix", default="prescription/")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    page = net.fetch(dailymed.BULK_PAGE).body.decode("utf-8")
    adv = dailymed.parse_advertised_update(page, a.update)
    if adv is None or not adv["https_url"]:
        sys.exit(f"{a.update} is not advertised on {dailymed.BULK_PAGE}")
    dest = config.data_dir() / "raw" / "dailymed" / "updates" / a.update
    rec = download.download(adv["https_url"], dest, expected_md5=adv["advertised_md5"])
    conn = db.connect(a.db, autocommit=True)
    db.migrate(conn)
    run_id = ingest.start_run(conn, {"refresh": a.update, "db": a.db})
    status = "failed"
    try:
        res = refresh.apply_update(conn, path=dest, record=rec, advertised=adv, prefix=a.member_prefix,
                                   run_id=run_id, log=lambda m: print(m, file=sys.stderr))
        status = "completed"
    finally:
        ingest.finish_run(conn, run_id, status, {"refresh": a.update})
        conn.close()
    res["download"] = {k: rec.get(k) for k in ("status", "bytes", "sha256", "md5_matches_advertised")}
    res["advertised"] = adv
    if a.out:
        write_json(a.out, json.loads(json.dumps(res, default=str)))
    print(json.dumps({k: res[k] for k in ("changes", "retractions", "build_before", "build_after")}, indent=1,
                     default=str))


if __name__ == "__main__":
    main()
