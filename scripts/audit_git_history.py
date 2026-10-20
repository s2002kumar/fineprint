"""Audit ALL local git history (every blob reachable from every ref, plus commit metadata) for
personal paths, contact data and secrets. Read-only: it never rewrites history.

Matched values are masked in the output; the project database password is compared in memory
and never printed.

  python -I scripts/audit_git_history.py --out evidence/security/git_history_audit.json
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))  # works under python -I
from fineprint import config, net  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402

ALLOWED_EMAILS = {"noreply@anthropic.com"}
PATTERNS = {
    "email": re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"),
    "windows_home_path": re.compile(rb"[A-Za-z]:(?:\\\\|\\|/)+Users(?:\\\\|\\|/)+[^\\/\"\s]+"),
    "posix_home_path": re.compile(rb"(?:/c/Users/|/home/|/Users/)[^/\"\s]+"),
    "contact_markup": re.compile(rb"<contactParty|mailto:|tel:\+?[0-9]"),
    "secret_like": re.compile(rb"(?i)(?:password\s*[=:]\s*\S{6,}|PGPASSWORD=|BEGIN [A-Z ]*PRIVATE KEY|"
                              rb"AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,})"),
}


def git(*args, input=None):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, input=input, check=True).stdout


def mask(b: bytes, kind: str) -> str:
    """Category token only (email keeps just its domain): the report must not leak fragments itself."""
    if kind == "email":
        return "<email at " + b.decode("utf-8", "replace").partition("@")[2].lower() + ">"
    return f"<{kind}>"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    user = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    pw_file = config.data_dir() / "secrets" / "pg_superuser_password"
    secret = pw_file.read_bytes().strip() if pw_file.exists() else None

    objs = git("rev-list", "--all", "--objects").decode().splitlines()
    paths = defaultdict(set)
    for line in objs:
        sha, _, path = line.partition(" ")
        if path:
            paths[sha].add(path)
    types = git("cat-file", "--batch-check=%(objectname) %(objecttype)", input="\n".join(paths).encode()).decode()
    blobs = [ln.split()[0] for ln in types.splitlines() if ln.endswith(" blob")]
    head_blobs = {ln.split()[2] for ln in git("ls-tree", "-r", "HEAD").decode().splitlines()}

    # findings[kind][path] -> {"history_blobs": n, "in_HEAD": bool, "examples": masked}
    findings = defaultdict(lambda: defaultdict(lambda: {"history_blobs": 0, "in_HEAD": False, "examples": set()}))
    secret_hits = []
    for sha in blobs:
        data = git("cat-file", "blob", sha)
        hits = defaultdict(set)
        for kind, pat in PATTERNS.items():
            for m in pat.finditer(data):
                v = m.group(0).decode("utf-8", "replace").lower()
                # GitHub noreply addresses are the deliberate, privacy-safe public identity
                if kind == "email" and (v in ALLOWED_EMAILS or v.endswith((".invalid", "example.com",
                                                                           "@users.noreply.github.com"))):
                    continue
                hits[kind].add(mask(m.group(0), kind))
        if user and user.encode().lower() in data.lower():
            hits["local_username"].add("<username>")
        for kind, ex in hits.items():
            for path in paths[sha]:
                f = findings[kind][path]
                f["history_blobs"] += 1
                f["in_HEAD"] |= sha in head_blobs
                f["examples"] |= set(sorted(ex)[:3])
        if secret and secret in data:
            secret_hits.append(sorted(paths[sha]))

    meta = git("log", "--all", "--format=%an%x09%ae%x09%cn%x09%ce").decode().splitlines()
    identities = sorted({mask(x.encode(), "email") for ln in meta for x in ln.split("\t")[1::2]})
    report = {
        "generated_at": net.utc_now(),
        "scope": "every blob reachable from every local ref + commit author/committer metadata",
        "refs": git("for-each-ref", "--format=%(refname:short) %(objectname:short)").decode().split("\n")[:-1],
        "blobs_scanned": len(blobs),
        "remotes": git("remote").decode().split(),
        "project_db_password_found_in_history": bool(secret_hits),
        "project_db_password_paths": secret_hits,
        "findings": {k: {p: {"history_blobs": v["history_blobs"], "in_HEAD": v["in_HEAD"],
                             "masked_examples": sorted(v["examples"])} for p, v in sorted(by_path.items())}
                     for k, by_path in sorted(findings.items())},
        "commit_identity_emails_masked": identities,
    }
    write_json(a.out, report)
    print(json.dumps({k: report[k] for k in ("blobs_scanned", "remotes", "project_db_password_found_in_history")}))
    for k, by_path in report["findings"].items():
        for p, v in by_path.items():
            print(f"{k:18} {'HEAD' if v['in_HEAD'] else 'history-only':12} {v['history_blobs']:>2} blob(s)  {p}  "
                  f"{v['masked_examples'][:2]}")
    print("commit identities:", identities)


if __name__ == "__main__":
    main()
