"""DST-08 source-NDC inventory: every asEquivalentEntity in every canonical label, read independently of the parser.

For each canonical document of the current graph (build 8) this re-opens the release member, verifies the member and
XML SHA-256 against the database record, and walks the XML with code that imports nothing from the fineprint parser
(the raw helpers of verify_audit_sample.py plus the walk below). It records, per product and kit part, every
asEquivalentEntity element verbatim (class code, equivalence code and code system, the definingMaterialKind code and
code system, and the element's location), the product's own code, dosage form and active ingredients, and the
operations the document's establishments assert for it. The database supplies only the list of canonical documents,
their hashes and locations, the canonical product index and each product's manufacturing status.

Each reference is then classified exactly, with no name, address or similarity matching:
  * validity: the FDA SPL Implementation Guide (v1, 2023-12) form is classCode EQUIV, code C64637 ("Same") in the NCI
    Thesaurus code system, and a source NDC *product* code in the NDC code system (sections 3.1.2 and 3.2.2);
  * resolution: canonical top-level products in other sets whose normalised 5-4 product code equals the source code;
  * chain: whether the single resolved source product itself cites a source (multi-hop), and cycles;
  * consistency: the source product's dosage form and active ingredients (UNII and strength) against the citing
    product's, which the Implementation Guide requires to be the same (3.2.2.3, 3.2.2.10).

Outputs: docs/research/dst08/source_inventory.json (counts), and outside the repository
$FINEPRINT_DATA/research/dst08/references.csv (one row per reference) and products.jsonl.gz (per-document walk).

  python -I scripts/research/dst08_source_inventory.py --db fineprint [--limit N]
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import sys
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "research"))
import verify_audit_sample as raw  # noqa: E402  independent XML helpers
from fineprint import db  # noqa: E402  database access only

NS = raw.NS
NDC_SYSTEM = "2.16.840.1.113883.6.69"
NCI_SYSTEM = "2.16.840.1.113883.3.26.1.1"
SAME = "C64637"
MANUFACTURE, REPACK, RELABEL, SALVAGE = "C43360", "C73606", "C73607", "C70827"
OUT_DIR = raw.DATA / "research" / "dst08"
SUMMARY = REPO / "docs" / "research" / "dst08" / "source_inventory.json"


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def norm_text(e) -> str | None:
    if e is None:
        return None
    t = " ".join("".join(e.itertext()).split())
    return t or None


def code_pattern(code: str | None) -> str:
    """'product' (4-4, 5-3, 5-4), 'package' (4-4-2, 5-3-2, 5-4-1, 5-4-2), 'malformed' or 'missing'."""
    if not code:
        return "missing"
    segs = code.strip().split("-")
    if not all(s.isdigit() for s in segs):
        return "malformed"
    pat = tuple(len(s) for s in segs)
    if pat in ((4, 4), (5, 3), (5, 4)):
        return "product"
    if pat in ((4, 4, 2), (5, 3, 2), (5, 4, 1), (5, 4, 2)):
        return "package"
    return "malformed"


def ingredients(holder) -> list[tuple]:
    """Active ingredients as (unii, numerator value, numerator unit, denominator value, denominator unit), sorted.

    SPL R5 uses <ingredient classCode="ACT..."><ingredientSubstance>; pre-2009 R4 uses <activeIngredient>."""
    out = []
    for ing in holder.findall(NS + "ingredient"):
        if not (ing.get("classCode") or "").startswith("ACT"):
            continue
        sub = ing.find(NS + "ingredientSubstance")
        out.append(_ingredient(ing, sub))
    for ing in holder.findall(NS + "activeIngredient"):
        sub = ing.find(NS + "activeIngredientSubstance")
        out.append(_ingredient(ing, sub))
    return sorted(out)


def _ingredient(ing, sub) -> tuple:
    code = sub.find(NS + "code") if sub is not None else None
    q = ing.find(NS + "quantity")
    num = q.find(NS + "numerator") if q is not None else None
    den = q.find(NS + "denominator") if q is not None else None
    g = lambda e, a: e.get(a) if e is not None else None  # noqa: E731
    return (g(code, "code") or "", g(num, "value") or "", g(num, "unit") or "", g(den, "value") or "", g(den, "unit") or "")


def equivalents(holder, holder_loc: str) -> list[dict]:
    refs = []
    counts: Counter = Counter()
    for child in holder:
        t = local(child.tag)
        counts[t] += 1
        if t != "asEquivalentEntity":
            continue
        code = child.find(NS + "code")
        dmk = child.find(NS + "definingMaterialKind")
        dcode = dmk.find(NS + "code") if dmk is not None else None
        refs.append({
            "loc": f"{holder_loc}/asEquivalentEntity[{counts[t]}]",
            "class_code": child.get("classCode"),
            "eq_code": code.get("code") if code is not None else None,
            "eq_system": code.get("codeSystem") if code is not None else None,
            "src_code": dcode.get("code") if dcode is not None else None,
            "src_system": dcode.get("codeSystem") if dcode is not None else None,
        })
    return refs


def product_record(inner, loc: str, kind: str, parent_code: str | None) -> dict:
    code = inner.find(NS + "code")
    form = inner.find(NS + "formCode")
    return {
        "loc": loc, "kind": kind, "parent_code": parent_code,
        "code": code.get("code") if code is not None else None,
        "code_system": code.get("codeSystem") if code is not None else None,
        "name": norm_text(inner.find(NS + "name")),
        "form": form.get("code") if form is not None else None,
        "form_name": form.get("displayName") if form is not None else None,
        "active": ingredients(inner),
        "refs": equivalents(inner, loc),
    }


def walk_products(root) -> list[dict]:
    """Products in every section, with locations in the parser's convention (every step indexed among siblings of
    the same tag, then /manufacturedProduct/<inner>), so that a reference can be matched to its product row exactly."""
    found: list[dict] = []

    def descend(elem, loc: str):
        counts: Counter = Counter()
        for child in elem:
            t = local(child.tag)
            counts[t] += 1
            cloc = f"{loc}/{t}[{counts[t]}]"
            if t == "subject" and local(elem.tag) == "section":
                outer = child.find(NS + "manufacturedProduct")
                if outer is None:
                    continue
                inner_tag = next((n for n in ("manufacturedProduct", "manufacturedMedicine") if outer.find(NS + n) is not None), None)
                if inner_tag is None:
                    continue
                inner = outer.find(NS + inner_tag)
                ploc = f"{cloc}/manufacturedProduct/{inner_tag}"
                rec = product_record(inner, ploc, "product", None)
                found.append(rec)
                pcounts: Counter = Counter()
                for part in inner:
                    pt = local(part.tag)
                    pcounts[pt] += 1
                    if pt != "part":
                        continue
                    pp_tag = next((n for n in ("partProduct", "partMedicine") if part.find(NS + n) is not None), None)
                    if pp_tag is None:
                        continue
                    found.append(product_record(part.find(NS + pp_tag), f"{ploc}/part[{pcounts[pt]}]/{pp_tag}", "kit_part", rec["code"]))
            elif t in ("component", "structuredBody", "section"):
                descend(child, cloc)

    descend(root, "/document")
    return found


def validity(ref: dict, own_code: str | None, n_refs_on_product: int) -> str:
    pat = code_pattern(ref["src_code"])
    if ref["class_code"] not in (None, "EQUIV"):
        return "NOT_EQUIV_CLASS"
    if ref["eq_code"] != SAME or ref["eq_system"] != NCI_SYSTEM:
        return "NOT_SAME_EQUIVALENCE"
    if ref["src_system"] != NDC_SYSTEM:
        return "NOT_NDC_CODE_SYSTEM"
    if pat == "package":
        return "PACKAGE_CODE_NOT_PRODUCT_CODE"
    if pat != "product":
        return "MALFORMED_OR_MISSING_CODE"
    if own_code and raw.to_5_4(ref["src_code"]) == raw.to_5_4(own_code):
        return "SELF_REFERENCE"
    if n_refs_on_product > 1:
        return "MULTIPLE_SOURCES_FOR_PRODUCT"
    return "VALID"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with db.connect(a.db) as c:
        build = c.execute("SELECT build_id FROM national.graph_build WHERE status = 'completed' ORDER BY build_id DESC LIMIT 1").fetchone()[0]
        docs = c.execute(
            """SELECT d.document_pk, d.set_id, d.version, d.document_id, f.name, d.member_name, d.xml_member_name,
                      m.member_sha256, d.xml_sha256, s.selection_class, d.published_date
               FROM national.set_version_selection s
               JOIN national.spl_document d ON d.document_pk = s.document_pk
               JOIN national.archive_member m ON m.document_pk = d.document_pk AND m.status = 'loaded'
               JOIN national.source_file f ON f.source_file_id = m.source_file_id
               ORDER BY f.name, d.member_name""").fetchall()
        # The canonical product rows, with each top-level product's manufacturing status.
        prod_rows = c.execute(
            """SELECT p.product_pk, p.document_pk, p.loc, p.kind, p.ndc_raw, p.ndc_product_5_4, s.set_id, s.selected_version,
                      s.selection_class, v.manufacturing_status, v.evidence_status
               FROM national.set_version_selection s
               JOIN national.product p ON p.document_pk = s.document_pk
               LEFT JOIN national.v_product_manufacturing_status v ON v.product_pk = p.product_pk""").fetchall()
        # Every product code in any document of the release, canonical or not (for version analysis).
        all_rows = c.execute(
            """SELECT p.ndc_product_5_4, d.set_id, d.version, p.kind, (s.document_pk IS NOT NULL) AS canonical
               FROM national.product p JOIN national.spl_document d ON d.document_pk = p.document_pk
               LEFT JOIN national.set_version_selection s ON s.document_pk = d.document_pk
               WHERE p.ndc_product_5_4 IS NOT NULL""").fetchall()
        versions = dict(c.execute("SELECT lower(set_id), count(DISTINCT version) FROM national.spl_document GROUP BY 1").fetchall())
        # Same-establishment MANUFACTURE beside REPACK/RELABEL on a top-level product (the assertion-quality pattern).
        repack_mfg = {r[0] for r in c.execute(
            """SELECT DISTINCT a.product_pk FROM national.operation_assertion a
               JOIN national.set_version_selection s ON s.document_pk = a.document_pk
               WHERE a.operation_code = %s AND a.product_scope = 'product'
                 AND EXISTS (SELECT 1 FROM national.operation_assertion b WHERE b.document_pk = a.document_pk
                             AND b.establishment_org_pk = a.establishment_org_pk AND b.product_pk = a.product_pk
                             AND b.operation_code IN (%s, %s))""", (MANUFACTURE, REPACK, RELABEL))}
    if a.limit:
        docs = docs[: a.limit]
    by_loc = {(r[1], r[2]): r for r in prod_rows}
    canonical_by_54 = defaultdict(list)
    for r in prod_rows:
        if r[5]:
            canonical_by_54[r[5]].append(r)
    noncanonical_by_54 = defaultdict(set)
    for n54, set_id, ver, kind, canonical in all_rows:
        if not canonical:
            noncanonical_by_54[n54].add((set_id.lower(), ver, kind))

    parts = {p.name: p for p in (raw.DATA / "raw" / "dailymed" / "human_rx_full").glob("*/dm_spl_release_human_rx_part*.zip")}
    tally: Counter = Counter()
    records: list[dict] = []          # one per product with its references (kept compact)
    cur, zf = None, None
    with gzip.open(OUT_DIR / "products.jsonl.gz", "wt", encoding="utf-8") as walk_out:
        for i, (pk, set_id, ver, doc_id, part, member, xml_member, msha, xsha, sel_class, pub) in enumerate(docs, 1):
            if part != cur:
                if zf:
                    zf.close()
                zf, cur = zipfile.ZipFile(parts[part]), part
            data = zf.read(member)
            if raw.sha256(data) != msha:
                tally["error_member_hash"] += 1
                continue
            with zipfile.ZipFile(io.BytesIO(data)) as inner:
                xml = inner.read(xml_member)
            if raw.sha256(xml) != xsha:
                tally["error_xml_hash"] += 1
                continue
            try:
                root = raw.parse_xml(xml)
            except Exception:
                tally["error_parse"] += 1
                continue
            tally["documents"] += 1
            perfs = [p for p in raw.performances(root) if p["in_author"]]
            ops_by_code = defaultdict(set)
            for p in perfs:
                for code in p["product_codes"] or [None]:
                    for d in p["duns"] or [None]:
                        ops_by_code[code].add((d, p["code"]))
            doc_ops = sorted({p["code"] for p in perfs if p["code"]})
            prods = walk_products(root)
            n_equiv_all = sum(1 for _ in root.iter(NS + "asEquivalentEntity"))
            n_equiv_seen = sum(len(p["refs"]) for p in prods)
            if n_equiv_all != n_equiv_seen:
                tally["documents_with_asEquivalentEntity_outside_products_and_parts"] += 1
            for p in prods:
                row = by_loc.get((pk, p["loc"]))
                if row is None:
                    tally["product_without_db_row"] += 1
                ops = sorted({op for _, op in ops_by_code.get(p["code"], ())})
                rec = {
                    "document_pk": pk, "set_id": set_id, "version": ver, "document_id": doc_id, "part": part,
                    "member": member, "xml_member": xml_member, "member_sha256": msha, "xml_sha256": xsha,
                    "selection_class": sel_class, "published_date": pub.isoformat() if pub else None,
                    "product_pk": row[0] if row else None, "status": row[9] if row else None,
                    "evidence_status": row[10] if row else None, "doc_ops": doc_ops, "product_ops": ops,
                    "repack_mfg": bool(row and row[0] in repack_mfg), **p,
                }
                records.append(rec)
            walk_out.write(json.dumps({"document_pk": pk, "set_id": set_id, "version": ver, "products": prods,
                                       "doc_ops": doc_ops, "n_equiv_all": n_equiv_all}, separators=(",", ":")) + "\n")
            if i % 5000 == 0:
                print(f"{i}/{len(docs)} documents {time.time() - t0:.0f}s", file=sys.stderr)
    if zf:
        zf.close()

    # Products of the inventory by normalised code, for consistency checks and chains.
    rec_by_pk = {r["product_pk"]: r for r in records if r["product_pk"]}

    def resolve(ref: dict, rec: dict) -> dict:
        n54 = raw.to_5_4(ref["src_code"])
        cands = [r for r in canonical_by_54.get(n54, []) if r[3] == "product"]
        parts_only = [r for r in canonical_by_54.get(n54, []) if r[3] == "kit_part"]
        other = [r for r in cands if r[6].lower() != rec["set_id"].lower()]
        same_set = [r for r in cands if r[6].lower() == rec["set_id"].lower()]
        nonc = sorted(noncanonical_by_54.get(n54, set()))
        if len(other) == 1:
            status = "RESOLVED"
        elif len(other) > 1:
            status = "MULTIPLE_CANDIDATES"
        elif same_set:
            status = "ONLY_SAME_SET"
        elif parts_only:
            status = "ONLY_KIT_PART"
        elif nonc:
            status = "ONLY_NON_CANONICAL_VERSION"
        else:
            status = "NO_CANDIDATE"
        return {"n54": n54, "status": status, "cands": other, "parts_only": parts_only, "noncanonical": nonc}

    def valid_refs(r: dict) -> list[dict]:
        return [x for x in r["refs"] if validity(x, r["code"], len(r["refs"])) == "VALID"]

    def chain(rec: dict, ref: dict) -> tuple[str, int, list[str]]:
        """Follow unique resolutions through cited source products; return (kind, depth, path of set ids)."""
        path = [rec["set_id"].lower()]
        cur_rec, cur_ref = rec, ref
        for depth in range(1, 12):
            res = resolve(cur_ref, cur_rec)
            if res["status"] != "RESOLVED":
                return ("ENDS_UNRESOLVED" if depth > 1 else "UNRESOLVED", depth, path)
            nxt = rec_by_pk.get(res["cands"][0][0])
            if nxt is None:
                return ("ENDS_UNRESOLVED", depth, path)
            if nxt["set_id"].lower() in path:
                return ("CYCLE", depth, path + [nxt["set_id"].lower()])
            path.append(nxt["set_id"].lower())
            nrefs = valid_refs(nxt)
            if not nrefs:
                return ("SINGLE_HOP" if depth == 1 else "MULTI_HOP", depth, path)
            cur_rec, cur_ref = nxt, nrefs[0]
        return ("TOO_DEEP", 12, path)

    columns = ["ref_id", "set_id", "version", "document_id", "document_pk", "product_pk", "product_kind", "product_code",
               "product_status", "evidence_status", "selection_class", "published_date", "product_name", "form",
               "product_ops", "repack_mfg", "n_refs_on_product", "ref_loc", "class_code", "eq_code", "eq_system",
               "src_code", "src_system", "src_pattern", "src_5_4", "validity", "resolution", "n_candidates",
               "candidate_product_pks", "candidate_set_ids", "candidate_statuses", "candidate_selection_classes",
               "kit_part_matches", "noncanonical_matches", "repack_set_versions", "source_set_versions",
               "source_cites_source", "chain", "chain_depth", "chain_sets", "form_match", "active_match",
               "doc_ops", "package_prefix_candidates", "part", "member", "member_sha256", "xml_sha256"]
    out = Counter()
    with (OUT_DIR / "references.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(columns)
        for rec in records:
            if rec["refs"]:
                out[f"products_with_reference_{rec['kind']}"] += 1
            for ref in rec["refs"]:
                v = validity(ref, rec["code"], len(rec["refs"]))
                res = resolve(ref, rec) if v == "VALID" else {"n54": raw.to_5_4(ref["src_code"]), "status": "NOT_RESOLVED_INVALID", "cands": [], "parts_only": [], "noncanonical": []}
                src = rec_by_pk.get(res["cands"][0][0]) if res["status"] == "RESOLVED" else None
                ch = chain(rec, ref) if v == "VALID" else ("NOT_APPLICABLE", 0, [])
                form_match = active_match = ""
                if src is not None:
                    form_match = str(src["form"] == rec["form"])
                    active_match = "True" if src["active"] == rec["active"] else (
                        "SAME_UNII_DIFFERENT_STRENGTH" if sorted(x[0] for x in src["active"]) == sorted(x[0] for x in rec["active"]) else "False")
                cands = res["cands"]
                # Diagnostic only, never a link: what a package code's first two segments would match if truncated.
                prefix_cands = ""
                if code_pattern(ref["src_code"]) == "package":
                    prefix = raw.to_5_4("-".join(ref["src_code"].split("-")[:2]))
                    prefix_cands = sum(1 for r in canonical_by_54.get(prefix, []) if r[3] == "product" and r[6].lower() != rec["set_id"].lower())
                    out[f"diagnostic_package_prefix_candidates:{min(prefix_cands, 2)}"] += 1
                row = [
                    f"{rec['set_id'].lower()}|{rec['version']}|{ref['loc']}", rec["set_id"], rec["version"], rec["document_id"],
                    rec["document_pk"], rec["product_pk"], rec["kind"], rec["code"], rec["status"], rec["evidence_status"],
                    rec["selection_class"], rec["published_date"], rec["name"], rec["form_name"], ";".join(rec["product_ops"]),
                    rec["repack_mfg"], len(rec["refs"]), ref["loc"], ref["class_code"], ref["eq_code"], ref["eq_system"],
                    ref["src_code"], ref["src_system"], code_pattern(ref["src_code"]), res["n54"], v, res["status"], len(cands),
                    ";".join(str(r[0]) for r in cands), ";".join(r[6] for r in cands), ";".join(str(r[9]) for r in cands),
                    ";".join(r[8] for r in cands), len(res["parts_only"]), len(res["noncanonical"]),
                    versions.get(rec["set_id"].lower(), 0),
                    ";".join(str(versions.get(r[6].lower(), 0)) for r in cands),
                    bool(src and valid_refs(src)), ch[0], ch[1], ">".join(ch[2]), form_match, active_match,
                    ";".join(rec["doc_ops"]), prefix_cands, rec["part"], rec["member"], rec["member_sha256"], rec["xml_sha256"],
                ]
                w.writerow(row)
                out["references"] += 1
                out[f"validity:{v}"] += 1
                out[f"resolution:{res['status']}"] += 1
                out[f"chain:{ch[0]}"] += 1
                out[f"kind:{rec['kind']}"] += 1
                if src is not None:
                    out[f"resolved_source_status:{src['status']}"] += 1
                    out[f"resolved_form_match:{form_match}"] += 1
                    out[f"resolved_active_match:{active_match}"] += 1
    summary = {
        "generated_at": raw.utc_now(), "graph_build": build, "documents_in_scope": len(docs), "seconds": round(time.time() - t0),
        "scan_tally": dict(sorted(tally.items())), "reference_tally": dict(sorted(out.items())),
        "outputs_outside_repo": ["FINEPRINT_DATA/research/dst08/references.csv", "FINEPRINT_DATA/research/dst08/products.jsonl.gz"],
        "references_csv_sha256": raw.sha256((OUT_DIR / "references.csv").read_bytes()),
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    sys.exit(main())
