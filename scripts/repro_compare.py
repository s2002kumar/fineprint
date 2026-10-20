"""Compare a reproduction against the reference build: database fingerprints and evidence files.

  python -I scripts/repro_compare.py --db-a fineprint --db-b fineprint_repro \
      --files REF_DIR CLONE_DIR evidence/historical/frozen/cohort_E.json ... --out report.json
Exit code 0 only if every compared item is identical.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import db, graph, net  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402

VOLATILE = {"generated_at", "started_at", "finished_at", "retrieved_at", "elapsed_ms", "seconds"}


def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if k not in VOLATILE}
    if isinstance(o, list):
        return [strip(v) for v in o]
    return o


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-a")
    ap.add_argument("--db-b")
    ap.add_argument("--files", nargs="*", default=[], help="REF_DIR CLONE_DIR relpath [relpath ...]")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    rep = {"generated_at": net.utc_now(), "databases": {}, "files": {}}
    ok = True
    if a.db_a and a.db_b:
        fps = {}
        for name in (a.db_a, a.db_b):
            with db.connect(name) as c:
                fps[name] = {"dst01": db.fingerprint(c), "graph": graph.fingerprint(c)}
        for layer in ("dst01", "graph"):
            same = fps[a.db_a][layer] == fps[a.db_b][layer]
            rep["databases"][layer] = {"identical": same, a.db_a: fps[a.db_a][layer], a.db_b: fps[a.db_b][layer]}
            ok &= same
    if a.files:
        ref, clone, *paths = a.files
        for rel in paths:
            ra, rb = Path(ref) / rel, Path(clone) / rel
            ba, bb = ra.read_bytes(), rb.read_bytes()
            same_bytes = ba == bb
            same_content = same_bytes or (rel.endswith(".json") and strip(json.loads(ba)) == strip(json.loads(bb)))
            rep["files"][rel] = {"identical_bytes": same_bytes, "identical_ignoring_timestamps": same_content,
                                 "sha256_ref": hashlib.sha256(ba).hexdigest(), "sha256_clone": hashlib.sha256(bb).hexdigest()}
            ok &= same_content
    rep["all_identical"] = ok
    write_json(a.out, rep)
    print(json.dumps({"all_identical": ok, "databases": {k: v["identical"] for k, v in rep["databases"].items()},
                      "files": {k: (v["identical_bytes"], v["identical_ignoring_timestamps"]) for k, v in rep["files"].items()}},
                     indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
