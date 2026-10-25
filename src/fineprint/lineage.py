"""Research prototype (DST-08): source-NDC references and source-linked manufacturing evidence.

Not wired into ingest, the CLI, the explorer export or the historical evaluation. It reads the canonical documents of
the current graph and writes only the ``lineage`` schema of a scratch database; it never modifies a ``national`` row.

Three relationships are kept distinct:

DIRECT_MANUFACTURE
    ``national.operation_edge`` with ``confidence = 'DIRECT'``, unchanged: a product-scoped MANUFACTURE assertion in
    the product's own canonical label by a currently registered establishment.
SOURCE_NDC_REFERENCE (``lineage.source_reference``)
    A repackaged or relabeled product's own label cites the NDC product code of the finished drug the registrant
    received (21 CFR 207.53(b)). SPL encodes it as ``asEquivalentEntity`` with class EQUIV, equivalence code C64637
    ("Same", NCI Thesaurus) and the source NDC *product* code in ``definingMaterialKind`` (SPL Implementation Guide v1,
    3.1.2 and 3.2.2). It is the registrant's listing assertion, not a manufacturing statement, and it names no version.
SOURCE_LINKED_MANUFACTURING_EVIDENCE (``lineage.source_linked_evidence``)
    A traceable path from such a product, through one validated source reference that resolves to exactly one
    canonical source product, to that source product's own DIRECT_MANUFACTURE edge. It is upstream evidence about the
    cited source product as currently listed. It is never a manufacturing assertion for the repackaged product or
    package, and it does not say which site made any particular lot.

Every rule is exact: NDC codes are normalised only through ``fineprint.ndc`` (a package code is never truncated to a
product code), candidates are matched on the normalised product code only, and nothing is inferred from names,
companies, addresses or product similarity. The dosage form and active ingredients are compared only to reject a
reference whose cited source contradicts it (the Implementation Guide requires them to be the same).
"""

from __future__ import annotations

import hashlib
import io
import json
import time
import xml.etree.ElementTree as ET
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fineprint import config, ndc, safezip

RULE_VERSION = "dst08-lineage-v1"
HL7 = "{urn:hl7-org:v3}"
NDC_SYSTEM = "2.16.840.1.113883.6.69"
NCI_SYSTEM = "2.16.840.1.113883.3.26.1.1"
SAME = "C64637"
MANUFACTURE, REPACK, RELABEL = "C43360", "C73606", "C73607"
SCHEMA_SQL = Path(__file__).resolve().parents[2] / "scripts" / "research" / "dst08_lineage.sql"

VALIDITY = ("VALID", "NOT_EQUIV_CLASS", "NOT_SAME_EQUIVALENCE", "NOT_NDC_CODE_SYSTEM", "PACKAGE_CODE_NOT_PRODUCT_CODE",
            "MALFORMED_OR_MISSING_CODE", "SELF_REFERENCE", "MULTIPLE_SOURCES_FOR_PRODUCT")


class LineageRefused(Exception):
    """The build was asked to run somewhere it must not (the production database)."""


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def code_pattern(code: str | None) -> str:
    if not code:
        return "missing"
    if not ndc.is_well_formed(code):
        return "malformed"
    return "package" if ndc.pattern(code) in ndc.PACKAGE_PATTERNS else "product"


def reference_validity(*, class_code, eq_code, eq_system, src_code, src_system, own_code, n_on_product) -> str:
    """The Implementation Guide form of a source reference, checked in a fixed order; VALID or the first departure."""
    if class_code not in (None, "EQUIV"):
        return "NOT_EQUIV_CLASS"
    if eq_code != SAME or eq_system != NCI_SYSTEM:
        return "NOT_SAME_EQUIVALENCE"
    if src_system != NDC_SYSTEM:
        return "NOT_NDC_CODE_SYSTEM"
    pat = code_pattern(src_code)
    if pat == "package":
        return "PACKAGE_CODE_NOT_PRODUCT_CODE"
    if pat != "product":
        return "MALFORMED_OR_MISSING_CODE"
    if own_code and ndc.is_well_formed(own_code) and ndc.to_product_5_4(own_code) == ndc.to_product_5_4(src_code):
        return "SELF_REFERENCE"
    if n_on_product > 1:
        return "MULTIPLE_SOURCES_FOR_PRODUCT"
    return "VALID"


def eligibility(*, validity, product_kind, resolution, selection_class, chain, consistency, source_repackaged,
                source_has_direct) -> tuple[str, list[str]]:
    """Whether a reference may carry SOURCE_LINKED_MANUFACTURING_EVIDENCE, with every reason it may not.

    The SQL in ``resolve`` implements the same rule; a test proves they agree."""
    reasons = []
    if validity != "VALID":
        reasons.append(f"validity:{validity}")
    if product_kind != "product":
        reasons.append("citing:kit_part")
    if resolution != "RESOLVED":
        reasons.append(f"resolution:{resolution}")
    else:
        if selection_class not in ("confirmed", "unconfirmed"):
            reasons.append(f"source_version:{selection_class}")
        if chain != "SINGLE_HOP":
            reasons.append(f"chain:{chain}")
        if source_repackaged:
            reasons.append("source:repackaged_or_relabeled")
        if consistency != "CONSISTENT":
            reasons.append(f"consistency:{consistency}")
        if not source_has_direct:
            reasons.append("source:no_direct_manufacture")
    return ("ELIGIBLE" if not reasons else "EXCLUDED"), reasons


def _ingredients(holder) -> list[list[str]]:
    out = []
    for ing in holder.findall(HL7 + "ingredient"):
        if (ing.get("classCode") or "").startswith("ACT"):
            out.append(_ingredient(ing, ing.find(HL7 + "ingredientSubstance")))
    for ing in holder.findall(HL7 + "activeIngredient"):
        out.append(_ingredient(ing, ing.find(HL7 + "activeIngredientSubstance")))
    return sorted(out)


def decimal_text(s: str) -> str:
    """The exact decimal value of a strength in one canonical spelling ('.25' and '0.250' are '0.25', '1.0' is '1').

    Only the spelling changes, never the value: 7.70 mg per 100 mL still differs from 7.7 mg per 1 mL. Anything that is
    not a finite decimal is kept verbatim."""
    try:
        d = Decimal(s)
    except InvalidOperation:
        return s
    return format(d.normalize(), "f") if d.is_finite() else s


def _ingredient(ing, sub) -> list[str]:
    code = sub.find(HL7 + "code") if sub is not None else None
    q = ing.find(HL7 + "quantity")
    num = q.find(HL7 + "numerator") if q is not None else None
    den = q.find(HL7 + "denominator") if q is not None else None
    g = lambda e, a: (e.get(a) if e is not None else None) or ""  # noqa: E731
    return [g(code, "code"), decimal_text(g(num, "value")), g(num, "unit"), decimal_text(g(den, "value")), g(den, "unit")]


def _equivalents(holder, holder_loc: str) -> list[dict]:
    refs, n = [], 0
    for child in holder:
        if _local(child.tag) != "asEquivalentEntity":
            continue
        n += 1
        code = child.find(HL7 + "code")
        dmk = child.find(HL7 + "definingMaterialKind")
        dcode = dmk.find(HL7 + "code") if dmk is not None else None
        refs.append({"loc": f"{holder_loc}/asEquivalentEntity[{n}]", "class_code": child.get("classCode"),
                     "eq_code": code.get("code") if code is not None else None,
                     "eq_system": code.get("codeSystem") if code is not None else None,
                     "src_code": dcode.get("code") if dcode is not None else None,
                     "src_system": dcode.get("codeSystem") if dcode is not None else None})
    return refs


def _attrs(inner, loc: str, kind: str) -> dict:
    code = inner.find(HL7 + "code")
    form = inner.find(HL7 + "formCode")
    return {"loc": loc, "kind": kind, "code": code.get("code") if code is not None else None,
            "form": form.get("code") if form is not None else None, "active": _ingredients(inner),
            "refs": _equivalents(inner, loc)}


def extract(xml: bytes) -> list[dict]:
    """Products and kit parts of one SPL document with their source references, dosage form and active ingredients.

    Locations follow the parser's convention exactly (``spl.parse_spl``): every step indexed among its siblings of the
    same tag, a product at ``.../subject[n]/manufacturedProduct/<inner>`` for any subject whose parent is a section,
    and a kit part at ``<product>/part[n]/<partProduct|partMedicine>``, so each row maps to one ``national.product``."""
    if b"<!DOCTYPE" in xml[:65536] or b"<!ENTITY" in xml[:65536]:
        raise ValueError("refusing XML with DTD/entity declarations")
    root = ET.fromstring(xml)
    found: list[dict] = []

    def walk(elem, path: str):
        counts: dict[str, int] = {}
        for child in elem:
            tag = _local(child.tag)
            counts[tag] = counts.get(tag, 0) + 1
            cpath = f"{path}/{tag}[{counts[tag]}]"
            if tag == "subject" and _local(elem.tag) == "section":
                outer = child.find(HL7 + "manufacturedProduct")
                if outer is not None:
                    inner_tag = next((n for n in ("manufacturedProduct", "manufacturedMedicine")
                                      if outer.find(HL7 + n) is not None), None)
                    if inner_tag is not None:
                        inner = outer.find(HL7 + inner_tag)
                        ploc = f"{cpath}/manufacturedProduct/{inner_tag}"
                        found.append(_attrs(inner, ploc, "product"))
                        pc: dict[str, int] = {}
                        for part in inner:
                            pt = _local(part.tag)
                            pc[pt] = pc.get(pt, 0) + 1
                            if pt != "part":
                                continue
                            pp_tag = next((n for n in ("partProduct", "partMedicine") if part.find(HL7 + n) is not None), None)
                            if pp_tag is not None:
                                found.append(_attrs(part.find(HL7 + pp_tag), f"{ploc}/part[{pc[pt]}]/{pp_tag}", "kit_part"))
            walk(child, cpath)

    walk(root, "/document")
    return found


def _require_scratch(conn) -> str:
    name = conn.execute("SELECT current_database()").fetchone()[0]
    if name == config.DEFAULT_DB or not (name.startswith("fineprint_dst08") or name.endswith("_test")):
        raise LineageRefused(f"the lineage prototype writes only to a scratch database, not {name!r}")
    return name


def _read_xml(data_dir: Path, local_path: str, member: str, member_sha: str, xml_member: str, xml_sha: str,
              outer: zipfile.ZipFile | None = None) -> bytes:
    """One document's XML, hash-verified against the ingested record. Pass ``outer`` (the open release part) when
    reading many documents: opening a multi-gigabyte part re-reads its whole central directory."""
    if outer is None:
        with zipfile.ZipFile(data_dir / local_path) as part:
            return _read_xml(data_dir, local_path, member, member_sha, xml_member, xml_sha, part)
    data = safezip.read_member(outer, outer.getinfo(member), safezip.DEFAULT_LIMITS.max_member_bytes)
    if hashlib.sha256(data).hexdigest() != member_sha:
        raise ValueError(f"member hash differs from the ingested record: {member}")
    with zipfile.ZipFile(io.BytesIO(data)) as inner:
        xml = inner.read(xml_member)
    if hashlib.sha256(xml).hexdigest() != xml_sha:
        raise ValueError(f"XML hash differs from the ingested record: {xml_member}")
    return xml


def build(conn, *, data_dir: Path | None = None, code_commit: str | None = None, code_dirty: bool | None = None,
          log=print) -> dict:
    """(Re)build the lineage schema over the canonical documents of the latest completed graph build."""
    _require_scratch(conn)
    data_dir = data_dir or config.data_dir()
    t0 = time.time()
    with conn.transaction():
        conn.execute("DROP SCHEMA IF EXISTS lineage CASCADE")
        conn.execute(SCHEMA_SQL.read_text(encoding="utf-8"))
        graph_build = conn.execute("SELECT build_id FROM national.graph_build WHERE status = 'completed' "
                                   "ORDER BY build_id DESC LIMIT 1").fetchone()[0]
        build_id = conn.execute(
            "INSERT INTO lineage.build (rule_version, graph_build_id, code_commit, code_dirty) VALUES (%s, %s, %s, %s) "
            "RETURNING build_id", (RULE_VERSION, graph_build, code_commit, code_dirty)).fetchone()[0]
        docs = conn.execute(
            """SELECT d.document_pk, f.local_path, d.member_name, m.member_sha256, d.xml_member_name, d.xml_sha256
               FROM national.set_version_selection s
               JOIN national.spl_document d ON d.document_pk = s.document_pk
               JOIN national.archive_member m ON m.document_pk = d.document_pk AND m.status = 'loaded'
               JOIN national.source_file f ON f.source_file_id = m.source_file_id
               ORDER BY f.local_path, d.member_name""").fetchall()
        product_pk = {(r[0], r[1]): (r[2], r[3], r[4]) for r in conn.execute(
            "SELECT p.document_pk, p.loc, p.product_pk, p.kind, p.ndc_raw FROM national.product p "
            "JOIN national.set_version_selection s ON s.document_pk = p.document_pk").fetchall()}
        attrs_rows, ref_rows, unmapped = [], [], 0
        part, part_path = None, None
        for i, (doc_pk, local_path, member, msha, xml_member, xsha) in enumerate(docs, 1):
            if local_path != part_path:            # documents are ordered by part: open each part once
                if part is not None:
                    part.close()
                part, part_path = zipfile.ZipFile(data_dir / local_path), local_path
            for p in extract(_read_xml(data_dir, local_path, member, msha, xml_member, xsha, part)):
                hit = product_pk.get((doc_pk, p["loc"]))
                if hit is None:
                    unmapped += 1
                    continue
                pk, kind, own = hit
                attrs_rows.append((pk, p["form"], json.dumps(p["active"]), build_id))
                for r in p["refs"]:
                    v = reference_validity(class_code=r["class_code"], eq_code=r["eq_code"], eq_system=r["eq_system"],
                                           src_code=r["src_code"], src_system=r["src_system"], own_code=own,
                                           n_on_product=len(p["refs"]))
                    pat = code_pattern(r["src_code"])
                    n54 = ndc.to_product_5_4(r["src_code"]) if pat == "product" and r["src_system"] == NDC_SYSTEM else None
                    ref_rows.append((build_id, doc_pk, pk, kind, own, ndc.to_product_5_4(own) if own and ndc.is_well_formed(own) else None,
                                     r["loc"], r["class_code"], r["eq_code"], r["eq_system"], r["src_code"], r["src_system"],
                                     pat, n54, v))
            if i % 5000 == 0:
                log(f"lineage: {i}/{len(docs)} documents read")
        if part is not None:
            part.close()
        if unmapped:
            raise ValueError(f"{unmapped} extracted products have no national.product row at the same location")
        with conn.cursor() as cur:
            cur.executemany("INSERT INTO lineage.product_attributes (product_pk, form_code, active, build_id) "
                            "VALUES (%s, %s, %s::jsonb, %s)", attrs_rows)
            cur.executemany(
                """INSERT INTO lineage.source_reference (build_id, document_pk, product_pk, product_kind, product_ndc_raw,
                       product_ndc_5_4, loc, class_code, equivalence_code, equivalence_code_system, source_code_raw,
                       source_code_system, source_code_pattern, source_ndc_5_4, validity)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", ref_rows)
        resolve(conn, build_id)
        outputs = summary(conn)
        outputs["seconds"] = round(time.time() - t0, 1)
        outputs["fingerprint"] = fingerprint(conn)
        conn.execute("UPDATE lineage.build SET finished_at = now(), status = 'completed', outputs = %s WHERE build_id = %s",
                     (json.dumps(outputs), build_id))
    log(f"lineage: build {build_id} completed in {outputs['seconds']}s")
    return outputs


RESOLVE_SQL = """
-- Candidates: canonical TOP-LEVEL products in OTHER sets with exactly the normalised source product code.
INSERT INTO lineage.source_resolution (reference_pk, resolution, n_candidates, candidate_product_pks)
SELECT r.reference_pk,
       CASE WHEN r.validity <> 'VALID' THEN 'NOT_RESOLVED_INVALID'
            WHEN c.n = 1 THEN 'RESOLVED'
            WHEN c.n > 1 THEN 'MULTIPLE_CANDIDATES'
            WHEN EXISTS (SELECT 1 FROM national.product p JOIN national.set_version_selection s ON s.document_pk = p.document_pk
                         JOIN national.spl_document d ON d.document_pk = r.document_pk
                         WHERE p.ndc_product_5_4 = r.source_ndc_5_4 AND p.kind = 'product' AND lower(s.set_id) = lower(d.set_id))
                 THEN 'ONLY_SAME_SET'
            WHEN EXISTS (SELECT 1 FROM national.product p JOIN national.set_version_selection s ON s.document_pk = p.document_pk
                         WHERE p.ndc_product_5_4 = r.source_ndc_5_4 AND p.kind = 'kit_part') THEN 'ONLY_KIT_PART'
            WHEN EXISTS (SELECT 1 FROM national.product p WHERE p.ndc_product_5_4 = r.source_ndc_5_4
                         AND NOT EXISTS (SELECT 1 FROM national.set_version_selection s WHERE s.document_pk = p.document_pk))
                 THEN 'ONLY_NON_CANONICAL_VERSION'
            ELSE 'NO_CANDIDATE' END,
       coalesce(c.n, 0), coalesce(c.pks, '{}')
FROM lineage.source_reference r
JOIN national.spl_document rd ON rd.document_pk = r.document_pk
LEFT JOIN LATERAL (
    SELECT count(*)::int AS n, array_agg(p.product_pk ORDER BY p.product_pk) AS pks
    FROM national.product p JOIN national.set_version_selection s ON s.document_pk = p.document_pk
    WHERE r.validity = 'VALID' AND p.ndc_product_5_4 = r.source_ndc_5_4 AND p.kind = 'product'
      AND lower(s.set_id) <> lower(rd.set_id)) c ON true;

UPDATE lineage.source_resolution x SET source_product_pk = x.candidate_product_pks[1],
       source_document_pk = p.document_pk, source_set_id = s.set_id, source_version = s.selected_version,
       source_selection_class = s.selection_class
FROM national.product p JOIN national.set_version_selection s ON s.document_pk = p.document_pk
WHERE x.resolution = 'RESOLVED' AND p.product_pk = x.candidate_product_pks[1];

-- The source product itself cites a source (any reference, valid or not): a repackaged or relabeled source.
UPDATE lineage.source_resolution x SET source_cites_source =
       EXISTS (SELECT 1 FROM lineage.source_reference q WHERE q.product_pk = x.source_product_pk)
WHERE x.resolution = 'RESOLVED';

-- Chains through unique resolutions; a product met twice is a cycle.
WITH RECURSIVE walk AS (
    SELECT x.reference_pk AS start_pk, x.source_product_pk AS at_pk, 1 AS depth,
           ARRAY[r.product_pk, x.source_product_pk] AS seen, false AS cycle
    FROM lineage.source_resolution x JOIN lineage.source_reference r USING (reference_pk)
    WHERE x.resolution = 'RESOLVED'
  UNION ALL
    SELECT w.start_pk, x2.source_product_pk, w.depth + 1, w.seen || x2.source_product_pk,
           x2.source_product_pk = ANY(w.seen)
    FROM walk w
    JOIN lineage.source_reference r2 ON r2.product_pk = w.at_pk AND r2.validity = 'VALID'
    JOIN lineage.source_resolution x2 ON x2.reference_pk = r2.reference_pk AND x2.resolution = 'RESOLVED'
    WHERE NOT w.cycle AND w.depth < 12)
UPDATE lineage.source_resolution x SET chain = CASE
        WHEN bool_or_cycle THEN 'CYCLE' WHEN max_depth > 1 THEN 'MULTI_HOP'
        WHEN x.source_cites_source THEN 'ENDS_AT_UNRESOLVED_REFERENCE' ELSE 'SINGLE_HOP' END
FROM (SELECT start_pk, bool_or(cycle) AS bool_or_cycle, max(depth) AS max_depth FROM walk GROUP BY start_pk) w
WHERE w.start_pk = x.reference_pk;
UPDATE lineage.source_resolution SET chain = 'NOT_APPLICABLE' WHERE chain IS NULL;

-- Consistency with the cited source: the same dosage form and the same active ingredients and strengths. A side
-- that states no form or no active ingredient cannot be confirmed and is INCOMPLETE, never consistent.
UPDATE lineage.source_resolution x SET consistency = CASE
        WHEN a.product_pk IS NULL OR b.product_pk IS NULL OR a.form_code IS NULL OR b.form_code IS NULL
             OR jsonb_array_length(a.active) = 0 OR jsonb_array_length(b.active) = 0 THEN 'INCOMPLETE'
        WHEN a.form_code <> b.form_code THEN 'FORM_DIFFERS'
        WHEN a.active <> b.active THEN 'ACTIVE_DIFFERS'
        ELSE 'CONSISTENT' END
FROM lineage.source_reference r
JOIN lineage.source_resolution y ON y.reference_pk = r.reference_pk
LEFT JOIN lineage.product_attributes a ON a.product_pk = r.product_pk
LEFT JOIN lineage.product_attributes b ON b.product_pk = y.source_product_pk
WHERE x.reference_pk = r.reference_pk AND x.resolution = 'RESOLVED';
UPDATE lineage.source_resolution SET consistency = 'NOT_APPLICABLE' WHERE consistency IS NULL;

UPDATE lineage.source_resolution x SET source_has_direct = EXISTS (
        SELECT 1 FROM national.operation_edge e
        WHERE e.product_pk = x.source_product_pk AND e.report_product_pk = x.source_product_pk
          AND e.product_scope = 'product' AND e.is_manufacture AND e.confidence = 'DIRECT')
WHERE x.resolution = 'RESOLVED';

-- Eligibility: the same rule as lineage.eligibility().
UPDATE lineage.source_resolution x SET reasons = array_remove(ARRAY[
        CASE WHEN r.validity <> 'VALID' THEN 'validity:' || r.validity END,
        CASE WHEN r.product_kind <> 'product' THEN 'citing:kit_part' END,
        CASE WHEN x.resolution <> 'RESOLVED' THEN 'resolution:' || x.resolution END,
        CASE WHEN x.resolution = 'RESOLVED' AND x.source_selection_class NOT IN ('confirmed', 'unconfirmed')
             THEN 'source_version:' || x.source_selection_class END,
        CASE WHEN x.resolution = 'RESOLVED' AND x.chain <> 'SINGLE_HOP' THEN 'chain:' || x.chain END,
        CASE WHEN x.resolution = 'RESOLVED' AND x.source_cites_source THEN 'source:repackaged_or_relabeled' END,
        CASE WHEN x.resolution = 'RESOLVED' AND x.consistency <> 'CONSISTENT' THEN 'consistency:' || x.consistency END,
        CASE WHEN x.resolution = 'RESOLVED' AND NOT x.source_has_direct THEN 'source:no_direct_manufacture' END
    ], NULL)
FROM lineage.source_reference r WHERE r.reference_pk = x.reference_pk;
UPDATE lineage.source_resolution SET status = CASE WHEN cardinality(reasons) = 0 THEN 'ELIGIBLE' ELSE 'EXCLUDED' END;

-- SOURCE_LINKED_MANUFACTURING_EVIDENCE: one row per eligible reference and DIRECT edge of the source product,
-- with the provenance of every step (citing SPL, source SPL, the source's assertion, the FDA registration line).
INSERT INTO lineage.source_linked_evidence (reference_pk, source_assertion_pk, linked_product_pk, source_product_pk,
       citing_document_pk, source_document_pk, duns, fei, registration_pk, registration_source_file_id, build_id)
SELECT x.reference_pk, e.assertion_pk, r.product_pk, x.source_product_pk, r.document_pk, x.source_document_pk,
       e.duns, e.fei, di.registration_pk, rr.source_file_id, r.build_id
FROM lineage.source_resolution x
JOIN lineage.source_reference r USING (reference_pk)
JOIN national.operation_edge e ON e.product_pk = x.source_product_pk AND e.report_product_pk = x.source_product_pk
     AND e.product_scope = 'product' AND e.is_manufacture AND e.confidence = 'DIRECT'
LEFT JOIN national.duns_identity di ON di.duns = e.duns
LEFT JOIN national.registration_record rr ON rr.registration_pk = di.registration_pk
WHERE x.status = 'ELIGIBLE';
"""


def resolve(conn, build_id: int) -> None:
    conn.execute(RESOLVE_SQL)


def summary(conn) -> dict:
    q = lambda sql: [list(r) for r in conn.execute(sql).fetchall()]  # noqa: E731
    return {
        "references": conn.execute("SELECT count(*) FROM lineage.source_reference").fetchone()[0],
        "citing_products": conn.execute("SELECT count(DISTINCT product_pk) FROM lineage.source_reference").fetchone()[0],
        "by_validity": q("SELECT validity, count(*) FROM lineage.source_reference GROUP BY 1 ORDER BY 1"),
        "by_resolution": q("SELECT resolution, count(*) FROM lineage.source_resolution GROUP BY 1 ORDER BY 1"),
        "by_chain": q("SELECT chain, count(*) FROM lineage.source_resolution GROUP BY 1 ORDER BY 1"),
        "by_consistency": q("SELECT consistency, count(*) FROM lineage.source_resolution GROUP BY 1 ORDER BY 1"),
        "by_status": q("SELECT status, count(*) FROM lineage.source_resolution GROUP BY 1 ORDER BY 1"),
        "exclusion_reasons": q("SELECT reason, count(*) FROM lineage.source_resolution, unnest(reasons) reason "
                               "GROUP BY 1 ORDER BY 2 DESC, 1"),
        "eligible_references": conn.execute("SELECT count(*) FROM lineage.source_resolution WHERE status = 'ELIGIBLE'").fetchone()[0],
        "unique_eligible_pairs": conn.execute(
            "SELECT count(DISTINCT (r.product_pk, x.source_product_pk)) FROM lineage.source_resolution x "
            "JOIN lineage.source_reference r USING (reference_pk) WHERE x.status = 'ELIGIBLE'").fetchone()[0],
        "evidence_rows": conn.execute("SELECT count(*) FROM lineage.source_linked_evidence").fetchone()[0],
        "coverage": q("SELECT coverage_tier, count(*) FROM lineage.v_product_coverage GROUP BY 1 ORDER BY 1"),
        "direct_tier_unchanged": q("SELECT direct_tier_status, count(*) FROM lineage.v_product_coverage GROUP BY 1 ORDER BY 1"),
    }


def fingerprint(conn) -> dict:
    """SHA-256 over each lineage table's rows by natural key (independent of generated identities)."""
    queries = {
        "source_reference": """SELECT d.set_id, d.version, r.loc, p.loc, r.source_code_raw, r.validity
                               FROM lineage.source_reference r JOIN national.spl_document d USING (document_pk)
                               JOIN national.product p ON p.product_pk = r.product_pk ORDER BY 1, 2, 3""",
        "source_resolution": """SELECT d.set_id, d.version, r.loc, x.resolution, x.source_set_id, x.chain, x.consistency,
                                       x.status, x.reasons
                                FROM lineage.source_resolution x JOIN lineage.source_reference r USING (reference_pk)
                                JOIN national.spl_document d ON d.document_pk = r.document_pk ORDER BY 1, 2, 3""",
        "source_linked_evidence": """SELECT d.set_id, d.version, r.loc, e.source_assertion_pk, e.duns, e.fei
                                     FROM lineage.source_linked_evidence e JOIN lineage.source_reference r USING (reference_pk)
                                     JOIN national.spl_document d ON d.document_pk = r.document_pk ORDER BY 1, 2, 3, 4""",
    }
    out = {}
    for name, sql in queries.items():
        h = hashlib.sha256()
        n = 0
        for row in conn.execute(sql):
            h.update(json.dumps(row, default=str).encode() + b"\n")
            n += 1
        out[name] = {"rows": n, "sha256": h.hexdigest()}
    return out


CHAIN_SQL = """
SELECT r.reference_pk, x.status, x.reasons, x.resolution, x.chain, x.consistency,
       cd.set_id, cd.version, cd.document_id, cd.published_date, cd.xml_sha256, cf.local_path, cd.member_name,
       cm.member_sha256, cd.xml_member_name, r.loc, r.product_ndc_raw, r.source_code_raw,
       sd.set_id, sd.version, sd.document_id, sd.published_date, sd.xml_sha256, sf.local_path, sd.member_name,
       sm.member_sha256, sd.xml_member_name, sp.ndc_raw,
       e.source_assertion_pk, oe.loc, oe.duns, oe.fei, oe.identity_status, oe.confidence,
       rr.registration_pk, rr.line_no, rf.name, rf.sha256, rf.generated_at
FROM lineage.source_reference r
JOIN lineage.source_resolution x USING (reference_pk)
JOIN national.spl_document cd ON cd.document_pk = r.document_pk
JOIN national.archive_member cm ON cm.document_pk = cd.document_pk AND cm.status = 'loaded'
JOIN national.source_file cf ON cf.source_file_id = cm.source_file_id
LEFT JOIN national.spl_document sd ON sd.document_pk = x.source_document_pk
LEFT JOIN national.archive_member sm ON sm.document_pk = sd.document_pk AND sm.status = 'loaded'
LEFT JOIN national.source_file sf ON sf.source_file_id = sm.source_file_id
LEFT JOIN national.product sp ON sp.product_pk = x.source_product_pk
LEFT JOIN lineage.source_linked_evidence e ON e.reference_pk = r.reference_pk
LEFT JOIN national.operation_edge oe ON oe.assertion_pk = e.source_assertion_pk
LEFT JOIN national.registration_record rr ON rr.registration_pk = e.registration_pk
LEFT JOIN national.source_file rf ON rf.source_file_id = rr.source_file_id
WHERE r.product_ndc_5_4 = %s
ORDER BY r.reference_pk, e.source_assertion_pk
"""


def _element(data_dir: Path, local_path, member, member_sha, xml_member, xml_sha, loc) -> str:
    root = ET.fromstring(_read_xml(data_dir, local_path, member, member_sha, xml_member, xml_sha))
    steps = loc.strip("/").split("/")[1:]
    el = root.find("./" + "/".join(HL7 + s for s in steps))
    if el is None:
        raise ValueError(f"cited element not found at {loc}")
    s = ET.tostring(el, encoding="unicode")
    return " ".join(s.replace('xmlns:ns0="urn:hl7-org:v3" ', "").replace("ns0:", "").split())


def evidence_chain(conn, product_ndc: str, *, data_dir: Path | None = None) -> list[dict]:
    """Every source reference of a product (by its NDC product code), with each step's provenance and the two cited XML
    elements re-read from the release and hash-verified: the citing asEquivalentEntity and the source's MANUFACTURE."""
    data_dir = data_dir or config.data_dir()
    n54 = ndc.to_product_5_4(product_ndc) if ndc.is_well_formed(product_ndc) else None
    if n54 is None:
        raise ValueError(f"not a hyphenated NDC product code: {product_ndc!r}")
    out = []
    for row in conn.execute(CHAIN_SQL, (n54,)).fetchall():
        (ref_pk, status, reasons, resolution, chain, consistency, c_set, c_ver, c_doc, c_pub, c_xsha, c_path, c_member,
         c_msha, c_xmem, r_loc, own, src_raw, s_set, s_ver, s_doc, s_pub, s_xsha, s_path, s_member, s_msha, s_xmem,
         s_ndc, a_pk, a_loc, duns, fei, ident, conf, reg_pk, reg_line, reg_file, reg_sha, reg_gen) = row
        step = {
            "relationship": "SOURCE_LINKED_MANUFACTURING_EVIDENCE" if a_pk else "SOURCE_NDC_REFERENCE",
            "reference_pk": ref_pk, "status": status, "reasons": list(reasons), "resolution": resolution,
            "chain": chain, "consistency": consistency,
            "citing": {"product_ndc": own, "set_id": c_set, "version": c_ver, "document_id": c_doc,
                       "published_date": c_pub.isoformat() if c_pub else None, "xml_sha256": c_xsha,
                       "release_part": Path(c_path).name, "member": c_member, "element_loc": r_loc,
                       "element": _element(data_dir, c_path, c_member, c_msha, c_xmem, c_xsha, r_loc)},
            "source_code_cited": src_raw,
        }
        if s_set:
            step["source"] = {"product_ndc": s_ndc, "set_id": s_set, "version": s_ver, "document_id": s_doc,
                              "published_date": s_pub.isoformat() if s_pub else None, "xml_sha256": s_xsha,
                              "release_part": Path(s_path).name, "member": s_member}
        if a_pk:
            step["source_direct_manufacture"] = {
                "assertion_pk": a_pk, "loc": a_loc, "duns": duns, "fei": fei, "identity_status": ident, "confidence": conf,
                "element": _element(data_dir, s_path, s_member, s_msha, s_xmem, s_xsha, a_loc)}
            step["registration"] = {"registration_pk": reg_pk, "line_no": reg_line, "file": reg_file, "sha256": reg_sha,
                                    "generated_at": reg_gen.isoformat() if reg_gen else None}
        out.append(step)
    return out
