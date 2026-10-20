"""fineprint CLI: explainable queries over the CURRENT national provenance graph.

Every answer is scoped to the loaded DailyMed release and the dated FDA registration file;
none of it is a reconstruction of any historical state. DIRECT / TENTATIVE / UNKNOWN are
always reported separately, and every relationship carries an evidence id that
`fineprint evidence <id>` resolves to its exact source location.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

from . import config, db, ndc, safezip

MFG = "C43360"
UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
NAME_WARNING = ("Name matches are listed one product at a time. A shared name does NOT mean the same product, "
                "labeler or manufacturing site.")


class UserError(Exception):
    pass


def scope(conn) -> dict:
    rel = conn.execute("SELECT max(release_label), count(*) FROM national.source_file "
                       "WHERE kind = 'dailymed_human_rx_full_part'").fetchone()
    reg = conn.execute("SELECT max(generated_at)::date FROM national.source_file "
                       "WHERE kind = 'fda_decrs_registration'").fetchone()[0]
    build = conn.execute("SELECT max(build_id) FROM national.graph_build WHERE status = 'completed'").fetchone()[0]
    return {"dailymed_release": rel[0], "release_parts": rel[1], "registration_as_of": str(reg) if reg else None,
            "graph_build": build,
            "note": "Current release only; not a historical state. Labeler != facility; PACK/LABEL != MANUFACTURE."}


def _rows(conn, sql, params=()):
    cur = conn.execute(sql, params)
    cols = [d.name for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


EDGE_SELECT = """
SELECT e.assertion_pk AS evidence_id, e.confidence, e.confidence_reasons AS reasons, e.operation_name AS operation,
       e.duns, e.fei, e.identity_status, i.evidence_as_of AS identity_as_of, i.firm_name, i.address,
       e.set_id, e.version, s.published_date, e.product_scope, e.product_ndc_raw AS operation_product_code,
       rp.product_pk, rp.ndc_raw AS product_ndc, rp.ndc_product_5_4, rp.name AS product_name, rp.dosage_form
FROM national.operation_edge e
JOIN national.set_version_selection s ON s.document_pk = e.document_pk
LEFT JOIN national.product rp ON rp.product_pk = e.report_product_pk
LEFT JOIN national.duns_identity i ON i.duns = e.duns
"""


def _group(edges):
    out = {"DIRECT": [], "TENTATIVE": [], "UNKNOWN": []}
    for e in edges:
        out[e["confidence"]].append(e)
    return out


def cmd_facility(conn, a):
    key = a.id.strip()
    if key.upper().startswith("FEI:"):
        fei = key[4:]
        fac = _rows(conn, "SELECT * FROM national.facility WHERE fei = %s", (fei,))
        if not fac:
            raise UserError(f"FEI {fei} has no registration evidence linked to any establishment DUNS")
        duns_list = fac[0]["duns"]
    else:
        if not key.isdigit():
            raise UserError("give a 9-digit DUNS or FEI:<number>")
        fac, duns_list = None, [key]
    ident = _rows(conn, "SELECT duns, status, fei, evidence_as_of, evidence_expiration, firm_name, address, "
                        "fei_changed, duns_sharing_fei, spl_names FROM national.duns_identity WHERE duns = ANY(%s) "
                        "ORDER BY duns", (duns_list,))
    labeler_docs = conn.execute(
        """SELECT count(DISTINCT o.document_pk) FROM national.organization_mention o
           JOIN national.set_version_selection s ON s.document_pk = o.document_pk
           WHERE o.role = 'labeler' AND o.duns = ANY(%s)""", (duns_list,)).fetchone()[0]
    op_filter = "" if a.operation == "all" else " AND e.is_manufacture"
    edges = _rows(conn, EDGE_SELECT + " WHERE e.duns = ANY(%s)" + op_filter +
                  " ORDER BY e.confidence, rp.ndc_product_5_4 NULLS LAST, e.set_id, e.assertion_pk", (duns_list,))
    other = _rows(conn, """SELECT operation_name AS operation, confidence, count(*) AS edges,
                                  count(DISTINCT report_product_pk) AS products
                           FROM national.operation_edge WHERE duns = ANY(%s) AND NOT is_manufacture
                           GROUP BY 1, 2 ORDER BY 1, 2""", (duns_list,))
    return {"query": {"facility": key, "duns": duns_list, "operation": a.operation}, "facility": fac[0] if fac else None,
            "identity": ident, "documents_where_this_duns_is_the_labeler": labeler_docs,
            "products_by_confidence": _dedupe_products(_group(edges)),
            "other_operations_summary": other}


def _dedupe_products(groups):
    out = {}
    for conf, edges in groups.items():
        seen, items = set(), []
        for e in edges:
            k = (e["product_pk"], e["duns"], e["operation"])
            if k in seen:
                continue
            seen.add(k)
            items.append(e)
        out[conf] = items
    return out


def _resolve_product_query(conn, q):
    q = q.strip()
    if UUID.match(q):
        return _rows(conn, """SELECT p.product_pk FROM national.set_version_selection s
                              JOIN national.product p ON p.document_pk = s.document_pk AND p.kind = 'product'
                              WHERE s.set_key = lower(%s) ORDER BY p.ndc_raw, p.product_pk""", (q,)), "set_id"
    segs = q.split("-")
    if len(segs) == 3:
        n11 = ndc.to_11_digit(q)
        if n11 is None:
            raise UserError(f"package NDC {q!r} has no explicit segment pattern; refusing to guess")
        return _rows(conn, """SELECT DISTINCT p.product_pk FROM national.package k
                              JOIN national.set_version_selection s ON s.document_pk = k.document_pk
                              JOIN national.product p ON p.product_pk = k.product_pk
                              WHERE k.ndc_package_5_4_2 = %s ORDER BY 1""", (n11,)), f"package {n11}"
    if len(segs) == 2:
        n9 = ndc.to_product_5_4(q)
        if n9 is None:
            raise UserError(f"product NDC {q!r} has no explicit segment pattern; refusing to guess")
        return _rows(conn, """SELECT p.product_pk FROM national.product p
                              JOIN national.set_version_selection s ON s.document_pk = p.document_pk
                              WHERE p.ndc_product_5_4 = %s AND p.kind = 'product' ORDER BY 1""", (n9,)), f"product {n9}"
    raise UserError("give a hyphenated product NDC (e.g. 0409-3308), package NDC (e.g. 00409-3308-03) or a set ID; "
                    "unhyphenated NDCs are ambiguous and are not guessed")


def cmd_product(conn, a):
    pks, matched_as = _resolve_product_query(conn, a.ndc)
    products = []
    for (pk,) in [(r["product_pk"],) for r in pks]:
        p = _rows(conn, """SELECT p.product_pk, p.ndc_raw, p.ndc_product_5_4, p.name, p.generic_name, p.dosage_form,
                                  p.routes, s.set_id, s.selected_version AS version, s.selection_status,
                                  s.selection_class, s.published_date, s.versions_in_release, v.evidence_status,
                                  (SELECT array_agg(DISTINCT o.name) FROM national.organization_mention o
                                   WHERE o.document_pk = p.document_pk AND o.role = 'labeler') AS labeler_names
                           FROM national.product p
                           JOIN national.set_version_selection s ON s.document_pk = p.document_pk
                           JOIN national.v_product_establishment_evidence v ON v.product_pk = p.product_pk
                           WHERE p.product_pk = %s""", (pk,))[0]
        edges = _rows(conn, EDGE_SELECT + " WHERE e.report_product_pk = %s ORDER BY e.is_manufacture DESC, "
                                          "e.confidence, e.duns, e.assertion_pk", (pk,))
        mfg = [e for e in edges if e["operation"] == "MANUFACTURE"]
        p["manufacturing_sites"] = _dedupe_products(_group(mfg))
        p["other_operations"] = [{k: e[k] for k in ("evidence_id", "operation", "duns", "fei", "confidence")}
                                 for e in edges if e["operation"] != "MANUFACTURE"]
        unscoped = conn.execute("""SELECT count(*) FROM national.operation_edge e
                                   JOIN national.product p ON p.document_pk = e.document_pk
                                   WHERE p.product_pk = %s AND e.product_scope = 'no_product_scope'""",
                                (pk,)).fetchone()[0]
        p["document_level_unscoped_operations"] = unscoped
        if not mfg:
            p["why_no_site"] = {"NO_ESTABLISHMENT_BLOCK": "label lists no establishments at all",
                                "OTHER_OPERATIONS_ONLY": "establishments listed, but none with MANUFACTURE for it",
                                "ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT": "operations exist but are not tied to any product",
                                "ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT":
                                    "establishments listed for other products only"}.get(p["evidence_status"],
                                                                                         p["evidence_status"])
        products.append(p)
    return {"query": {"ndc_or_set": a.ndc, "matched_as": matched_as}, "products": products}


def cmd_labeler(conn, a):
    rows = _rows(conn, """
        SELECT coalesce(e.duns, '-') AS duns, coalesce(i.status, 'NO_MANUFACTURE_EVIDENCE') AS identity_status,
               e.fei, i.firm_name, i.address, e.confidence, count(DISTINCT p.product_pk) AS products
        FROM national.set_version_selection s
        JOIN national.organization_mention l ON l.document_pk = s.document_pk AND l.role = 'labeler' AND l.duns = %s
        JOIN national.product p ON p.document_pk = s.document_pk AND p.kind = 'product'
        LEFT JOIN national.operation_edge e ON e.report_product_pk = p.product_pk AND e.is_manufacture
        LEFT JOIN national.duns_identity i ON i.duns = e.duns
        GROUP BY 1, 2, 3, 4, 5, 6 ORDER BY products DESC, 1""", (a.duns,))
    total = conn.execute("""SELECT count(DISTINCT p.product_pk), count(DISTINCT s.set_key)
                            FROM national.set_version_selection s
                            JOIN national.organization_mention l ON l.document_pk = s.document_pk
                                 AND l.role = 'labeler' AND l.duns = %s
                            JOIN national.product p ON p.document_pk = s.document_pk AND p.kind = 'product'""",
                         (a.duns,)).fetchone()
    return {"query": {"labeler_duns": a.duns}, "labeler_products": total[0], "labeler_sets": total[1],
            "note": "A product made at several sites is counted under each site.", "by_manufacturing_site": rows}


def cmd_compare(conn, a):
    lab = ""
    params = [a.duns_a, a.duns_b]
    if a.labeler:
        lab = (" AND EXISTS (SELECT 1 FROM national.organization_mention l WHERE l.document_pk = e.document_pk "
               "AND l.role = 'labeler' AND l.duns = %s)")
    rows = _rows(conn, f"""
        SELECT rp.product_pk, rp.ndc_product_5_4, rp.name, e.set_id,
               array_agg(DISTINCT e.duns ORDER BY e.duns) AS sites,
               array_agg(DISTINCT e.confidence ORDER BY e.confidence) AS confidences
        FROM national.operation_edge e JOIN national.product rp ON rp.product_pk = e.report_product_pk
        WHERE e.is_manufacture AND e.duns IN (%s, %s){lab}
        GROUP BY 1, 2, 3, 4 ORDER BY 2 NULLS LAST, 4""", params + ([a.labeler] if a.labeler else []))
    only_a = [r for r in rows if r["sites"] == [a.duns_a]]
    only_b = [r for r in rows if r["sites"] == [a.duns_b]]
    both = [r for r in rows if len(r["sites"]) == 2]
    return {"query": {"site_a": a.duns_a, "site_b": a.duns_b, "labeler": a.labeler},
            "counts": {"only_a": len(only_a), "only_b": len(only_b), "both": len(both)},
            "only_a": only_a[: a.limit], "only_b": only_b[: a.limit], "both": both[: a.limit]}


def cmd_search(conn, a):
    rows = _rows(conn, """
        SELECT m.product_pk, m.ndc_raw, m.ndc_product_5_4, m.name, m.set_id, m.version, m.manufacturing_status,
               m.manufacture_duns, m.evidence_status,
               (SELECT array_agg(DISTINCT o.name) FROM national.organization_mention o
                JOIN national.product p ON p.document_pk = o.document_pk
                WHERE p.product_pk = m.product_pk AND o.role = 'labeler') AS labeler_names
        FROM national.v_product_manufacturing_status m
        WHERE m.name ILIKE %s ORDER BY m.ndc_product_5_4 NULLS LAST, m.set_id LIMIT %s""",
                 (f"%{a.text}%", a.limit))
    return {"query": {"name_contains": a.text}, "warning": NAME_WARNING, "products": rows}


def cmd_evidence(conn, a):
    r = _rows(conn, """
        SELECT a.assertion_pk AS evidence_id, d.set_id, d.version, d.document_id, d.document_type_name,
               d.effective_time_raw, s.published_date, s.selection_status, d.xml_sha256, d.xml_member_name,
               m.member_name, m.member_sha256, f.name AS source_part, f.sha256 AS source_sha256,
               f.retrieved_completed_at, f.local_path, f.release_label, a.loc, a.operation_code,
               a.operation_name_raw, a.product_code_raw, a.product_scope, a.duns, o.name AS establishment_name_in_spl,
               e.confidence, e.confidence_reasons, e.identity_status, e.fei,
               i.evidence_as_of AS identity_as_of, rf.name AS identity_source, rf.sha256 AS identity_source_sha256,
               rf.generated_at AS identity_generated_at, rf.captured_at AS identity_captured_at,
               rr.line_no AS identity_line, i.firm_name AS identity_firm_name, i.address AS identity_address
        FROM national.operation_assertion a
        JOIN national.spl_document d USING (document_pk)
        JOIN national.archive_member m ON m.document_pk = d.document_pk AND m.status = 'loaded'
        JOIN national.source_file f ON f.source_file_id = m.source_file_id
        JOIN national.organization_mention o ON o.org_pk = a.establishment_org_pk
        LEFT JOIN national.set_version_selection s ON s.document_pk = d.document_pk
        LEFT JOIN national.operation_edge e ON e.assertion_pk = a.assertion_pk
        LEFT JOIN national.duns_identity i ON i.duns = a.duns
        LEFT JOIN national.registration_record rr ON rr.registration_pk = i.registration_pk
        LEFT JOIN national.source_file rf ON rf.source_file_id = i.evidence_source_file_id
        WHERE a.assertion_pk = %s""", (a.id,))
    if not r:
        raise UserError(f"no operation assertion with evidence id {a.id}")
    ev = r[0]
    ev["in_current_graph"] = ev["confidence"] is not None
    if a.raw:
        ev["raw_xml"] = raw_excerpt(ev)
    return {"query": {"evidence_id": a.id}, "evidence": ev}


def raw_excerpt(ev: dict) -> str:
    """Re-open the original archive, verify hashes, and return the cited XML element verbatim."""
    path = config.data_dir() / ev["local_path"]
    with zipfile.ZipFile(path) as outer:
        data = safezip.read_member(outer, outer.getinfo(ev["member_name"]), safezip.DEFAULT_LIMITS.max_member_bytes)
    import hashlib
    if hashlib.sha256(data).hexdigest() != ev["member_sha256"]:
        raise UserError("archive member hash differs from the ingested record")
    with zipfile.ZipFile(io.BytesIO(data)) as inner:
        xml = inner.read(ev["xml_member_name"])
    if hashlib.sha256(xml).hexdigest() != ev["xml_sha256"]:
        raise UserError("XML hash differs from the ingested record")
    root = ET.fromstring(xml)
    steps = ev["loc"].strip("/").split("/")[1:]
    el = root.find("./" + "/".join("{urn:hl7-org:v3}" + s for s in steps))
    if el is None:
        raise UserError(f"citation {ev['loc']} does not resolve in the source XML")
    ET.register_namespace("", "urn:hl7-org:v3")
    return re.sub(r"\n\s*\n", "\n", ET.tostring(el, encoding="unicode"))


def cmd_coverage(conn, a):
    q = lambda sql: _rows(conn, sql)  # noqa: E731
    docs = q("""SELECT (SELECT count(*) FROM national.spl_document) AS documents_in_release,
                       count(*) AS sets, count(document_pk) AS canonical_documents,
                       count(*) FILTER (WHERE selection_class = 'confirmed') AS confirmed,
                       count(*) FILTER (WHERE selection_class = 'unconfirmed') AS unconfirmed,
                       count(*) FILTER (WHERE selection_class = 'ambiguous') AS ambiguous,
                       count(*) FILTER (WHERE selection_class = 'unresolved') AS unresolved
                FROM national.set_version_selection""")[0]
    prod = q("""SELECT manufacturing_status, count(*) AS products FROM national.v_product_manufacturing_status
                GROUP BY 1 ORDER BY 2 DESC""")
    no_evidence = q("""SELECT evidence_status, count(*) AS products FROM national.v_product_manufacturing_status
                       WHERE manufacturing_status = 'NO_MANUFACTURE_EVIDENCE' GROUP BY 1 ORDER BY 2 DESC""")
    sets_direct = q("""SELECT count(DISTINCT set_id) FILTER (WHERE confidence = 'DIRECT') AS sets_with_direct_manufacture,
                              count(DISTINCT set_id) AS sets_with_any_manufacture_edge
                       FROM national.operation_edge WHERE is_manufacture""")[0]
    duns = q("""SELECT i.status, count(DISTINCT i.duns) AS duns,
                       count(DISTINCT i.duns) FILTER (WHERE EXISTS (SELECT 1 FROM national.operation_edge e
                             WHERE e.duns = i.duns AND e.is_manufacture)) AS manufacture_duns
                FROM national.duns_identity i GROUP BY 1 ORDER BY 2 DESC""")
    fac = q("""SELECT count(*) AS facilities, count(*) FILTER (WHERE current_registered) AS currently_registered,
                      count(*) FILTER (WHERE cardinality(duns) > 1) AS shared_by_multiple_duns
               FROM national.facility""")[0]
    edges = q("""SELECT operation_name, confidence, count(*) AS edges FROM national.operation_edge
                 WHERE is_manufacture GROUP BY 1, 2 ORDER BY 1, 2""")
    return {"documents_and_sets": docs, "products_by_manufacturing_status": prod,
            "products_without_manufacture_evidence_by_reason": no_evidence, "sets": sets_direct,
            "establishment_duns_by_identity_status": duns, "facilities": fac, "manufacture_edges": edges}


def cmd_unresolved(conn, a):
    rows = _rows(conn, """
        SELECT i.duns, i.status, i.fei, i.evidence_as_of, i.spl_names,
               count(DISTINCT e.report_product_pk) FILTER (WHERE e.is_manufacture) AS manufacture_products,
               count(*) AS edges
        FROM national.duns_identity i LEFT JOIN national.operation_edge e ON e.duns = i.duns
        WHERE i.status <> 'CURRENT_REGISTERED' OR i.fei_changed
        GROUP BY 1, 2, 3, 4, 5 ORDER BY manufacture_products DESC, edges DESC, 1 LIMIT %s""", (a.limit,))
    by_status = _rows(conn, "SELECT status, count(*) AS duns FROM national.duns_identity "
                            "WHERE status <> 'CURRENT_REGISTERED' GROUP BY 1 ORDER BY 2 DESC")
    return {"by_status": by_status, "top_unresolved_or_partial": rows,
            "note": "NOT_FOUND = no registration evidence in any loaded snapshot; STALE = listed only in an older "
                    "snapshot; no identity is inferred from names or addresses."}


def _site(e):
    ident = f"FEI {e['fei']}" if e.get("fei") else e.get("identity_status", "")
    where = f" — {e['firm_name']}, {e['address']}" if e.get("firm_name") else ""
    why = f"  ({'; '.join(e['reasons'])})" if e.get("reasons") else ""
    return f"{e['duns'] or '(no DUNS)'}  {ident}{where}{why}  [evidence {e['evidence_id']}]"


def _prod(e):
    return (f"{e.get('ndc_product_5_4') or e.get('product_ndc') or '(unscoped)'}  {e.get('product_name') or ''}  "
            f"set {e['set_id']} v{e['version']}  [evidence {e['evidence_id']}]")


def render(cmd, res):
    s = res["scope"]
    out = [f"SCOPE: DailyMed release {s['dailymed_release']} ({s['release_parts']} parts) | FDA registration as of "
           f"{s['registration_as_of']} | graph build {s['graph_build']} — current state only, not historical"]
    if cmd == "product":
        if not res["products"]:
            out.append(f"No product in the current release matches {res['query']['ndc_or_set']} "
                       f"({res['query']['matched_as']}).")
        for p in res["products"]:
            out.append(f"\n{p['ndc_product_5_4']}  {p['name']}  {p['dosage_form'] or ''}  "
                       f"[labeler: {', '.join(p['labeler_names'] or ['?'])} — a labeler is not a facility]")
            out.append(f"  set {p['set_id']} v{p['version']}  published {p['published_date'] or 'unknown'}  "
                       f"version selection: {p['selection_class']} ({p['selection_status']}); "
                       f"versions in release {p['versions_in_release']}")
            for conf in ("DIRECT", "TENTATIVE", "UNKNOWN"):
                sites = p["manufacturing_sites"][conf]
                out.append(f"  MANUFACTURE {conf}: " + ("none" if not sites else ""))
                out += [f"    {_site(e)}" for e in sites]
            if p.get("why_no_site"):
                out.append(f"  no manufacturing site: {p['why_no_site']} [{p['evidence_status']}]")
            if p["other_operations"]:
                out.append("  other operations (not manufacture): " + "; ".join(
                    f"{o['operation']} {o['duns']} {o['confidence']} [{o['evidence_id']}]" for o in p["other_operations"]))
            if p["document_level_unscoped_operations"]:
                out.append(f"  + {p['document_level_unscoped_operations']} operation(s) in this label are not tied "
                           "to any product")
    elif cmd == "facility":
        for i in res["identity"] or [{"duns": d, "status": "NOT_AN_ESTABLISHMENT_IN_CURRENT_LABELS"}
                                     for d in res["query"]["duns"]]:
            out.append(f"\nDUNS {i['duns']}: {i['status']}" + (f", FEI {i['fei']}, {i['firm_name']}, {i['address']} "
                                                               f"(registration file {i['evidence_as_of']}, expires "
                                                               f"{i['evidence_expiration']})" if i.get("fei") else ""))
        if res["documents_where_this_duns_is_the_labeler"]:
            out.append(f"  also LABELER on {res['documents_where_this_duns_is_the_labeler']} current labels "
                       "(company role; not counted as manufacturing)")
        for conf in ("DIRECT", "TENTATIVE", "UNKNOWN"):
            items = res["products_by_confidence"][conf]
            out.append(f"  {res['query']['operation']} {conf}: {len(items)} product edge(s)")
            out += [f"    {_prod(e)}" + (f"  ({'; '.join(e['reasons'])})" if e["reasons"] else "") for e in items]
        if res["other_operations_summary"]:
            out.append("  other operations: " + "; ".join(
                f"{o['operation']} {o['confidence']} {o['products']} products" for o in res["other_operations_summary"]))
    elif cmd == "labeler":
        out.append(f"\nLabeler DUNS {res['query']['labeler_duns']}: {res['labeler_products']} products in "
                   f"{res['labeler_sets']} current sets. {res['note']}")
        for r in res["by_manufacturing_site"]:
            where = f"FEI {r['fei']} {r['firm_name']}, {r['address']}" if r["fei"] else r["identity_status"]
            out.append(f"  {r['products']:>5}  {r['confidence'] or '-':9}  {r['duns']:9}  {where}")
    elif cmd == "compare":
        q = res["query"]
        out.append(f"\nMANUFACTURE at {q['site_a']} vs {q['site_b']}" + (f" (labeler {q['labeler']})" if q["labeler"]
                                                                         else "") + f": {res['counts']}")
        for k in ("only_a", "only_b", "both"):
            out.append(f"  {k}:")
            out += [f"    {r['ndc_product_5_4']}  {r['name']}  set {r['set_id']}  {r['confidences']}" for r in res[k]]
    elif cmd == "search":
        out.append(f"\n{res['warning']}")
        out += [f"  {r['ndc_product_5_4'] or r['ndc_raw']}  {r['name']}  [{', '.join(r['labeler_names'] or [])}]  "
                f"set {r['set_id']}  manufacturing: {r['manufacturing_status']} ({r['manufacture_duns']} DUNS)"
                for r in res["products"]]
    elif cmd == "evidence":
        e = res["evidence"]
        out.append("")
        out += [f"  {k}: {v}" for k, v in e.items() if k != "raw_xml"]
        if e.get("raw_xml"):
            out.append("  raw XML (re-read from the archive; member and XML SHA-256 verified):")
            out += ["    " + ln for ln in e["raw_xml"].splitlines()]
    elif cmd == "coverage":
        d = res["documents_and_sets"]
        out.append(f"\nDocuments in release {d['documents_in_release']} | sets {d['sets']} | canonical documents "
                   f"{d['canonical_documents']} (confirmed {d['confirmed']}, unconfirmed {d['unconfirmed']}, "
                   f"ambiguous {d['ambiguous']}, unresolved {d['unresolved']})")
        total = sum(r["products"] for r in res["products_by_manufacturing_status"])
        out.append(f"Products in canonical documents: {total}")
        for r in res["products_by_manufacturing_status"]:
            out.append(f"  {r['manufacturing_status']:26} {r['products']:>7}  {100 * r['products'] / max(total, 1):5.1f}%")
        for r in res["products_without_manufacture_evidence_by_reason"]:
            out.append(f"    no evidence: {r['evidence_status']:40} {r['products']:>7}")
        st = res["sets"]
        out.append(f"Sets with a DIRECT manufacture edge: {st['sets_with_direct_manufacture']} of {d['sets']}; "
                   f"with any manufacture edge: {st['sets_with_any_manufacture_edge']}")
        mduns = sum(r["manufacture_duns"] for r in res["establishment_duns_by_identity_status"])
        out.append(f"Manufacturing DUNS by identity status (of {mduns}):")
        for r in res["establishment_duns_by_identity_status"]:
            out.append(f"  {r['status']:28} {r['manufacture_duns']:>6}  {100 * r['manufacture_duns'] / max(mduns, 1):5.1f}%"
                       f"   (all establishment DUNS: {r['duns']})")
        f = res["facilities"]
        out.append(f"Facilities (FEI): {f['facilities']}, currently registered {f['currently_registered']}, "
                   f"shared by >1 DUNS {f['shared_by_multiple_duns']}")
        out.append("MANUFACTURE edges: " + ", ".join(f"{r['confidence']} {r['edges']}" for r in res["manufacture_edges"]))
    elif cmd == "unresolved":
        out.append("\n" + ", ".join(f"{r['status']} {r['duns']}" for r in res["by_status"]))
        out.append(res["note"])
        for r in res["top_unresolved_or_partial"]:
            names = r["spl_names"][:3] + (["…"] if len(r["spl_names"]) > 3 else [])
            out.append(f"  {r['duns']}  {r['status']:26} {r['manufacture_products']:>4} products  "
                       f"{('FEI ' + r['fei'] + ' as of ' + str(r['evidence_as_of'])) if r['fei'] else ''}  "
                       f"SPL names: {'; '.join(names)}")
    else:
        out.append(json.dumps({k: v for k, v in res.items() if k != "scope"}, indent=1, default=str))
    out.append(f"\n({res['elapsed_ms']} ms)")
    return "\n".join(out)


def build_parser():
    ap = argparse.ArgumentParser(prog="fineprint", description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=config.DEFAULT_DB)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--timing", action="store_true", help="print query wall time to stderr")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("facility", help="products with operations at a DUNS or FEI:<n>")
    s.add_argument("id")
    s.add_argument("--operation", choices=["MANUFACTURE", "all"], default="MANUFACTURE")
    s.set_defaults(fn=cmd_facility)
    s = sub.add_parser("product", help="manufacturing sites for a product NDC, package NDC or set ID")
    s.add_argument("ndc")
    s.set_defaults(fn=cmd_product)
    s = sub.add_parser("labeler", help="a labeler's products grouped by manufacturing site")
    s.add_argument("duns")
    s.set_defaults(fn=cmd_labeler)
    s = sub.add_parser("compare", help="products made at site A vs site B")
    s.add_argument("duns_a")
    s.add_argument("duns_b")
    s.add_argument("--labeler")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(fn=cmd_compare)
    s = sub.add_parser("search", help="products by name (never merged)")
    s.add_argument("text")
    s.add_argument("--limit", type=int, default=50)
    s.set_defaults(fn=cmd_search)
    s = sub.add_parser("evidence", help="exact source reference for an evidence id")
    s.add_argument("id", type=int)
    s.add_argument("--raw", action="store_true", help="re-open the archive and print the cited XML")
    s.set_defaults(fn=cmd_evidence)
    s = sub.add_parser("coverage", help="national coverage summary")
    s.set_defaults(fn=cmd_coverage)
    s = sub.add_parser("unresolved", help="unresolved, stale and partial identities")
    s.add_argument("--limit", type=int, default=25)
    s.set_defaults(fn=cmd_unresolved)
    return ap


def run(argv=None, conn=None) -> dict:
    a = build_parser().parse_args(argv)
    own = conn is None
    conn = conn or db.connect(a.db)
    try:
        t0 = time.perf_counter()
        result = {"scope": scope(conn), **a.fn(conn, a)}
        result["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return result
    finally:
        if own:
            conn.close()


def main(argv=None):
    a = build_parser().parse_args(argv)
    try:
        res = run(argv)
    except UserError as e:
        print(f"fineprint: {e}", file=sys.stderr)
        return 2
    if a.timing:
        print(f"[{a.cmd}] {res['elapsed_ms']} ms", file=sys.stderr)
    if a.json:
        print(json.dumps(res, indent=1, default=str))
    else:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(render(a.cmd, res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
