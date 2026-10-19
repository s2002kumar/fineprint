"""PostgreSQL connection, immutable migrations, and content fingerprints."""

from __future__ import annotations

import hashlib
from pathlib import Path

import psycopg

from . import config

MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations"


def connect(dbname: str = config.DEFAULT_DB, **kw) -> psycopg.Connection:
    return psycopg.connect(config.dsn(dbname), **kw)


def migrate(conn: psycopg.Connection, directory: Path = MIGRATIONS) -> list[str]:
    """Apply migrations in filename order. An applied file whose bytes changed is an error."""
    conn.execute("CREATE TABLE IF NOT EXISTS public.fineprint_migration "
                 "(version text PRIMARY KEY, sha256 text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())")
    applied = dict(conn.execute("SELECT version, sha256 FROM public.fineprint_migration").fetchall())
    done = []
    for f in sorted(directory.glob("*.sql")):
        body = f.read_bytes()
        sha = hashlib.sha256(body).hexdigest()
        if f.name in applied:
            if applied[f.name] != sha:
                raise RuntimeError(f"migration {f.name} changed after being applied; add a new migration instead")
            continue
        with conn.transaction():
            conn.execute(body.decode("utf-8"))
            conn.execute("INSERT INTO public.fineprint_migration (version, sha256) VALUES (%s, %s)", (f.name, sha))
        done.append(f.name)
    conn.commit()
    return done


def reset_national(conn: psycopg.Connection) -> None:
    """Drop the national schema and all migration records (tests / clean rebuilds only).

    Every migration so far targets the national schema; revisit when another schema exists.
    """
    conn.execute("DROP SCHEMA IF EXISTS national CASCADE")
    if conn.execute("SELECT to_regclass('public.fineprint_migration')").fetchone()[0]:
        conn.execute("DELETE FROM public.fineprint_migration")
    conn.commit()


DOC_KEY = "d.set_id || '|' || d.version || '|' || d.xml_sha256"

# Natural-key fingerprints: independent of surrogate ids, so two databases built from the
# same sources (in any order, with any crashes) must produce identical values.
FINGERPRINT_SQL = {
    "spl_document": f"""SELECT {DOC_KEY} || '|' || coalesce(d.published_date::text,'') || '|' ||
        coalesce(d.effective_time_raw,'') || '|' || d.has_establishment_block || '|' || d.n_products || '|' ||
        d.n_packages || '|' || d.n_establishments || '|' || d.n_operation_assertions FROM national.spl_document d""",
    "organization_mention": f"""SELECT {DOC_KEY} || '|' || o.loc || '|' || o.role || '|' || coalesce(o.duns,'')
        FROM national.organization_mention o JOIN national.spl_document d USING (document_pk)""",
    "product": f"""SELECT {DOC_KEY} || '|' || p.loc || '|' || p.kind || '|' || coalesce(p.ndc_raw,'') || '|' ||
        coalesce(p.ndc_product_5_4,'') FROM national.product p JOIN national.spl_document d USING (document_pk)""",
    "package": f"""SELECT {DOC_KEY} || '|' || k.loc || '|' || coalesce(k.ndc_raw,'') || '|' ||
        coalesce(k.ndc_package_5_4_2,'') || '|' || k.level || '|' || coalesce(k.contains_ndc_raw,'')
        FROM national.package k JOIN national.spl_document d USING (document_pk)""",
    "operation_assertion": f"""SELECT {DOC_KEY} || '|' || a.loc || '|' || coalesce(a.product_code_raw,'') || '|' ||
        coalesce(a.duns,'') || '|' || coalesce(a.operation_code,'') || '|' || a.product_scope
        FROM national.operation_assertion a JOIN national.spl_document d USING (document_pk)""",
    "archive_member": """SELECT s.sha256 || '|' || m.member_name || '|' || m.status || '|' || coalesce(m.member_sha256,'')
        FROM national.archive_member m JOIN national.source_file s USING (source_file_id)""",
    "dead_letter": """SELECT s.sha256 || '|' || x.member_name || '|' || x.stage || '|' || x.error_kind
        FROM national.dead_letter x JOIN national.source_file s USING (source_file_id)""",
}


def fingerprint(conn: psycopg.Connection) -> dict:
    out = {}
    for table, sql in FINGERPRINT_SQL.items():
        n, digest = conn.execute(
            f"SELECT count(*), md5(coalesce(string_agg(k, E'\\n' ORDER BY k COLLATE \"C\"), '')) FROM ({sql}) t(k)"
        ).fetchone()
        out[table] = {"rows": n, "md5": digest}
    return out


def table_counts(conn: psycopg.Connection) -> dict:
    tables = ["source_file", "ingest_run", "dailymed_zip_metadata", "spl_document", "archive_member", "dead_letter",
              "organization_mention", "product", "package", "operation_assertion", "operation_type"]
    return {t: conn.execute(f"SELECT count(*) FROM national.{t}").fetchone()[0] for t in tables}
