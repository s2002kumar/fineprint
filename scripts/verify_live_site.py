"""Compare every tracked file under site/ with what the deployed explorer serves, byte for byte.

  python -I scripts/verify_live_site.py https://s2002kumar.github.io/fineprint/ --out evidence/explorer/live_files_check.json

Downloads with fineprint's generic User-Agent and records each file's SHA-256 locally and live. Read-only.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # works under python -I
from fineprint.net import USER_AGENT  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("--out")
    args = ap.parse_args()
    base = args.base.rstrip("/") + "/"
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    tracked = subprocess.run(["git", "ls-files", "site"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    rows, bad = [], []
    for rel in sorted(tracked):
        local = (ROOT / rel).read_bytes()
        url = base + rel[len("site/"):]
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=60) as r:
            live, status = r.read(), r.status
        same = live == local
        rows.append({"path": rel, "status": status, "bytes": len(local), "sha256": hashlib.sha256(local).hexdigest(),
                     "live_identical": same})
        if not same:
            bad.append(rel)
    out = {"site": base, "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "repo_commit": commit,
           "files": len(rows), "identical": len(rows) - len(bad), "differing": bad, "ok": not bad, "results": rows}
    text = json.dumps(out, indent=1) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in out.items() if k != "results"}, indent=1))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
