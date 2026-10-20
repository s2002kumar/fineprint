"""DST-02: fetch and load dated FDA establishment-registration evidence (DECRS).

* Current: drls_reg.zip and drls_excluded.zip straight from FDA (resumable, hashed).
* Archived (stale-identity evidence only): Internet Archive captures of drls_reg.zip chosen by a
  fixed rule — the latest HTTP-200 capture in each calendar year from 2024 to last year, plus the
  latest capture this year that precedes the current file. CDX SHA-1 digests are verified.

  python -I scripts/dst02_registration.py --db fineprint --out evidence/dst02/registration_manifest.json
"""

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import config, db, download, identity, net  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402

FDA = "https://www.accessdata.fda.gov/cder/{name}"
CDX = ("https://web.archive.org/cdx/search/cdx?url=accessdata.fda.gov/cder/drls_reg.zip&from=2024&to={year}"
       "&output=json&fl=timestamp,original,statuscode,digest,length&filter=statuscode:200")
RAW = "https://web.archive.org/web/{ts}id_/{original}"
ARCHIVE_RULE = ("latest HTTP-200 Internet Archive capture of drls_reg.zip in each calendar year from 2024 to "
                "last year, plus the latest capture this year that precedes the current FDA file")


def choose_captures(caps, current_generated_at):
    cutoff = current_generated_at[:10].replace("-", "")
    by_year = {}
    for c in sorted(caps, key=lambda c: c["timestamp"]):
        if c["timestamp"][:8] < cutoff:
            by_year[c["timestamp"][:4]] = c  # last one wins = latest in that year
    return [by_year[y] for y in sorted(by_year)]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    root = config.data_dir() / "raw" / "fda" / "decrs"
    conn = db.connect(a.db, autocommit=True)
    db.migrate(conn)
    out = {"generated_at": net.utc_now(), "rule": ARCHIVE_RULE, "files": []}

    def load(kind, path, record, generated_at, captured_at=None, digest=None):
        rows, member = identity.parse_decrs(path)
        sid, new = identity.register_file(conn, kind=kind, path=path, record=record,
                                          release_label=generated_at[:10], generated_at=generated_at,
                                          captured_at=captured_at, archive_digest=digest)
        n = identity.load_rows(conn, sid, rows)
        out["files"].append({"kind": kind, "source_file_id": sid, "newly_registered": new, "rows_loaded_now": n,
                             "rows": len(rows), "url": record["url"], "sha256": record["sha256"],
                             "bytes": record["bytes"], "generated_at": generated_at, "captured_at": captured_at,
                             "archive_digest_verified": digest is not None, "member": member,
                             "with_fei": sum(1 for r in rows if r["FEI_NUMBER"]),
                             "distinct_duns": len({r["DUNS_NUMBER"] for r in rows if r["DUNS_NUMBER"]})})
        print(kind, generated_at, len(rows), "rows", "new" if new else "existing", file=sys.stderr)
        return member

    current_generated = None
    for name, kind in (("drls_reg.zip", "fda_decrs_registration"), ("drls_excluded.zip", "fda_decrs_excluded")):
        existing = sorted(p for p in root.glob(f"*/{name}") if p.parent.name != "archived")
        try:
            if not existing:
                raise FileNotFoundError(name)
            dest = existing[-1]
            rec = download.download(FDA.format(name=name), dest)          # re-verify unchanged snapshot
        except (FileNotFoundError, download.VerificationFailed):
            # FDA regenerates these files; a changed file becomes a new dated snapshot.
            dest = root / net.utc_now().replace(":", "")[:15] / name
            rec = download.download(FDA.format(name=name), dest)
        member = load(kind, dest, rec, identity.parse_decrs(dest)[1]["generated_at"])
        if kind == "fda_decrs_registration":
            current_generated = member["generated_at"]

    cdx = net.fetch(CDX.format(year=current_generated[:4]))
    rows = json.loads(cdx.body.decode("utf-8"))
    caps = [dict(zip(rows[0], r)) for r in rows[1:]] if rows else []
    chosen = choose_captures(caps, current_generated)
    out["archive_captures_listed"] = len(caps)
    out["archive_captures_chosen"] = [c["timestamp"] for c in chosen]
    for c in chosen:
        dest = root / "archived" / f"drls_reg_{c['timestamp']}.zip"
        rec_path = dest.with_name(dest.name + ".json")
        if dest.exists() and rec_path.exists():
            rec = json.loads(rec_path.read_text(encoding="utf-8"))
        else:
            r = net.fetch(RAW.format(ts=c["timestamp"], original=c["original"]), dest)
            rec = {"url": r.url, "etag": None, "last_modified": None, "bytes": r.bytes, "sha256": r.sha256,
                   "md5": r.md5, "first_started_at": r.retrieved_at, "completed_at": r.retrieved_at}
            rec_path.write_text(json.dumps(rec, indent=2), encoding="utf-8", newline="\n")
        sha1 = base64.b32encode(hashlib.sha1(dest.read_bytes()).digest()).decode()
        if sha1 != c["digest"]:
            raise SystemExit(f"archive digest mismatch for {c['timestamp']}: {sha1} != {c['digest']}")
        ts = c["timestamp"]
        captured = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}T{ts[8:10]}:{ts[10:12]}:{ts[12:14]}Z"
        load("fda_decrs_registration_archived", dest, rec, identity.parse_decrs(dest)[1]["generated_at"],
             captured_at=captured, digest=c["digest"])
    write_json(a.out, out)
    conn.close()
    print(json.dumps({f["generated_at"]: f["rows"] for f in out["files"]}, indent=1))


if __name__ == "__main__":
    main()
