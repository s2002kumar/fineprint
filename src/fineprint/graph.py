"""DST-02 projection: canonical current version per set, dated DUNS identity, operation edges.

The whole projection is rebuilt atomically in one transaction from DST-01 rows plus loaded
registration evidence, so a rebuild is idempotent and readers never see a half-built graph.

Confidence of an operation edge (product -> operation -> DUNS -> facility):
  DIRECT     explicit operation, product-scoped, DUNS on the CURRENT registration file with an
             FEI and a future expiration date, no FEI change across snapshots, and a canonical
             version that is not ambiguous.
  TENTATIVE  explicit and product-scoped, but identity is partial (no FEI, excluded, stale,
             ambiguous, FEI changed, expired) or the version selection is ambiguous.
  UNKNOWN    the DUNS has no registration evidence at all, the SPL gave no DUNS, or the
             operation is not attributable to a product.
"""

from __future__ import annotations

from collections import defaultdict

RULE_VERSION = "dst02-v1"
MANUFACTURE = "C43360"

CONFIRMED = {"SINGLE_VERSION_METADATA_CONFIRMED": "confirmed", "MULTI_VERSION_METADATA_SELECTED": "confirmed",
             "SINGLE_VERSION_NOT_IN_METADATA": "unconfirmed", "SINGLE_VERSION_METADATA_LISTS_OTHER": "ambiguous",
             "MULTI_VERSION_HIGHEST_NO_METADATA": "ambiguous",
             "MULTI_VERSION_HIGHEST_METADATA_LISTS_OTHER": "ambiguous",
             "UNRESOLVED_SAME_VERSION_CONFLICT": "unresolved"}


def select_version(docs: list[tuple[int, int, str]], metadata_version: int | None) -> dict:
    """Pure rule. docs = [(document_pk, version, xml_sha256)] for one set."""
    versions = sorted({v for _, v, _ in docs})
    if metadata_version is not None and metadata_version in versions:
        target = metadata_version
        status = "SINGLE_VERSION_METADATA_CONFIRMED" if len(versions) == 1 else "MULTI_VERSION_METADATA_SELECTED"
    elif len(versions) == 1:
        target = versions[0]
        status = "SINGLE_VERSION_NOT_IN_METADATA" if metadata_version is None else "SINGLE_VERSION_METADATA_LISTS_OTHER"
    else:
        target = versions[-1]
        status = ("MULTI_VERSION_HIGHEST_NO_METADATA" if metadata_version is None
                  else "MULTI_VERSION_HIGHEST_METADATA_LISTS_OTHER")
    at_target = sorted({(pk, sha) for pk, v, sha in docs if v == target}, key=lambda x: x[1])
    if len({sha for _, sha in at_target}) > 1:
        return {"document_pk": None, "selected_version": target, "versions": versions,
                "status": "UNRESOLVED_SAME_VERSION_CONFLICT", "class": "unresolved"}
    return {"document_pk": at_target[0][0], "selected_version": target, "versions": versions,
            "status": status, "class": CONFIRMED[status]}


def resolve_duns(duns: str, snapshots: list[dict], rows_by_duns: dict) -> dict:
    """Pure rule. snapshots: [{source_file_id, kind, as_of}] newest first per kind.

    rows_by_duns[duns][source_file_id] -> list of registration rows.
    """
    mine = rows_by_duns.get(duns, {})
    current = next((s for s in snapshots if s["kind"] == "fda_decrs_registration"), None)
    excluded = next((s for s in snapshots if s["kind"] == "fda_decrs_excluded"), None)
    history = []
    for s in sorted(snapshots, key=lambda s: (s["as_of"], s["source_file_id"])):
        for r in mine.get(s["source_file_id"], []):
            history.append({"as_of": s["as_of"].isoformat(), "kind": s["kind"], "fei": r["fei"],
                            "address": r["address"]})
    feis = {h["fei"] for h in history if h["fei"]}
    out = {"duns": duns, "fei_history": history, "fei_changed": len(feis) > 1, "row": None, "snapshot": None}

    def use(status, s, rows):
        out.update(status=status, snapshot=s, row=rows[0], fei=rows[0]["fei"])
        return out

    if current and mine.get(current["source_file_id"]):
        rows = mine[current["source_file_id"]]
        if len({r["fei"] for r in rows if r["fei"]}) > 1:
            out.update(status="AMBIGUOUS_MULTIPLE_FEI", snapshot=current, row=rows[0], fei=None)
            return out
        return use("CURRENT_REGISTERED" if rows[0]["fei"] else "CURRENT_REGISTERED_NO_FEI", current, rows)
    if excluded and mine.get(excluded["source_file_id"]):
        return use("CURRENT_EXCLUDED", excluded, mine[excluded["source_file_id"]])
    for s in snapshots:  # newest archived snapshot that lists this DUNS
        if s["kind"] == "fda_decrs_registration_archived" and mine.get(s["source_file_id"]):
            return use("STALE_REGISTERED", s, mine[s["source_file_id"]])
    out.update(status="NOT_FOUND", fei=None)
    return out


def edge_confidence(*, duns, identity_status, expired, fei_changed, scope, selection_class) -> tuple[str, list[str]]:
    """Pure rule shared by the SQL build and the tests."""
    reasons = []
    if duns is None:
        return "UNKNOWN", ["spl:no_duns"]
    if scope in ("no_product_scope", "unmatched_code"):
        return "UNKNOWN", [f"scope:{scope}"]
    if identity_status == "NOT_FOUND":
        return "UNKNOWN", ["identity:NOT_FOUND"]
    if identity_status != "CURRENT_REGISTERED":
        reasons.append(f"identity:{identity_status}")
    if expired:
        reasons.append("identity:registration_expired")
    if fei_changed:
        reasons.append("identity:fei_changed_across_snapshots")
    if selection_class == "ambiguous":
        reasons.append("version_selection:ambiguous")
    return ("TENTATIVE", reasons) if reasons else ("DIRECT", [])


def build(conn, *, log=print) -> dict:
    """Rebuild the projection atomically. Returns the build summary."""
    from psycopg.types.json import Jsonb  # DB-only imports stay local so the pure rules need no driver

    from . import ingest
    commit, dirty = ingest.code_version()
    with conn.transaction():
        build_id = conn.execute("INSERT INTO national.graph_build (rule_version, code_commit, code_dirty) "
                                "VALUES (%s, %s, %s) RETURNING build_id", (RULE_VERSION, commit, dirty)).fetchone()[0]
        for t in ("operation_edge", "facility", "duns_identity", "set_version_selection"):
            conn.execute(f"DELETE FROM national.{t}")

        # 1. version selection ---------------------------------------------------------------
        meta_sid = conn.execute("SELECT max(source_file_id) FROM national.source_file "
                                "WHERE kind = 'dailymed_zip_metadata'").fetchone()[0]
        meta = {k: (v, d) for k, v, d in conn.execute(
            """SELECT lower(m.set_id), m.spl_version, m.upload_date FROM national.dailymed_zip_metadata m
               WHERE m.source_file_id = %s AND lower(m.set_id) IN (SELECT lower(set_id) FROM national.spl_document)""",
            (meta_sid,))}
        sets = defaultdict(list)
        names = {}
        pub = {}
        for pk, set_id, version, sha, pdate in conn.execute(
                "SELECT document_pk, set_id, version, xml_sha256, published_date FROM national.spl_document"):
            key = set_id.lower()
            sets[key].append((pk, version, sha))
            names.setdefault(key, set_id)
            pub[pk] = pdate
        sel_rows = []
        for key in sorted(sets):
            mv, md = meta.get(key, (None, None))
            r = select_version(sets[key], mv)
            sel_rows.append((key, names[key], r["document_pk"], r["selected_version"], r["versions"], len(sets[key]),
                             mv, md, r["status"], r["class"], pub.get(r["document_pk"]), build_id))
        with conn.cursor() as cur:
            with cur.copy("""COPY national.set_version_selection (set_key, set_id, document_pk, selected_version,
                                 versions_in_release, n_documents, metadata_version, metadata_upload_date,
                                 selection_status, selection_class, published_date, build_id) FROM STDIN""") as cp:
                for row in sel_rows:
                    cp.write_row(row)
        log(f"version selection: {len(sel_rows)} sets")

        # 2. identity -----------------------------------------------------------------------
        snaps = [{"source_file_id": s, "kind": k, "as_of": g.date()} for s, k, g in conn.execute(
            """SELECT source_file_id, kind, generated_at FROM national.source_file
               WHERE kind IN ('fda_decrs_registration', 'fda_decrs_excluded', 'fda_decrs_registration_archived')
               ORDER BY generated_at DESC, source_file_id DESC""")]
        if not any(s["kind"] == "fda_decrs_registration" for s in snaps):
            raise RuntimeError("no current registration file loaded; run scripts/dst02_registration.py first")
        duns_needed = [r[0] for r in conn.execute(
            """SELECT DISTINCT a.duns FROM national.operation_assertion a
               JOIN national.set_version_selection s ON s.document_pk = a.document_pk WHERE a.duns IS NOT NULL""")]
        rows_by_duns = defaultdict(lambda: defaultdict(list))
        for pk, sid, fei, duns, firm, addr, exp in conn.execute(
                """SELECT registration_pk, source_file_id, fei, duns, firm_name, address, expiration_date
                   FROM national.registration_record WHERE duns = ANY(%s) ORDER BY registration_pk""", (duns_needed,)):
            rows_by_duns[duns][sid].append({"pk": pk, "fei": fei, "firm": firm, "address": addr, "expiration": exp})
        share = {(sid, fei): n for sid, fei, n in conn.execute(
            """SELECT source_file_id, fei, count(DISTINCT duns) FROM national.registration_record
               WHERE fei IS NOT NULL GROUP BY 1, 2""")}
        spl_names = defaultdict(set)
        for duns, name in conn.execute(
                """SELECT DISTINCT o.duns, o.name FROM national.organization_mention o
                   JOIN national.set_version_selection s ON s.document_pk = o.document_pk
                   WHERE o.role = 'establishment' AND o.duns IS NOT NULL AND o.name IS NOT NULL"""):
            spl_names[duns].add(name)
        id_rows = []
        for duns in sorted(duns_needed):
            r = resolve_duns(duns, snaps, rows_by_duns)
            row, snap = r["row"], r["snapshot"]
            id_rows.append((duns, r["status"], r["fei"], row["pk"] if row else None,
                            snap["source_file_id"] if snap else None, snap["as_of"] if snap else None,
                            row["expiration"] if row else None, row["firm"] if row else None,
                            row["address"] if row else None, Jsonb(r["fei_history"]), r["fei_changed"],
                            share.get((snap["source_file_id"], r["fei"])) if (snap and r["fei"]) else None,
                            sorted(spl_names.get(duns, ())), build_id))
        with conn.cursor() as cur:
            with cur.copy("""COPY national.duns_identity (duns, status, fei, registration_pk, evidence_source_file_id,
                                 evidence_as_of, evidence_expiration, firm_name, address, fei_history, fei_changed,
                                 duns_sharing_fei, spl_names, build_id) FROM STDIN""") as cp:
                for row in id_rows:
                    cp.write_row(row)
        log(f"identity: {len(id_rows)} DUNS")

        # 3. facilities (one per FEI with any registration evidence) --------------------------
        conn.execute(
            """INSERT INTO national.facility (fei, duns, firm_names, addresses, current_registered, build_id)
               SELECT fei, array_agg(DISTINCT duns ORDER BY duns), array_agg(DISTINCT firm_name ORDER BY firm_name)
                          FILTER (WHERE firm_name IS NOT NULL),
                      array_agg(DISTINCT address ORDER BY address) FILTER (WHERE address IS NOT NULL),
                      bool_or(status = 'CURRENT_REGISTERED'), %s
               FROM national.duns_identity WHERE fei IS NOT NULL GROUP BY fei""", (build_id,))

        # 4. edges (SQL mirrors edge_confidence) ------------------------------------------------
        conn.execute(
            """INSERT INTO national.operation_edge (assertion_pk, document_pk, set_id, version, selection_class,
                   product_pk, report_product_pk, product_scope, product_ndc_raw, product_ndc_5_4, operation_code,
                   operation_name, is_manufacture, duns, identity_status, fei, confidence, confidence_reasons, loc,
                   build_id)
               SELECT a.assertion_pk, a.document_pk, s.set_id, s.selected_version, s.selection_class, a.product_pk,
                      coalesce(p.parent_product_pk, a.product_pk), a.product_scope, a.product_code_raw,
                      a.product_code_5_4, a.operation_code, coalesce(t.canonical_name, upper(btrim(a.operation_name_raw))),
                      a.operation_code = %(mfg)s, a.duns, coalesce(i.status, 'NO_DUNS_IN_SPL'), i.fei,
                      x.confidence, x.reasons, a.loc, %(build)s
               FROM national.operation_assertion a
               JOIN national.set_version_selection s ON s.document_pk = a.document_pk
               LEFT JOIN national.product p ON p.product_pk = a.product_pk
               LEFT JOIN national.operation_type t ON t.operation_code = a.operation_code
               LEFT JOIN national.duns_identity i ON i.duns = a.duns
               CROSS JOIN LATERAL (
                 SELECT CASE
                   WHEN a.duns IS NULL THEN 'UNKNOWN'
                   WHEN a.product_scope IN ('no_product_scope', 'unmatched_code') THEN 'UNKNOWN'
                   WHEN i.status = 'NOT_FOUND' THEN 'UNKNOWN'
                   WHEN cardinality(r.reasons) = 0 THEN 'DIRECT'
                   ELSE 'TENTATIVE' END AS confidence,
                   CASE
                     WHEN a.duns IS NULL THEN ARRAY['spl:no_duns']
                     WHEN a.product_scope IN ('no_product_scope', 'unmatched_code') THEN ARRAY['scope:' || a.product_scope]
                     WHEN i.status = 'NOT_FOUND' THEN ARRAY['identity:NOT_FOUND']
                     ELSE r.reasons END AS reasons
                 FROM (SELECT array_remove(ARRAY[
                         CASE WHEN i.status <> 'CURRENT_REGISTERED' THEN 'identity:' || i.status END,
                         CASE WHEN i.evidence_expiration < i.evidence_as_of THEN 'identity:registration_expired' END,
                         CASE WHEN i.fei_changed THEN 'identity:fei_changed_across_snapshots' END,
                         CASE WHEN s.selection_class = 'ambiguous' THEN 'version_selection:ambiguous' END
                       ], NULL) AS reasons) r
               ) x""", {"mfg": MANUFACTURE, "build": build_id})
        outputs = summary(conn)
        outputs["fingerprint"] = fingerprint(conn)
        conn.execute("UPDATE national.graph_build SET status = 'completed', finished_at = now(), outputs = %s, "
                     "inputs = %s WHERE build_id = %s",
                     (Jsonb(outputs), Jsonb(inputs(conn)), build_id))
    return {"build_id": build_id, **outputs}


def inputs(conn) -> dict:
    files = conn.execute("SELECT kind, name, sha256, generated_at::text FROM national.source_file ORDER BY 1, 2, 3")
    return {"source_files": [list(r) for r in files.fetchall()]}


FINGERPRINT_SQL = {
    "set_version_selection": """SELECT s.set_key || '|' || coalesce(s.selected_version::text, '') || '|' ||
        s.selection_status || '|' || coalesce(d.xml_sha256, '') FROM national.set_version_selection s
        LEFT JOIN national.spl_document d USING (document_pk)""",
    "duns_identity": """SELECT i.duns || '|' || i.status || '|' || coalesce(i.fei, '') || '|' ||
        coalesce(f.sha256, '') || '|' || coalesce(i.evidence_as_of::text, '') || '|' || i.fei_changed
        FROM national.duns_identity i LEFT JOIN national.source_file f ON f.source_file_id = i.evidence_source_file_id""",
    "facility": "SELECT fei || '|' || array_to_string(duns, ',') FROM national.facility",
    "operation_edge": """SELECT d.set_id || '|' || d.version || '|' || d.xml_sha256 || '|' || e.loc || '|' ||
        coalesce(e.product_ndc_raw, '') || '|' || coalesce(e.duns, '') || '|' || e.operation_code || '|' ||
        e.confidence || '|' || array_to_string(e.confidence_reasons, ',')
        FROM national.operation_edge e JOIN national.spl_document d USING (document_pk)""",
}


def fingerprint(conn) -> dict:
    out = {}
    for t, sql in FINGERPRINT_SQL.items():
        n, h = conn.execute(f"SELECT count(*), md5(coalesce(string_agg(k, E'\\n' ORDER BY k COLLATE \"C\"), '')) "
                            f"FROM ({sql}) t(k)").fetchone()
        out[t] = {"rows": n, "md5": h}
    return out


def summary(conn) -> dict:
    q = lambda sql: [list(r) for r in conn.execute(sql).fetchall()]  # noqa: E731
    return {
        "selection_status": dict(q("SELECT selection_status, count(*) FROM national.set_version_selection GROUP BY 1")),
        "selection_class": dict(q("SELECT selection_class, count(*) FROM national.set_version_selection GROUP BY 1")),
        "identity_status": dict(q("SELECT status, count(*) FROM national.duns_identity GROUP BY 1")),
        "facilities": q("SELECT count(*), count(*) FILTER (WHERE current_registered) FROM national.facility")[0],
        "edges_by_confidence": dict(q("SELECT confidence, count(*) FROM national.operation_edge GROUP BY 1")),
        "manufacture_edges_by_confidence": dict(q(
            "SELECT confidence, count(*) FROM national.operation_edge WHERE is_manufacture GROUP BY 1")),
    }
