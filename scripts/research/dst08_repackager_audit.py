"""DST-08 Phase 5: audit of repackager MANUFACTURE assertions and the labeler-as-manufacturer contradictions.

Population (exact, database-wide, graph build 8): every product-scoped MANUFACTURE (C43360) edge whose establishment
lists REPACK (C73606) or RELABEL (C73607) for the same product in the same document — 139 products, 19 DIRECT edges.
Plus the three labeler-as-manufacturer contradictions from the coverage diagnosis (S077, S098, S104).

For every assertion the script re-reads the label from the release (hash-verified) and records, without using names,
addresses or product similarity to decide anything:

  - the establishment's operations for the product as written in the XML, and its edge in the graph;
  - FDA's registration record for the DUNS: the registered business operations (an FDA source independent of the SPL);
  - the product's source NDC reference, if any, and whether the claimed DUNS is itself a MANUFACTURE establishment
    of the resolved source product in the source's own label;
  - whether the DUNS asserts MANUFACTURE without REPACK/RELABEL for other products (acts as a maker elsewhere);
  - label text statements ("Manufactured by/for", "Repackaged by", "Distributed by", ...), as text only.

Mechanical class (stated rule, not a judgment):
  CORROBORATED_BY_SOURCE   the claimed DUNS is a MANUFACTURE establishment of the resolved source product in the
                           source's own label
  REGISTRATION_ONLY        the FDA registration of the DUNS lists MANUFACTURE and no resolved source contradicts it; this
                           is establishment-level and does not show that this product is made there
  POTENTIALLY_ERRONEOUS    the FDA registration lists operations without MANUFACTURE and the source does not corroborate,
                           or a resolved source names other MANUFACTURE sites and the registration does not list MANUFACTURE
  AMBIGUOUS                anything else (no registration operations and no resolved source, or the two disagree)
"POTENTIALLY_ERRONEOUS" means the assertion is not supported as a physical-manufacture claim for this product. 21 CFR
207.1 defines manufacture separately from repack and relabel for listing purposes, but counts contract packers and
labelers as manufacturers, so no assertion here is called false.

  python -I scripts/research/dst08_repackager_audit.py --db fineprint
Output: docs/research/dst08/repackager_manufacture_audit.json and .csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "research"))
import dst08_check_sample as chk  # noqa: E402
import verify_audit_sample as raw  # noqa: E402
from fineprint import db  # noqa: E402

OUT_JSON = REPO / "docs" / "research" / "dst08" / "repackager_manufacture_audit.json"
OUT_CSV = REPO / "docs" / "research" / "dst08" / "repackager_manufacture_audit.csv"
REFERENCES = raw.DATA / "research" / "dst08" / "references.csv"
CONTRADICTIONS = {"S077": 65978, "S098": 24855, "S104": 21898}
WORST = ["CORROBORATED_BY_SOURCE", "REGISTRATION_ONLY", "AMBIGUOUS", "POTENTIALLY_ERRONEOUS"]
STATEMENT = re.compile(r"\b(manufactured|mfd\.?|mfg\.?|made|repackaged|repacked|relabeled|relabelled|distributed|packaged|"
                       r"marketed)\s+(by|for|in)\b[:\s]*(.{0,110})", re.I)

POPULATION_SQL = """
SELECT DISTINCT e.assertion_pk, e.report_product_pk, a.document_pk, a.establishment_org_pk, e.duns, e.confidence,
       e.confidence_reasons, e.identity_status, e.fei, e.loc, e.product_ndc_raw
FROM national.operation_edge e JOIN national.operation_assertion a ON a.assertion_pk = e.assertion_pk
WHERE e.is_manufacture AND e.product_scope = 'product' AND EXISTS (
    SELECT 1 FROM national.operation_assertion b WHERE b.document_pk = a.document_pk
      AND b.establishment_org_pk = a.establishment_org_pk AND b.operation_code IN ('C73606', 'C73607')
      AND b.product_pk = a.product_pk)
ORDER BY e.report_product_pk, e.assertion_pk"""


def registration(c, duns: str | None) -> dict:
    if not duns:
        return {"identity_status": None, "operations": None, "lists_manufacture": None}
    row = c.execute(
        """SELECT di.status, di.fei, di.evidence_as_of, di.evidence_expiration, rr.operations_raw, f.kind, f.name
           FROM national.duns_identity di LEFT JOIN national.registration_record rr ON rr.registration_pk = di.registration_pk
           LEFT JOIN national.source_file f ON f.source_file_id = rr.source_file_id WHERE di.duns = %s""", (duns,)).fetchone()
    every = sorted({r[0] for r in c.execute(
        "SELECT rr.operations_raw FROM national.registration_record rr WHERE rr.duns = %s AND rr.operations_raw IS NOT NULL",
        (duns,)).fetchall()})
    ops = row[4] if row else None
    tokens = {t.strip().upper() for t in (ops or "").split(";") if t.strip()}
    return {"identity_status": row[0] if row else "NOT_IN_IDENTITY_TABLE", "fei": row[1] if row else None,
            "evidence_as_of": row[2] if row else None, "expiration": row[3] if row else None,
            "evidence_file_kind": row[5] if row else None, "operations": ops, "operations_all_snapshots": every,
            "lists_manufacture": ("MANUFACTURE" in tokens) if ops else None}


def maker_elsewhere(c, duns: str | None, product_pk: int) -> dict:
    if not duns:
        return {"products": 0, "labelers": 0}
    row = c.execute(
        """SELECT count(DISTINCT e.report_product_pk), count(DISTINCT lab.duns)
           FROM national.operation_edge e JOIN national.operation_assertion a ON a.assertion_pk = e.assertion_pk
           LEFT JOIN national.organization_mention lab ON lab.document_pk = e.document_pk AND lab.role = 'labeler'
           WHERE e.duns = %s AND e.is_manufacture AND e.product_scope = 'product' AND e.report_product_pk <> %s
             AND NOT EXISTS (SELECT 1 FROM national.operation_assertion b WHERE b.document_pk = a.document_pk
                 AND b.establishment_org_pk = a.establishment_org_pk AND b.operation_code IN ('C73606', 'C73607')
                 AND b.product_pk = a.product_pk)""", (duns, product_pk)).fetchone()
    return {"products": row[0], "labelers": row[1]}


def source_check(c, refs: dict, set_id: str, version: int, product_pk: int, duns: str | None) -> dict:
    mine = [r for r in refs.get((set_id.lower(), version), []) if r["product_pk"] == str(product_pk)]
    if not mine:
        return {"cites_source": False, "verdict": "NO_SOURCE_REFERENCE"}
    out = {"cites_source": True, "references": [], "verdict": "NO_RESOLVED_SOURCE"}
    for r in mine:
        entry = {"source_code": r["src_code"], "validity": r["validity"], "resolution": r["resolution"],
                 "candidates": []}
        for pk in [p for p in (r["candidate_product_pks"] or "").split(";") if p]:
            mfg = sorted({x[0] for x in c.execute(
                "SELECT duns FROM national.operation_edge WHERE report_product_pk = %s AND is_manufacture "
                "AND product_scope = 'product' AND duns IS NOT NULL", (int(pk),)).fetchall()})
            entry["candidates"].append({"product_pk": int(pk), "manufacture_duns": mfg, "claimed_duns_listed": duns in mfg})
        if r["resolution"] == "RESOLVED" and entry["candidates"]:
            cand = entry["candidates"][0]
            out["verdict"] = "CORROBORATES" if cand["claimed_duns_listed"] else (
                "CONTRADICTS" if cand["manufacture_duns"] else "SOURCE_HAS_NO_MANUFACTURE_SITE")
        out["references"].append(entry)
    return out


def classify(reg_mfg, src) -> str:
    if src == "CORROBORATES":
        return "CORROBORATED_BY_SOURCE"
    if reg_mfg is True and src != "CONTRADICTS":
        return "REGISTRATION_ONLY"
    if (reg_mfg is False and src != "CORROBORATES") or (src == "CONTRADICTS" and reg_mfg is not True):
        return "POTENTIALLY_ERRONEOUS"
    return "AMBIGUOUS"


def statements(root) -> list[str]:
    text = " ".join(" ".join(root.itertext()).split())
    seen, out = set(), []
    for m in STATEMENT.finditer(text):
        s = m.group(0)[:150]
        if s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out[:10]


def establishment_ops(root, duns: str | None, code: str | None) -> list[str]:
    return sorted({p["code"] for p in raw.performances(root) if p["in_author"] and duns in (p["duns"] or [])
                   and code in p["product_codes"]})


def audit_product(c, refs, product_pk: int, assertions: list, xml_cache: dict) -> dict:
    p = c.execute("""SELECT p.ndc_raw, p.name, p.kind, s.manufacturing_status, s.evidence_status, s.set_id, s.version,
                            p.document_pk
                     FROM national.product p JOIN national.v_product_manufacturing_status s USING (product_pk)
                     WHERE p.product_pk = %s""", (product_pk,)).fetchone()
    ndc_raw, name, kind, status, evidence, set_id, version, doc_pk = p
    if doc_pk not in xml_cache:
        loc = chk.doc_location(c, doc_pk)
        xml_cache[doc_pk] = (loc, chk.open_xml(loc[0], loc[1], loc[2], loc[3], loc[4])[1])
    loc, root = xml_cache[doc_pk]
    labelers = [list(r) for r in c.execute("SELECT name, duns FROM national.organization_mention WHERE document_pk = %s "
                                           "AND role = 'labeler' ORDER BY loc", (doc_pk,)).fetchall()]
    rows = []
    for (a_pk, _, _, _, duns, conf, reasons, ident, fei, a_loc, code) in assertions:
        el = chk.find_by_loc(root, a_loc)
        reg = registration(c, duns)
        src = source_check(c, refs, set_id, version, product_pk, duns)
        rows.append({
            "assertion_pk": a_pk, "duns": duns, "fei": fei, "edge_confidence": conf, "edge_reasons": list(reasons),
            "identity_status": ident, "assertion_loc": a_loc, "assertion_found_in_xml": el is not None,
            "operations_for_product_in_xml": establishment_ops(root, duns, code),
            "establishment_is_labeler": any(duns and duns == lab[1] for lab in labelers),
            "registration": reg, "maker_elsewhere": maker_elsewhere(c, duns, product_pk), "source": src,
            "mechanical_class": classify(reg["lists_manufacture"], src["verdict"]),
        })
    return {"product_pk": product_pk, "ndc": ndc_raw, "name": name, "kind": kind, "graph_status": status,
            "evidence_status": evidence, "set_id": set_id, "version": version, "document_id": loc[8],
            "published_date": loc[7], "release_part": loc[0], "member": loc[1], "xml_sha256": loc[4],
            "labelers": labelers, "label_statements": statements(root), "assertions": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint")
    a = ap.parse_args()
    refs: dict = {}
    for r in csv.DictReader(REFERENCES.read_text(encoding="utf-8").splitlines()):
        refs.setdefault((r["set_id"].lower(), int(r["version"])), []).append(r)
    with db.connect(a.db) as c:
        pop: dict[int, list] = {}
        for row in c.execute(POPULATION_SQL).fetchall():
            pop.setdefault(row[1], []).append(row)
        cache: dict = {}
        products = [audit_product(c, refs, pk, rows, cache) for pk, rows in sorted(pop.items())]
        contradictions = {}
        for sid, pk in CONTRADICTIONS.items():
            mfg = c.execute("SELECT assertion_pk, report_product_pk, document_pk, NULL, duns, confidence, confidence_reasons, "
                            "identity_status, fei, loc, product_ndc_raw FROM national.operation_edge "
                            "WHERE report_product_pk = %s AND is_manufacture ORDER BY assertion_pk", (pk,)).fetchall()
            contradictions[sid] = audit_product(c, refs, pk, mfg, cache)
        build = c.execute("SELECT max(build_id) FROM national.graph_build WHERE status = 'completed'").fetchone()[0]
        # Context for a possible future rule (not applied): DIRECT edges whose establishment's registration evidence
        # row lists business operations without MANUFACTURE.
        unregistered_op = [list(r) for r in c.execute(
            """SELECT coalesce(rr.operations_raw, '(none)'), count(*), count(DISTINCT e.duns), count(DISTINCT e.report_product_pk)
               FROM national.operation_edge e JOIN national.duns_identity di ON di.duns = e.duns
               LEFT JOIN national.registration_record rr ON rr.registration_pk = di.registration_pk
               WHERE e.is_manufacture AND e.confidence = 'DIRECT' AND NOT ('MANUFACTURE' = ANY (
                   SELECT upper(trim(t)) FROM unnest(string_to_array(coalesce(rr.operations_raw, ''), ';')) t))
               GROUP BY 1 ORDER BY 2 DESC, 1""").fetchall()]
        all_direct = c.execute("SELECT count(*), count(DISTINCT duns), count(DISTINCT report_product_pk) "
                               "FROM national.operation_edge WHERE is_manufacture AND confidence = 'DIRECT'").fetchone()
    edges = [r for p in products for r in p["assertions"]]
    tally = {
        "products": len(products), "edges": len(edges),
        "direct_edges": sum(r["edge_confidence"] == "DIRECT" for r in edges),
        "establishments": len({r["duns"] for r in edges}),
        "by_class": dict(Counter(r["mechanical_class"] for r in edges)),
        "direct_by_class": dict(Counter(r["mechanical_class"] for r in edges if r["edge_confidence"] == "DIRECT")),
        "by_confidence": dict(Counter(r["edge_confidence"] for r in edges)),
        "source_verdicts": dict(Counter(r["source"]["verdict"] for r in edges)),
        "registration_lists_manufacture": dict(Counter(str(r["registration"]["lists_manufacture"]) for r in edges)),
        "products_by_worst_class": dict(Counter(max((r["mechanical_class"] for r in p["assertions"]), key=WORST.index)
                                                for p in products)),
    }
    out = {"generated_at": raw.utc_now(), "graph_build": build, "rule": __doc__.split("Mechanical class")[1].split("  python")[0],
           "tally": tally,
           "direct_edges_whose_registration_lists_no_manufacture": {
               "all_direct_manufacture": {"edges": all_direct[0], "duns": all_direct[1], "products": all_direct[2]},
               "edges": sum(r[1] for r in unregistered_op),
               "by_registered_operations": [{"operations": r[0], "edges": r[1], "duns": r[2], "products": r[3]}
                                            for r in unregistered_op]},
           "products": products, "contradictions": contradictions}
    OUT_JSON.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["case", "product_pk", "ndc", "name", "graph_status", "set_id", "version", "duns", "edge_confidence",
                    "operations_in_xml", "establishment_is_labeler", "registration_operations", "registration_lists_manufacture",
                    "maker_elsewhere_products", "source_verdict", "mechanical_class", "label_statements"])
        for case, p in [("REPACK_MFG", p) for p in products] + list(contradictions.items()):
            for r in p["assertions"]:
                w.writerow([case, p["product_pk"], p["ndc"], p["name"], p["graph_status"], p["set_id"], p["version"], r["duns"],
                            r["edge_confidence"], ";".join(r["operations_for_product_in_xml"]), r["establishment_is_labeler"],
                            r["registration"]["operations"], r["registration"]["lists_manufacture"],
                            r["maker_elsewhere"]["products"], r["source"]["verdict"], r["mechanical_class"],
                            " | ".join(p["label_statements"][:4])])
    print(json.dumps(tally, indent=1))


if __name__ == "__main__":
    sys.exit(main())
