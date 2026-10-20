"""Dated FDA registration evidence (DECRS) for establishment identity: DUNS -> FEI -> address.

Only firm/site columns are kept. Contact names, contact emails and agent details in the
FDA files are dropped at parse time and never reach the database.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import zipfile
from pathlib import Path

from . import config, safezip

KEEP = ("FEI_NUMBER", "DUNS_NUMBER", "FIRM_NAME", "ADDRESS", "EXPIRATION_DATE", "OPERATIONS",
        "REGISTRANT_NAME", "REGISTRANT_DUNS", "EXCLUSION_FLAG")
DROPPED = ("ESTABLISHMENT_CONTACT_NAME", "ESTABLISHMENT_CONTACT_EMAIL", "AGENT_DETAILS",
           "REGISTRANT_CONTACT_NAME", "REGISTRANT_CONTACT_EMAIL")
REGISTRATION_KINDS = ("fda_decrs_registration", "fda_decrs_excluded", "fda_decrs_registration_archived")


def _mdy(s: str | None) -> dt.date | None:
    try:
        return dt.datetime.strptime(s, "%m/%d/%Y").date() if s else None
    except ValueError:
        return None


def parse_decrs(path: Path) -> tuple[list[dict], dict]:
    """Rows (KEEP columns only, stripped) and member info, from a drls_*.zip archive."""
    with zipfile.ZipFile(path) as zf:
        scan = safezip.scan_directory(zf)
        txt = [i for i in zf.infolist() if i.filename.lower().endswith(".txt")]
        if len(txt) != 1 or scan["flagged"]:
            raise RuntimeError(f"unexpected DECRS archive layout in {path.name}: {[i.filename for i in zf.infolist()]}")
        info = txt[0]
        raw = safezip.read_member(zf, info, 64 << 20)
    lines = raw.decode("latin-1").splitlines()
    hdr = [h.strip() for h in lines[0].split("\t")]
    missing = [k for k in KEEP if k not in hdr]
    if missing:
        raise RuntimeError(f"DECRS header lacks {missing}: {hdr}")
    rows = []
    for n, ln in enumerate(lines[1:], start=2):
        if not ln.strip():
            continue
        full = dict(zip(hdr, (f.strip() for f in ln.split("\t"))))
        rows.append({"line_no": n, **{k: (full.get(k) or None) for k in KEEP}})
    member = {"name": info.filename, "bytes": info.file_size, "sha256": hashlib.sha256(raw).hexdigest(),
              "generated_at": "%04d-%02d-%02dT%02d:%02d:%02d" % info.date_time}
    return rows, member


def register_file(conn, *, kind: str, path: Path, record: dict, release_label: str, generated_at: str,
                  captured_at: str | None = None, archive_digest: str | None = None) -> tuple[int, bool]:
    """Insert (or find) the source_file row for a registration file whose bytes were already verified."""
    try:
        rel = path.resolve().relative_to(config.data_dir()).as_posix()
    except ValueError:
        rel = path.resolve().as_posix()
    with conn.transaction():
        row = conn.execute(
            """INSERT INTO national.source_file (kind, source_role, name, url, release_label, etag, http_last_modified,
                   content_length, bytes, sha256, md5, retrieved_started_at, retrieved_completed_at, local_path,
                   generated_at, captured_at, archive_digest_sha1_b32)
               VALUES (%s, 'current', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (sha256) DO NOTHING RETURNING source_file_id""",
            (kind, path.name, record["url"], release_label, record.get("etag"), record.get("last_modified"),
             record["bytes"], record["bytes"], record["sha256"], record["md5"], record.get("first_started_at"),
             record["completed_at"], rel, generated_at, captured_at, archive_digest)).fetchone()
        if row:
            return row[0], True
        return conn.execute("SELECT source_file_id FROM national.source_file WHERE sha256 = %s",
                            (record["sha256"],)).fetchone()[0], False


def load_rows(conn, source_file_id: int, rows: list[dict]) -> int:
    """COPY registration rows once per source file (idempotent)."""
    if conn.execute("SELECT 1 FROM national.registration_record WHERE source_file_id = %s LIMIT 1",
                    (source_file_id,)).fetchone():
        return 0
    with conn.transaction():
        with conn.cursor() as cur:
            with cur.copy("""COPY national.registration_record (source_file_id, line_no, fei, duns, firm_name, address,
                                 expiration_date_raw, expiration_date, operations_raw, registrant_name,
                                 registrant_duns, exclusion_flag) FROM STDIN""") as cp:
                for r in rows:
                    cp.write_row((source_file_id, r["line_no"], r["FEI_NUMBER"], r["DUNS_NUMBER"], r["FIRM_NAME"],
                                  r["ADDRESS"], r["EXPIRATION_DATE"], _mdy(r["EXPIRATION_DATE"]), r["OPERATIONS"],
                                  r["REGISTRANT_NAME"], r["REGISTRANT_DUNS"], r["EXCLUSION_FLAG"]))
    return len(rows)
