"""DST-02: rebuild the current provenance graph projection (idempotent, atomic).

  python -I scripts/dst02_build_graph.py --db fineprint --out evidence/dst02/graph_build.json [--verify-rebuild]
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import bulk, db, graph, net  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--verify-rebuild", action="store_true", help="build twice and require identical fingerprints")
    a = ap.parse_args(argv)
    conn = db.connect(a.db, autocommit=True)
    db.migrate(conn)
    base_before = db.fingerprint(conn)
    runs = []
    for _ in range(2 if a.verify_rebuild else 1):
        t0 = time.perf_counter()
        res = graph.build(conn, log=lambda m: print(m, file=sys.stderr))
        runs.append({"build_id": res["build_id"], "seconds": round(time.perf_counter() - t0, 2),
                     "fingerprint": res["fingerprint"]})
    out = {"generated_at": net.utc_now(), "database": a.db, "rule_version": graph.RULE_VERSION, "builds": runs,
           "summary": {k: v for k, v in res.items() if k not in ("fingerprint", "build_id")},
           "dst01_base_unchanged": db.fingerprint(conn) == base_before,
           "peak_rss_bytes": bulk.peak_rss_bytes()}
    if a.verify_rebuild:
        out["rebuild_fingerprints_equal"] = runs[0]["fingerprint"] == runs[1]["fingerprint"]
    if a.out:
        write_json(a.out, out)
    conn.close()
    print(json.dumps({k: out[k] for k in out if k in ("builds", "summary", "dst01_base_unchanged",
                                                      "rebuild_fingerprints_equal")}, indent=1, default=str))


if __name__ == "__main__":
    main()
