"""DST-08 source checks of the frozen sample: raw XML and source-version relationships, re-derived per reference.

Refuses to run unless docs/research/dst08/sample_manifest.json matches its FREEZE hash. For every sampled reference:

  1. the citing label is re-opened from the release part and hash-verified, and the cited asEquivalentEntity element
     is located by its recorded path and printed verbatim;
  2. the source code is re-resolved from scratch against every product row of the release (canonical or not, any
     version, top-level or kit part), not from the inventory's resolution;
  3. every canonical top-level candidate in another set is opened from its own release member (hash-verified); its
     product with that code is compared with the citing product (dosage form; active ingredients by UNII and strength,
     which the SPL Implementation Guide requires to be the same, 3.2.2.3 and 3.2.2.10);
  4. the candidate's MANUFACTURE assertions are read from its XML and matched to the graph's MANUFACTURE edges for it:
     each DIRECT edge must come from a performance in the candidate's canonical version that is scoped to exactly the
     cited source code, by the same DUNS (the manufacturing statement belongs to the source product and version);
  5. every version of the candidate's set in the release is listed with whether it still lists the code and asserts
     MANUFACTURE for it, and the publication dates of the citing and the source versions are compared;
  6. a candidate that itself cites a source is followed one further hop.

Each check yields a mechanical result; nothing here decides eligibility by names, companies, addresses or product
similarity. Output: docs/research/dst08/sample_checks.json and sample_checks_digest.md. The AI review of these
results is recorded separately (sample_ai_review.csv); human adjudication is a separate, blank worksheet.

  python -I scripts/research/dst08_check_sample.py --db fineprint
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "research"))
import dst08_source_inventory as inv  # noqa: E402  independent XML walk (no fineprint parser imports)
import verify_audit_sample as raw  # noqa: E402
from fineprint import db  # noqa: E402  database access only

NS = raw.NS
MANIFEST = REPO / "docs" / "research" / "dst08" / "sample_manifest.json"
FREEZE = REPO / "docs" / "research" / "dst08" / "sample_FREEZE.json"
OUT = REPO / "docs" / "research" / "dst08" / "sample_checks.json"
DIGEST = REPO / "docs" / "research" / "dst08" / "sample_checks_digest.md"
PARTS = {p.name: p for p in (raw.DATA / "raw" / "dailymed" / "human_rx_full").glob("*/dm_spl_release_human_rx_part*.zip")}


def open_xml(part: str, member: str, xml_member: str, member_sha: str, xml_sha: str) -> tuple[bytes, ET.Element]:
    with zipfile.ZipFile(PARTS[part]) as zf:
        data = zf.read(member)
    if raw.sha256(data) != member_sha:
        raise ValueError(f"member hash mismatch {member}")
    with zipfile.ZipFile(io.BytesIO(data)) as inner:
        xml = inner.read(xml_member)
    if raw.sha256(xml) != xml_sha:
        raise ValueError(f"xml hash mismatch {xml_member}")
    return xml, raw.parse_xml(xml)


def find_by_loc(root: ET.Element, loc: str) -> ET.Element | None:
    """Follow '/document/a[1]/b/c[2]': an indexed step is the n-th child with that tag, a bare step the first."""
    steps = loc.strip("/").split("/")
    if steps[0] != "document":
        return None
    elem = root
    for step in steps[1:]:
        tag, _, rest = step.partition("[")
        n = int(rest[:-1]) if rest else 1
        kids = [c for c in elem if inv.local(c.tag) == tag]
        if len(kids) < n:
            return None
        elem = kids[n - 1]
    return elem


def verbatim(elem: ET.Element) -> str:
    s = ET.tostring(elem, encoding="unicode")
    return " ".join(s.replace('xmlns:ns0="urn:hl7-org:v3" ', "").replace("ns0:", "").split())


def doc_location(c, document_pk: int) -> tuple:
    return c.execute(
        """SELECT f.name, d.member_name, d.xml_member_name, m.member_sha256, d.xml_sha256, d.set_id, d.version,
                  d.published_date, d.document_id
           FROM national.spl_document d
           JOIN national.archive_member m ON m.document_pk = d.document_pk AND m.status = 'loaded'
           JOIN national.source_file f ON f.source_file_id = m.source_file_id
           WHERE d.document_pk = %s""", (document_pk,)).fetchone()


def product_in(root: ET.Element, code: str, kind: str = "product") -> dict | None:
    hits = [p for p in inv.walk_products(root) if p["code"] == code and p["kind"] == kind]
    return hits[0] if len(hits) == 1 else ({"ambiguous_in_document": len(hits)} if hits else None)


def mfg_performances(root: ET.Element, code: str) -> list[dict]:
    return [{"loc": p["loc"], "duns": p["duns"], "org": p["org_name"]} for p in raw.performances(root)
            if p["in_author"] and p["code"] == raw.MANUFACTURE and code in p["product_codes"]]


def check_one(c, s: dict) -> dict:
    out: dict = {"sample_id": s["sample_id"], "stratum": s["stratum"], "ref_id": s["ref_id"], "checks": {}}
    xml_member = c.execute("SELECT xml_member_name FROM national.spl_document WHERE document_pk = %s",
                           (int(s["document_pk"]),)).fetchone()[0]
    _, root = open_xml(s["part"], s["member"], xml_member, s["member_sha256"], s["xml_sha256"])
    out["citing"] = {"set_id": s["set_id"], "version": s["version"], "document_id": s["document_id"],
                     "published_date": s["published_date"] or None, "product_code": s["product_code"],
                     "product_kind": s["product_kind"], "status_in_graph": s["product_status"]}
    el = find_by_loc(root, s["ref_loc"])
    out["checks"]["element_found_at_recorded_path"] = el is not None and inv.local(el.tag) == "asEquivalentEntity"
    out["cited_element"] = verbatim(el) if el is not None else None
    holder_loc = s["ref_loc"].rsplit("/", 1)[0]
    holder = find_by_loc(root, holder_loc)
    own = inv.product_record(holder, holder_loc, s["product_kind"], None) if holder is not None else None
    out["citing_product"] = {k: own[k] for k in ("code", "name", "form", "form_name", "active")} if own else {}
    out["citing_product"]["establishment_operations"] = sorted({(p["code"], tuple(p["duns"])) for p in raw.performances(root)
                                                                if p["in_author"] and own and own["code"] in p["product_codes"]})
    out["citing_product"]["unscoped_operations"] = sorted({p["code"] for p in raw.performances(root)
                                                           if p["in_author"] and not p["product_codes"]})
    refs_here = own["refs"] if own else []
    out["checks"]["one_reference_on_product"] = len(refs_here) == 1
    ref = next((r for r in refs_here if r["loc"] == s["ref_loc"]), None)
    out["checks"]["implementation_guide_form"] = bool(ref and ref["class_code"] in (None, "EQUIV") and ref["eq_code"] == inv.SAME
                                                      and ref["eq_system"] == inv.NCI_SYSTEM and ref["src_system"] == inv.NDC_SYSTEM)
    pattern = inv.code_pattern(ref["src_code"] if ref else None)
    out["checks"]["source_is_product_code"] = pattern == "product"
    n54 = raw.to_5_4(ref["src_code"]) if ref and pattern == "product" else None
    out["source_code"] = {"raw": ref and ref["src_code"], "pattern": pattern, "normalised_5_4": n54}
    if ref and pattern == "package":
        prefix = raw.to_5_4("-".join(ref["src_code"].split("-")[:2]))
        out["diagnostic_package_prefix_5_4"] = prefix
        n54_for_lookup = prefix
    else:
        n54_for_lookup = n54
    # Re-resolution from scratch: every product row of the release with this exact normalised product code.
    rows = c.execute(
        """SELECT p.product_pk, p.kind, p.ndc_raw, d.document_pk, d.set_id, d.version, d.published_date,
                  (s.document_pk IS NOT NULL) AS canonical, s.selection_class, v.manufacturing_status
           FROM national.product p JOIN national.spl_document d ON d.document_pk = p.document_pk
           LEFT JOIN national.set_version_selection s ON s.document_pk = d.document_pk
           LEFT JOIN national.v_product_manufacturing_status v ON v.product_pk = p.product_pk
           WHERE p.ndc_product_5_4 = %s ORDER BY d.set_id, d.version, p.kind""", (n54_for_lookup,)).fetchall() if n54_for_lookup else []
    out["release_matches"] = [{"product_pk": r[0], "kind": r[1], "ndc_raw": r[2], "set_id": r[4], "version": r[5],
                               "published_date": r[6].isoformat() if r[6] else None, "canonical": r[7],
                               "selection_class": r[8], "status": r[9]} for r in rows]
    cands = [r for r in rows if r[7] and r[1] == "product" and r[4].lower() != s["set_id"].lower()]
    out["checks"]["unique_canonical_candidate_in_other_set"] = len(cands) == 1 and pattern == "product"
    out["candidates"] = []
    for r in cands:
        loc = doc_location(c, r[3])
        _, croot = open_xml(loc[0], loc[1], loc[2], loc[3], loc[4])
        cprod = product_in(croot, r[2])
        perfs = mfg_performances(croot, r[2])
        edges = c.execute(
            """SELECT e.assertion_pk, e.duns, e.fei, e.identity_status, e.confidence, e.loc, a.product_code_raw,
                      di.registration_pk, rr.source_file_id, sf.name, di.evidence_as_of
               FROM national.operation_edge e JOIN national.operation_assertion a ON a.assertion_pk = e.assertion_pk
               LEFT JOIN national.duns_identity di ON di.duns = e.duns
               LEFT JOIN national.registration_record rr ON rr.registration_pk = di.registration_pk
               LEFT JOIN national.source_file sf ON sf.source_file_id = rr.source_file_id
               WHERE e.report_product_pk = %s AND e.is_manufacture ORDER BY e.assertion_pk""", (r[0],)).fetchall()
        perf_keys = {(p["loc"], d) for p in perfs for d in p["duns"]}
        edge_rows = [{"assertion_pk": e[0], "duns": e[1], "fei": e[2], "identity": e[3], "confidence": e[4], "loc": e[5],
                      "scoped_code": e[6], "in_source_xml_scoped_to_code": (e[5], e[1]) in perf_keys and e[6] == r[2],
                      "registration_pk": e[7], "registration_source_file": e[9],
                      "registration_as_of": e[10].isoformat() if e[10] else None} for e in edges]
        versions = []
        for v in c.execute("SELECT document_pk, version FROM national.spl_document WHERE lower(set_id) = lower(%s) ORDER BY version, document_pk", (r[4],)).fetchall():
            vloc = doc_location(c, v[0])
            _, vroot = open_xml(vloc[0], vloc[1], vloc[2], vloc[3], vloc[4])
            versions.append({"version": v[1], "canonical": v[0] == r[3], "published_date": vloc[7].isoformat() if vloc[7] else None,
                             "lists_code": product_in(vroot, r[2]) is not None,
                             "manufacture_scoped_duns": sorted({d for p in mfg_performances(vroot, r[2]) for d in p["duns"]})})
        nxt = list(cprod.get("refs", [])) if isinstance(cprod, dict) else []
        cand = {
            "product_pk": r[0], "set_id": r[4], "version": r[5], "document_id": loc[8], "published_date": r[6].isoformat() if r[6] else None,
            "selection_class": r[8], "status": r[9],
            "product": cprod and {k: cprod.get(k) for k in ("code", "name", "form", "form_name", "active")},
            "form_same": bool(cprod and own and "form" in cprod and cprod["form"] == own["form"]),
            "active_same": bool(cprod and own and "active" in cprod and cprod["active"] == own["active"]),
            "manufacture_performances_scoped_to_code": perfs,
            "graph_manufacture_edges": edge_rows,
            "direct_edges_all_from_source_xml": bool(edge_rows) and all(x["in_source_xml_scoped_to_code"] for x in edge_rows if x["confidence"] == "DIRECT"),
            "versions_in_release": versions,
            "candidate_cites_source": [{"src_code": x["src_code"], "eq_code": x["eq_code"]} for x in nxt],
        }
        if nxt and inv.code_pattern(nxt[0]["src_code"]) == "product":
            hop = c.execute(
                """SELECT p.product_pk, s.set_id, v.manufacturing_status FROM national.product p
                   JOIN national.set_version_selection s ON s.document_pk = p.document_pk
                   LEFT JOIN national.v_product_manufacturing_status v ON v.product_pk = p.product_pk
                   WHERE p.ndc_product_5_4 = %s AND p.kind = 'product'""", (raw.to_5_4(nxt[0]["src_code"]),)).fetchall()
            cand["next_hop"] = [{"product_pk": h[0], "set_id": h[1], "status": h[2]} for h in hop]
        out["candidates"].append(cand)
    one = out["candidates"][0] if len(out["candidates"]) == 1 else None
    out["checks"]["source_consistent_form_and_active"] = bool(one and one["form_same"] and one["active_same"])
    out["checks"]["source_has_direct_manufacture"] = bool(one and any(e["confidence"] == "DIRECT" for e in one["graph_manufacture_edges"]))
    out["checks"]["direct_statement_from_source_product_and_version"] = bool(one and one["direct_edges_all_from_source_xml"]
                                                                            and out["checks"]["source_has_direct_manufacture"])
    out["checks"]["single_hop"] = bool(one and not one["candidate_cites_source"])
    out["checks"]["source_selection_not_ambiguous"] = bool(one and one["selection_class"] in ("confirmed", "unconfirmed"))
    cites_pub, src_pub = out["citing"]["published_date"], one and one["published_date"]
    out["temporal"] = {"citing_published": cites_pub, "source_published": src_pub,
                       "source_version_published_after_citing_version": bool(cites_pub and src_pub and src_pub > cites_pub)}
    required = ("element_found_at_recorded_path", "one_reference_on_product", "implementation_guide_form", "source_is_product_code",
                "unique_canonical_candidate_in_other_set", "source_consistent_form_and_active", "source_has_direct_manufacture",
                "direct_statement_from_source_product_and_version", "single_hop", "source_selection_not_ambiguous")
    failed = [k for k in required if not out["checks"][k]]
    out["mechanical_result"] = "ELIGIBLE_SOURCE_LINKED" if not failed else "NOT_ELIGIBLE"
    out["failed_checks"] = failed
    return out


def digest(results: list[dict]) -> str:
    lines = ["# DST-08 sample source checks (mechanical, re-derived from raw XML)", "",
             "Generated by `scripts/research/dst08_check_sample.py` from the frozen sample. AI review and human",
             "adjudication are recorded separately.", ""]
    for r in results:
        lines += [f"## {r['sample_id']} ({r['stratum']})", "",
                  f"- citing: set `{r['citing']['set_id']}` v{r['citing']['version']} doc `{r['citing']['document_id']}` "
                  f"published {r['citing']['published_date']}; product `{r['citing']['product_code']}` ({r['citing']['product_kind']}), "
                  f"graph status {r['citing']['status_in_graph']}",
                  f"- cited element: `{r['cited_element']}`",
                  f"- citing product: {json.dumps(r['citing_product'], default=str)}",
                  f"- source code: {json.dumps(r['source_code'])}"
                  + (f"; diagnostic package prefix {r['diagnostic_package_prefix_5_4']}" if r.get("diagnostic_package_prefix_5_4") else ""),
                  f"- release matches ({len(r['release_matches'])}): "
                  + "; ".join(f"{m['set_id']} v{m['version']} {m['kind']} canonical={m['canonical']} status={m['status']}" for m in r["release_matches"][:12])]
        for cnd in r["candidates"]:
            lines += [f"- candidate `{cnd['set_id']}` v{cnd['version']} ({cnd['selection_class']}, published {cnd['published_date']}), status {cnd['status']}: "
                      f"product {json.dumps(cnd['product'], default=str)}; form same {cnd['form_same']}, active same {cnd['active_same']}",
                      f"  - MANUFACTURE scoped to the code in its XML: {json.dumps(cnd['manufacture_performances_scoped_to_code'])}",
                      f"  - graph MANUFACTURE edges: {json.dumps(cnd['graph_manufacture_edges'], default=str)}",
                      f"  - versions in release: {json.dumps(cnd['versions_in_release'])}",
                      f"  - candidate cites a source: {json.dumps(cnd['candidate_cites_source'])}"
                      + (f"; next hop {json.dumps(cnd.get('next_hop'))}" if cnd.get("next_hop") is not None else "")]
        lines += [f"- temporal: {json.dumps(r['temporal'])}",
                  f"- checks: {json.dumps(r['checks'])}",
                  f"- mechanical result: **{r['mechanical_result']}**" + (f" (failed: {', '.join(r['failed_checks'])})" if r["failed_checks"] else ""), ""]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint")
    a = ap.parse_args()
    text = MANIFEST.read_bytes()
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if hashlib.sha256(text).hexdigest() != freeze["sha256"]:
        sys.exit("sample_manifest.json does not match its FREEZE hash; refusing to check an unfrozen sample")
    manifest = json.loads(text)
    with db.connect(a.db) as c:
        results = [check_one(c, s) for s in manifest["sample"]]
    OUT.write_text(json.dumps({"generated_at": raw.utc_now(), "manifest_sha256": freeze["sha256"], "results": results},
                              indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    DIGEST.write_text(digest(results), encoding="utf-8", newline="\n")
    tally = {}
    for r in results:
        tally.setdefault(r["stratum"], {}).setdefault(r["mechanical_result"], 0)
        tally[r["stratum"]][r["mechanical_result"]] += 1
    print(json.dumps(tally, indent=1))


if __name__ == "__main__":
    sys.exit(main())
