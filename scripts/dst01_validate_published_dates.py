"""DST-01: check documented UPLOAD_DATE (zip metadata) against the DailyMed history service.

Seeded sample of ingested documents; for each, the history service's published_date for
that exact version is compared with spl_document.published_date and member_name_date.

  python -I scripts/dst01_validate_published_dates.py --db fineprint --n 60 \
      --out evidence/dst01/published_date_check.json
"""

import argparse
import datetime as dt
import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import dailymed, db, net  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint")
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--seed", default="fineprint-dst01")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    with db.connect(a.db) as c:
        sample = c.execute(
            """SELECT set_id, version, published_date, member_name_date, effective_date FROM national.spl_document
               ORDER BY md5(%s || set_id || ':' || version) LIMIT %s""", (a.seed, a.n)).fetchall()
    rows = []
    for set_id, version, pub, mdate, eff in sample:
        r = net.fetch(dailymed.HISTORY.format(setid=set_id, page=1))
        time.sleep(0.4)
        hist = json.loads(r.body.decode("utf-8"))["data"]["history"]
        h = next((x for x in hist if int(x["spl_version"]) == version), None)
        hdate = dt.date.fromisoformat(dailymed.parse_history_date(h["published_date"])) if h else None

        def diff(x):
            return (x - hdate).days if (x and hdate) else None
        rows.append({"set_id": set_id, "version": version, "history_published": str(hdate) if hdate else None,
                     "upload_date": str(pub) if pub else None, "member_name_date": str(mdate) if mdate else None,
                     "effective_date": str(eff) if eff else None, "upload_minus_history_days": diff(pub),
                     "member_name_minus_history_days": diff(mdate), "effective_minus_history_days": diff(eff),
                     "history_sha256": r.sha256})
    summ = {}
    for k in ("upload_minus_history_days", "member_name_minus_history_days", "effective_minus_history_days"):
        vals = [x[k] for x in rows if x[k] is not None]
        summ[k] = {"compared": len(vals), "exact": sum(v == 0 for v in vals),
                   "distribution": dict(sorted(Counter(vals).items()))}
    summ["version_missing_from_history"] = sum(1 for x in rows if x["history_published"] is None)
    write_json(a.out, {"generated_at": net.utc_now(), "seed": a.seed, "n": len(rows), "summary": summ, "rows": rows})
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
