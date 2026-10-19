"""DST-01 national ingestion of current DailyMed human-Rx full-release parts into PostgreSQL.

Unit of work = one archive member (a nested per-SPL ZIP). Guarantees:
* bounded memory: one member in memory at a time (hard byte caps in safezip);
* failed-document isolation: each document is stored inside its own SAVEPOINT; any
  failure becomes a dead_letter row + archive_member(status='failed') and the run continues;
* resume / idempotence: members already recorded for a source file are skipped; documents
  are unique on (set_id, version, xml_sha256), so re-processing can never duplicate rows;
* crash safety: work is committed per batch together with its archive_member rows, so a
  killed process loses at most one uncommitted batch, which is simply redone.
Nothing here resolves facility identity or infers missing facilities.
"""

from __future__ import annotations

import copy
import datetime as dt
import gc
import io
import json
import os
import platform
import subprocess
import sys
import time
import zipfile
from pathlib import Path, PurePosixPath

import psycopg
from psycopg.types.json import Jsonb

from . import bulk, config, db, download, ndc, safezip, spl

LOCK_KEY = 0x66696E65  # 'fine'
REPO = Path(__file__).resolve().parents[2]


class AlreadyRunning(RuntimeError):
    pass


def _date(yyyymmdd: str | None) -> dt.date | None:
    if not yyyymmdd or len(yyyymmdd) < 8 or not yyyymmdd[:8].isdigit():
        return None
    try:
        return dt.date(int(yyyymmdd[:4]), int(yyyymmdd[4:6]), int(yyyymmdd[6:8]))
    except ValueError:
        return None


def _mdy(s: str | None) -> dt.date | None:
    try:
        return dt.datetime.strptime(s, "%m/%d/%Y").date() if s else None
    except ValueError:
        return None


def code_version() -> tuple[str | None, bool | None]:
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True, check=True)
        return head.stdout.strip(), bool(dirty.stdout.strip())
    except Exception:
        return None, None


def start_run(conn: psycopg.Connection, args: dict) -> int:
    if not conn.execute("SELECT pg_try_advisory_lock(%s)", (LOCK_KEY,)).fetchone()[0]:
        raise AlreadyRunning("another fineprint ingest holds the advisory lock")
    with conn.transaction():
        stale = conn.execute("UPDATE national.ingest_run SET status = 'interrupted', finished_at = now() "
                             "WHERE status = 'running' RETURNING run_id").fetchall()
        commit, dirty = code_version()
        run_id = conn.execute(
            "INSERT INTO national.ingest_run (code_commit, code_dirty, python, platform, args) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING run_id",
            (commit, dirty, sys.version.split()[0], platform.platform(), Jsonb(args))).fetchone()[0]
    if stale:
        print(f"marked abandoned runs as interrupted: {[r[0] for r in stale]}", file=sys.stderr)
    return run_id


def finish_run(conn, run_id, status, stats):
    with conn.transaction():
        conn.execute("UPDATE national.ingest_run SET status = %s, finished_at = now(), stats = %s WHERE run_id = %s",
                     (status, Jsonb(stats), run_id))
    conn.execute("SELECT pg_advisory_unlock(%s)", (LOCK_KEY,))


def register_source(conn, *, kind: str, advertised: dict, record: dict, path: Path, release_label: str,
                    verify: bool = True) -> tuple[int, dict]:
    """Insert (or find) a source_file row after re-verifying the bytes on disk."""
    info = {"verified": False}
    if not path.exists():
        raise FileNotFoundError(path)
    if verify:
        t0 = time.perf_counter()
        sha, md5, n = download.hash_file(path)
        info.update(verify_seconds=round(time.perf_counter() - t0, 2), verified=True)
        problems = []
        if sha != record["sha256"]:
            problems.append("sha256 differs from download record")
        if advertised.get("advertised_md5") and md5 != advertised["advertised_md5"]:
            problems.append("md5 differs from advertised")
        if n != record["bytes"]:
            problems.append("size differs from download record")
        if problems:
            raise download.VerificationFailed(f"{path.name}: {problems}")
    try:
        rel = path.resolve().relative_to(config.data_dir()).as_posix()
    except ValueError:  # e.g. test fixtures in a temp dir
        rel = path.resolve().as_posix()
    info["local_path"] = rel  # relative to $FINEPRINT_DATA: evidence never embeds a home directory
    with conn.transaction():
        row = conn.execute(
            """INSERT INTO national.source_file (kind, source_role, name, url, release_label, advertised_md5,
                   advertised_files, advertised_size, etag, http_last_modified, content_length, bytes, sha256, md5,
                   md5_matches_advertised, retrieved_started_at, retrieved_completed_at, local_path)
               VALUES (%s, 'current', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (sha256) DO NOTHING RETURNING source_file_id""",
            (kind, advertised["name"], record["url"], release_label, advertised.get("advertised_md5"),
             advertised.get("advertised_number_of_files"), advertised.get("advertised_file_size"), record.get("etag"),
             record.get("last_modified"), record["content_length"], record["bytes"], record["sha256"], record["md5"],
             record.get("md5_matches_advertised"), record.get("first_started_at"), record["completed_at"], rel)
        ).fetchone()
        if row is None:
            row = conn.execute("SELECT source_file_id FROM national.source_file WHERE sha256 = %s",
                               (record["sha256"],)).fetchone()
            info["newly_registered"] = False
        else:
            info["newly_registered"] = True
    return row[0], info


def load_zip_metadata(conn, source_file_id: int, path: Path) -> dict:
    n_existing = conn.execute("SELECT count(*) FROM national.dailymed_zip_metadata WHERE source_file_id = %s",
                              (source_file_id,)).fetchone()[0]
    if n_existing:
        return {"rows": n_existing, "loaded_now": 0}
    bad = n = 0
    with zipfile.ZipFile(path) as zf:
        txt = [i for i in zf.infolist() if i.filename.lower().endswith("meta_data.txt")]
        if len(txt) != 1:
            raise RuntimeError(f"unexpected metadata archive layout: {[i.filename for i in zf.infolist()]}")
        # Stream line by line from the (byte-capped) member straight into COPY: bounded memory.
        with io.TextIOWrapper(safezip.open_member(zf, txt[0], 256 << 20), encoding="utf-8",
                              errors="replace", newline="") as lines:
            header = next(lines).rstrip("\r\n")
            if header.strip() != "SETID|ZIP_FILE_NAME|UPLOAD_DATE|SPL_VERSION|TITLE":
                raise RuntimeError(f"unexpected metadata header: {header!r}")
            with conn.transaction():
                with conn.cursor() as cur:
                    with cur.copy("COPY national.dailymed_zip_metadata (source_file_id, zip_file_name, set_id, "
                                  "spl_version, upload_date_raw, upload_date, title) FROM STDIN") as cp:
                        for ln in lines:
                            f = ln.rstrip("\r\n").split("|", 4)
                            if len(f) != 5:
                                bad += 1
                                continue
                            ver = int(f[3]) if f[3].strip().isdigit() else None
                            cp.write_row((source_file_id, f[1].strip(), f[0].strip(), ver, f[2].strip(),
                                          _mdy(f[2].strip()), f[4]))
                            n += 1
    return {"rows": n, "loaded_now": n, "malformed_lines": bad}


def _prepare(doc: dict) -> dict:
    """Turn a parsed SPL into row tuples (pure Python, before touching the database)."""
    anomalies = list(doc["anomalies"])
    ests = spl.establishments(doc)
    products, code_map = [], {}
    for p in doc["products"]:
        products.append(("product", None, p))
        if p["product_ndc_raw"] in code_map:
            anomalies.append({"kind": "duplicate_product_code_in_document", "code": p["product_ndc_raw"]})
        code_map.setdefault(p["product_ndc_raw"], ("product", len(products) - 1))
    for pi, p in enumerate(list(doc["products"])):
        for part in p["parts"]:
            products.append(("kit_part", pi, part))
            if part["code"] not in code_map:
                code_map[part["code"]] = ("kit_part", len(products) - 1)
    assertions, seen = [], set()
    for est in ests:
        for op in est["operations"]:
            for pc in (op["product_codes"] or [{"code": None, "code_system": None}]):
                for duns in (est["duns"] or [None]):
                    key = (op["loc"], pc["code"], duns)
                    if key in seen:
                        anomalies.append({"kind": "duplicate_operation_product_code", "loc": op["loc"]})
                        continue
                    seen.add(key)
                    if pc["code"] is None:
                        scope, target = "no_product_scope", None
                    elif pc["code"] in code_map:
                        scope, target = code_map[pc["code"]]
                    else:
                        scope, target = "unmatched_code", None
                    assertions.append((est["loc"], duns, op, pc, scope, target))
    n_packages = sum(len(p["packages"]) for p in doc["products"]) + \
        sum(len(part["packages"]) for p in doc["products"] for part in p["parts"])
    return {"ests": ests, "products": products, "assertions": assertions, "anomalies": anomalies,
            "n_packages": n_packages}


def _store_document(cur, *, source_file_id, member_name, opened, run_id) -> tuple[int, str]:
    doc = opened["doc"]
    prep = _prepare(doc)
    ver = int(doc["version"]) if doc["version"] and str(doc["version"]).isdigit() else None
    if not doc["set_id"] or ver is None:
        raise ValueError(f"missing set_id/version: {doc['set_id']!r} {doc['version']!r}")
    row = cur.execute(
        """INSERT INTO national.spl_document (set_id, version, document_id, document_type_code, document_type_name,
               effective_time_raw, effective_date, xml_sha256, xml_bytes, source_file_id, member_name, xml_member_name,
               member_name_date, has_establishment_block, n_products, n_packages, n_establishments,
               n_operation_assertions, anomalies, first_run_id)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           ON CONFLICT (set_id, version, xml_sha256) DO NOTHING RETURNING document_pk""",
        (doc["set_id"], ver, doc["document_id"], doc["document_type_code"], doc["document_type"],
         doc["effective_time"], _date(doc["effective_time"]), doc["xml_sha256"], doc["xml_bytes"], source_file_id,
         member_name, opened["xml_member"], _date(opened.get("name_date")), bool(prep["ests"]),
         len(doc["products"]), prep["n_packages"], len(prep["ests"]), len(prep["assertions"]),
         Jsonb(prep["anomalies"]), run_id)).fetchone()
    if row is None:
        pk = cur.execute("SELECT document_pk FROM national.spl_document WHERE set_id=%s AND version=%s AND xml_sha256=%s",
                         (doc["set_id"], ver, doc["xml_sha256"])).fetchone()[0]
        return pk, "duplicate"
    pk = row[0]

    org_pk = {}
    for o in doc["organizations"]:
        org_pk[o["loc"]] = cur.execute(
            """INSERT INTO national.organization_mention (document_pk, loc, role, depth, name, duns, duns_all, fei_all,
                   ids, address) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING org_pk""",
            (pk, o["loc"], o["role"], o["depth"], o["name"], o["duns"][0] if o["duns"] else None, o["duns"], o["fei"],
             Jsonb(o["ids"]), Jsonb(o["address"]) if o["address"] else None)).fetchone()[0]

    product_pks, pkg_rows = [], []
    for kind, parent_idx, p in prep["products"]:
        raw = p["product_ndc_raw"] if kind == "product" else p["code"]
        parent_pk = product_pks[parent_idx] if parent_idx is not None else None
        ppk = cur.execute(
            """INSERT INTO national.product (document_pk, parent_product_pk, kind, loc, ndc_raw, ndc_code_system,
                   ndc_pattern, ndc_product_5_4, name, generic_name, dosage_form, routes, approvals, marketing,
                   section_code) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING product_pk""",
            (pk, parent_pk, kind, p["loc"], raw, p["code_system"], ndc.pattern(raw) if raw else None,
             ndc.to_product_5_4(raw) if raw else None, p["name"], p.get("generic_name"), p["form"],
             [r["display_name"] or r["code"] for r in p.get("routes", [])], Jsonb(p.get("approvals", [])),
             Jsonb(p.get("marketing", [])), p.get("section_code"))).fetchone()[0]
        product_pks.append(ppk)
        for k in p["packages"]:
            kr = k["package_ndc_raw"]
            q = k.get("quantity") or {}
            pkg_rows.append((pk, ppk, k["loc"], k["level"], kr, ndc.pattern(kr) if kr else None,
                             ndc.to_11_digit(kr) if kr else None, k["contains"], k["form"], q.get("value"),
                             q.get("unit"), Jsonb(k["marketing"]),
                             ndc.package_belongs_to_product(kr, raw) if kr and raw else None))
    if pkg_rows:
        cur.executemany(
            """INSERT INTO national.package (document_pk, product_pk, loc, level, ndc_raw, ndc_pattern,
                   ndc_package_5_4_2, contains_ndc_raw, form, quantity_value, quantity_unit, marketing,
                   segments_match_product) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", pkg_rows)

    a_rows = []
    for est_loc, duns, op, pc, scope, target in prep["assertions"]:
        code = pc["code"]
        a_rows.append((pk, org_pk[est_loc], duns, op["code"], op["display_name"], code, pc["code_system"],
                       ndc.to_product_5_4(code) if code else None,
                       product_pks[target] if target is not None else None, scope, op["loc"],
                       Jsonb(op["qualifiers"])))
    if a_rows:
        cur.executemany(
            """INSERT INTO national.operation_assertion (document_pk, establishment_org_pk, duns, operation_code,
                   operation_name_raw, product_code_raw, product_code_system, product_code_5_4, product_pk,
                   product_scope, loc, qualifiers) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", a_rows)
    return pk, "loaded"


def _record_member(cur, source_file_id, info, index, member_sha, status, document_pk, run_id):
    cur.execute("""INSERT INTO national.archive_member (source_file_id, member_name, member_index, member_bytes,
                       member_sha256, status, document_pk, run_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (source_file_id, info.filename, index, info.file_size, member_sha, status, document_pk, run_id))


def _dead_letter(cur, run_id, source_file_id, info, member_sha, stage, error_kind, detail):
    cur.execute("""INSERT INTO national.dead_letter (run_id, source_file_id, member_name, member_sha256, stage,
                       error_kind, error_detail) VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (run_id, source_file_id, info.filename, member_sha, stage, error_kind, (detail or "")[:2000]))


def ingest_part(conn, *, source_file_id: int, path: Path, run_id: int, batch_size: int = 200,
                retry_failed: bool = False, limit: int | None = None, crash_after: int | None = None,
                limits: safezip.Limits = safezip.DEFAULT_LIMITS, memory_retries: int = 3,
                memory_backoff_s: float = 30.0, log=print) -> dict:
    t_start = time.perf_counter()
    if retry_failed:
        with conn.transaction():
            n = conn.execute("DELETE FROM national.dead_letter WHERE source_file_id = %s", (source_file_id,)).rowcount
            conn.execute("DELETE FROM national.archive_member WHERE source_file_id = %s AND status = 'failed'",
                         (source_file_id,))
        log(f"retry-failed: cleared {n} dead letters")
    done = {r[0] for r in conn.execute("SELECT member_name FROM national.archive_member WHERE source_file_id = %s",
                                       (source_file_id,))}
    st = {"members_in_archive": 0, "already_done": 0, "processed": 0, "loaded": 0, "duplicate": 0, "failed": 0,
          "failed_by_stage": {}, "failed_by_kind": {}, "member_bytes_processed": 0,
          "read_seconds": 0.0, "parse_seconds": 0.0, "db_seconds": 0.0}
    with zipfile.ZipFile(path) as zf:
        scan = safezip.scan_directory(zf, limits)
        infos = [i for i in zf.infolist() if not i.is_dir()]
        st["members_in_archive"] = len(infos)
        st["duplicate_member_names"] = len(scan["duplicate_names"])
        todo = [(idx, i) for idx, i in enumerate(infos) if i.filename not in done]
        st["already_done"] = len(infos) - len(todo)
        if limit is not None:
            todo = todo[:limit]
        for b0 in range(0, len(todo), batch_size):
            for attempt in range(1, memory_retries + 2):
                snapshot = copy.deepcopy(st)
                try:
                    _run_batch(conn, zf, todo[b0:b0 + batch_size], source_file_id, run_id, limits, st,
                               crash_after, log)
                    break
                except MemoryError:
                    # Machine-wide allocation failure (e.g. Windows commit limit), not a bad document:
                    # the batch was rolled back; restore its stats and retry, else fail the run loudly.
                    st.clear()
                    st.update(snapshot)
                    if attempt > memory_retries:
                        raise
                    st["memory_error_batch_retries"] = st.get("memory_error_batch_retries", 0) + 1
                    log(f"{path.name}: MemoryError in batch at {b0}; rolled back, retry {attempt}/{memory_retries}")
                    gc.collect()
                    time.sleep(memory_backoff_s * attempt)
            done_n = st["already_done"] + st["processed"]
            if (b0 // batch_size) % 10 == 9 or b0 + batch_size >= len(todo):
                el = time.perf_counter() - t_start
                log(f"{path.name}: {done_n}/{len(infos)} loaded={st['loaded']} dup={st['duplicate']} "
                    f"failed={st['failed']} {el:.0f}s rss={bulk.peak_rss_bytes()}")
    st["wall_seconds"] = round(time.perf_counter() - t_start, 2)
    for k in ("read_seconds", "parse_seconds", "db_seconds"):
        st[k] = round(st[k], 2)
    if st["processed"] and st["wall_seconds"]:
        st["members_per_second"] = round(st["processed"] / st["wall_seconds"], 2)
        st["member_MB_per_second"] = round(st["member_bytes_processed"] / st["wall_seconds"] / 1e6, 2)
    return st


def _run_batch(conn, zf, batch, source_file_id, run_id, limits, st, crash_after, log):
    """One committed unit: documents + their archive_member/dead_letter rows, all or nothing."""
    with conn.transaction():
        with conn.cursor() as cur:
            for idx, info in batch:
                if crash_after is not None and st["processed"] >= crash_after:
                    log(f"CRASH HOOK: hard exit with an open, uncommitted batch after {st['processed']} members")
                    sys.stdout.flush()
                    sys.stderr.flush()
                    os._exit(137)
                st["processed"] += 1
                st["member_bytes_processed"] += info.file_size
                status, stage, kind, detail, member_sha, doc_pk = _process_one(
                    conn, cur, zf, info, source_file_id, run_id, limits, st)
                if status == "failed":
                    st["failed"] += 1
                    st["failed_by_stage"][stage] = st["failed_by_stage"].get(stage, 0) + 1
                    st["failed_by_kind"][kind] = st["failed_by_kind"].get(kind, 0) + 1
                    _dead_letter(cur, run_id, source_file_id, info, member_sha, stage, kind, detail)
                else:
                    st[status] += 1
                _record_member(cur, source_file_id, info, idx, member_sha, status, doc_pk, run_id)


def _process_one(conn, cur, zf, info, source_file_id, run_id, limits, st):
    """Return (status, stage, error_kind, detail, member_sha256, document_pk)."""
    problems = safezip.member_problems(info, limits)
    if problems:
        return "failed", "outer_member", "unsafe_outer_member", ",".join(problems), None, None
    t0 = time.perf_counter()
    try:
        data = safezip.read_member(zf, info, limits.max_member_bytes)
    except (safezip.ZipSafetyError, zipfile.BadZipFile, OSError, EOFError) as e:
        st["read_seconds"] += time.perf_counter() - t0
        return "failed", "outer_member", type(e).__name__, str(e), None, None
    t1 = time.perf_counter()
    st["read_seconds"] += t1 - t0
    opened = bulk.open_nested(info.filename, data, limits)
    del data
    t2 = time.perf_counter()
    st["parse_seconds"] += t2 - t1
    if opened["status"] != "ok":
        kind = opened["failure"].split(":")[0]
        return "failed", opened["stage"], kind, opened["failure"], opened["member_sha256"], None
    try:
        with conn.transaction():  # SAVEPOINT: a bad document cannot poison its batch
            pk, status = _store_document(cur, source_file_id=source_file_id, member_name=info.filename,
                                         opened=opened, run_id=run_id)
    except MemoryError:
        raise  # resource exhaustion is not a document defect: never dead-letter it
    except Exception as e:  # isolate ANY per-document failure; kind + detail are kept in dead_letter
        st["db_seconds"] += time.perf_counter() - t2
        return "failed", "db_insert", type(e).__name__, str(e), opened["member_sha256"], None
    st["db_seconds"] += time.perf_counter() - t2
    return status, None, None, None, opened["member_sha256"], pk


def resolve_published_dates(conn) -> dict:
    """Fill published_date ONLY from official zip metadata whose set_id AND version agree."""
    with conn.transaction():
        n = conn.execute(
            """UPDATE national.spl_document d SET published_date = m.upload_date,
                   published_date_source = 'dailymed_zip_metadata:UPLOAD_DATE:' || s.sha256
               FROM national.dailymed_zip_metadata m JOIN national.source_file s USING (source_file_id)
               WHERE d.published_date IS NULL AND m.upload_date IS NOT NULL
                 AND m.zip_file_name = regexp_replace(d.member_name, '^.*/', '')
                 AND lower(m.set_id) = lower(d.set_id) AND m.spl_version = d.version""").rowcount
    row = conn.execute(
        """SELECT count(*) FILTER (WHERE published_date IS NOT NULL),
                  count(*) FILTER (WHERE published_date IS NULL),
                  count(*) FILTER (WHERE published_date IS NULL AND EXISTS (
                      SELECT 1 FROM national.dailymed_zip_metadata m
                      WHERE m.zip_file_name = regexp_replace(d.member_name, '^.*/', '')))
           FROM national.spl_document d""").fetchone()
    return {"updated_now": n, "documents_with_published_date": row[0], "documents_without_published_date": row[1],
            "without_date_but_zip_name_listed_with_mismatched_set_or_version": row[2]}


def refresh_operation_types(conn, run_id) -> list[dict]:
    with conn.transaction():
        conn.execute("DELETE FROM national.operation_type")
        conn.execute(
            """WITH raw AS (SELECT operation_code, coalesce(operation_name_raw, '') AS nm, count(*) AS c
                            FROM national.operation_assertion WHERE operation_code IS NOT NULL GROUP BY 1, 2),
                    norm AS (SELECT operation_code, upper(btrim(nm)) AS nm, sum(c) AS c FROM raw GROUP BY 1, 2),
                    best AS (SELECT DISTINCT ON (operation_code) operation_code, nm FROM norm
                             ORDER BY operation_code, c DESC, nm)
               INSERT INTO national.operation_type (operation_code, canonical_name, observed_names, assertions,
                                                    refreshed_run_id)
               SELECT r.operation_code, b.nm, jsonb_object_agg(r.nm, r.c), sum(r.c), %s
               FROM raw r JOIN best b USING (operation_code) GROUP BY r.operation_code, b.nm""", (run_id,))
    rows = conn.execute("SELECT operation_code, canonical_name, observed_names, assertions FROM national.operation_type "
                        "ORDER BY assertions DESC").fetchall()
    out = []
    for code, canon, observed, n in rows:
        distinct_norm = sorted({k.strip().upper() for k in observed})
        out.append({"code": code, "canonical_name": canon, "assertions": n, "raw_variants": len(observed),
                    "distinct_normalized_names": distinct_norm})
    return out


def release_inputs(manifest_path: Path) -> dict:
    """Read the release manifest produced by dst01_fetch_release.py."""
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = config.data_dir()
    parts = []
    for p in m["parts"]:
        rec_path = root / (p["local_path"] + ".json")
        if not rec_path.exists():
            parts.append({"advertised": p, "error": "no completed download record"})
            continue
        parts.append({"advertised": p, "record": json.loads(rec_path.read_text(encoding="utf-8")),
                      "path": root / p["local_path"]})
    meta = m.get("zip_metadata") or {}
    meta_in = None
    if meta.get("local_path"):
        mp = root / meta["local_path"]
        meta_in = {"advertised": meta["advertised"], "record": json.loads(Path(str(mp) + ".json").read_text("utf-8")),
                   "path": mp}
    return {"release_label": m["advertised_last_modified_values"][-1], "parts": parts, "zip_metadata": meta_in}


def member_basename(name: str) -> str:
    return PurePosixPath(name).name
