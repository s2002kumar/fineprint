"""DST-03: measured latency of representative CLI queries on the real national database.

  python -I scripts/dst03_benchmark.py --db fineprint --repeat 5 --out evidence/dst03/query_benchmark.json
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import bulk, cli, db, net  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402

QUERIES = [
    ["product", "0409-4346"],                                   # sites for one product
    ["product", "00409-1782-03"],                               # package NDC -> product -> sites
    ["facility", "093132819"],                                  # products made at Rocky Mount (current)
    ["facility", "FEI:1925262"],                                # same by facility FEI (McPherson)
    ["compare", "093132819", "030606222", "--labeler", "141588017"],
    ["labeler", "141588017"],
    ["search", "naloxone hydrochloride"],
    ["facility", "080105003"],                                  # unresolved identity
    ["unresolved", "--limit", "25"],
    ["coverage"],
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint")
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    conn = db.connect(a.db)
    rows = []
    for q in QUERIES + [["evidence", None, "--raw"]]:
        if q[0] == "evidence":  # evidence id of Rocky Mount's aminocaproic acid MANUFACTURE edge
            q = ["evidence", str(conn.execute(
                "SELECT assertion_pk FROM national.operation_edge WHERE duns='093132819' AND product_ndc_raw='0409-4346'"
                " AND is_manufacture").fetchone()[0]), "--raw"]
        times = []
        for _ in range(a.repeat):
            t0 = time.perf_counter()
            res = cli.run(["--db", a.db, *q], conn=conn)
            times.append((time.perf_counter() - t0) * 1000)
        text = cli.render(q[0], res)
        rows.append({"argv": q, "ms_min": round(min(times), 1), "ms_median": round(statistics.median(times), 1),
                     "ms_max": round(max(times), 1), "output_head": text.splitlines()[:14]})
        print(f"{' '.join(q):70} median {rows[-1]['ms_median']:>8} ms", file=sys.stderr)
    conn.close()
    write_json(a.out, {"generated_at": net.utc_now(), "database": a.db, "repeat": a.repeat,
                       "peak_rss_bytes": bulk.peak_rss_bytes(), "queries": rows})


if __name__ == "__main__":
    main()
