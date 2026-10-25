"""DST-08 final validation, Phase 3: DIRECT MANUFACTURE edges whose FDA registration does not list MANUFACTURE.

  python -I scripts/research/dst08_registration_audit.py --db fineprint

Population (exact, graph build 8): every DIRECT MANUFACTURE edge whose identity evidence row (the registration line
behind national.duns_identity) lists business operations without MANUFACTURE. No DIRECT classification is changed;
this script only reads.

For every edge it records, without using names or addresses to decide anything:
  - the SPL statement: the performance element re-read verbatim from the release (hash-verified), the operation code,
    and every operation the same establishment lists for the product in that label;
  - the product's dosage form and marketing category, and the label version's publication date;
  - every FDA registration snapshot loaded for the DUNS (current 2026-10-19 and the archived 2024-12-23, 2025-12-05
    and 2026-08-21 files), with its date, operations and expiration.

Classes (first that applies; the rule is fixed here, before the classes were counted):
  EXPLAINED_REGISTRATION_CHANGED  a snapshot lists MANUFACTURE, and the snapshot nearest the label's publication date
                                  (the latest on or before it; if none, the earliest after it) lists MANUFACTURE. The
                                  label agreed with the registration in force near its publication; the current
                                  registration no longer lists MANUFACTURE, so the current DIRECT edge rests on an
                                  operation the establishment no longer registers.
  EXPLAINED_MEDICAL_GAS_FILLER    the product's dosage form is GAS and no snapshot lists anything but TRANSFILL,
                                  REPACK, RELABEL, LABEL or PACK. Medical gases need no source NDC (21 CFR 207.53(b));
                                  a product without a source must list a manufacture operation (SPL IG 4.1.4.15: API
                                  Manufacture, Manufacture or PET Drug Production; Transfill is not one); and medical-gas
                                  CGMP counts packaging and labelling as manufacture (21 CFR 213.3(b)(11)) while naming
                                  the gas's producer separately as the original manufacturer (213.3(b)(13)). The edge
                                  names a filling site, not where the gas was produced.
  EXPLAINED_PET_PRODUCTION        a snapshot lists POSITRON EMISSION TOMOGRAPHY DRUG PRODUCTION: the IG counts it as a
                                  manufacture operation (4.1.4.15) and 21 CFR 212.1 defines PET production as including
                                  manufacturing.
  CONFLICTING                     no snapshot lists MANUFACTURE and none of the above applies: the label's MANUFACTURE
                                  (C43360) contradicts every registration of the establishment (API-only, pack or label
                                  only, or repack or relabel only). 21 CFR 207.1 and 210.3(b)(12) use "manufacture" in a
                                  broad sense, but the listing vocabulary gives those operations their own codes.
  UNRESOLVED                      anything else.

Output: docs/research/dst08/registration_operations_audit.json and .csv.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "research"))
import dst08_check_sample as chk  # noqa: E402
import verify_audit_sample as raw  # noqa: E402
from fineprint import db  # noqa: E402

OUT_JSON = REPO / "docs" / "research" / "dst08" / "registration_operations_audit.json"
OUT_CSV = REPO / "docs" / "research" / "dst08" / "registration_operations_audit.csv"
GAS_FILL = {"TRANSFILL", "REPACK", "RELABEL", "LABEL", "PACK"}
PET = "POSITRON EMISSION TOMOGRAPHY DRUG PRODUCTION"
SOURCES = {
    "21 CFR 207.1": "ecfr_21_207_1.xml (eCFR versioner, 2026-10-01)",
    "21 CFR 207.53(b)": "ecfr_21_207_53.xml (eCFR versioner, 2026-10-01)",
    "21 CFR 210.3(b)(12)": "ecfr_21_210_3.html (eCFR renderer, 2026-10-21) sha256 097f8a8d8c95453442c3b9f64a409550e6c18014c1b3125a5a3034bc7a17e677",
    "21 CFR 212.1": "ecfr_21_212_1.html (eCFR renderer, 2026-10-21) sha256 8e67980ff4348ba52671da14f593a838d3747fab5432ba15dbee676ce0a61ebe",
    "21 CFR 213.3(b)(11), (13)": "ecfr_21_213_3.html (eCFR renderer, 2026-10-21) sha256 8f8213829a7f0675cba0c60809ff5268fdc1ad77d856f09b71e761ef322a6089",
    "SPL IG 4.1.4.15, 6.1.6.8": "spl_ig_84201.pdf (FDA, December 2023) sha256 9845e23cb51ee2e7f493b17ed5729b2bc946040244e6f6da2d78c9491a41f983",
}

EDGES_SQL = """
SELECT e.assertion_pk, e.document_pk, e.report_product_pk, e.product_ndc_raw, e.duns, e.fei, e.loc, e.operation_code,
       e.confidence_reasons, p.name, p.dosage_form, p.approvals, rr.registration_pk, rf.name, rr.line_no,
       rr.operations_raw, di.evidence_as_of, di.evidence_expiration
FROM national.operation_edge e
JOIN national.duns_identity di ON di.duns = e.duns
LEFT JOIN national.registration_record rr ON rr.registration_pk = di.registration_pk
LEFT JOIN national.source_file rf ON rf.source_file_id = rr.source_file_id
JOIN national.product p ON p.product_pk = e.report_product_pk
WHERE e.is_manufacture AND e.confidence = 'DIRECT' AND NOT ('MANUFACTURE' = ANY (
    SELECT upper(trim(t)) FROM unnest(string_to_array(coalesce(rr.operations_raw, ''), ';')) t))
ORDER BY e.duns, e.product_ndc_raw, e.assertion_pk"""

SNAPSHOTS_SQL = """
SELECT f.kind, f.name, f.release_label, rr.line_no, rr.operations_raw, rr.expiration_date, rr.exclusion_flag
FROM national.registration_record rr JOIN national.source_file f USING (source_file_id)
WHERE rr.duns = %s ORDER BY f.release_label, f.name, rr.line_no"""


def ops(s: str | None) -> set[str]:
    return {t.strip().upper() for t in (s or "").split(";") if t.strip()}


def nearest(snapshots: list[dict], date: str | None) -> dict | None:
    """The snapshot in force nearest the label's publication: the latest on or before it, else the earliest after."""
    regs = [s for s in snapshots if s["kind"].startswith("fda_decrs_registration")]
    if not regs or not date:
        return None
    before = [s for s in regs if s["as_of"] <= date]
    return max(before, key=lambda s: s["as_of"]) if before else min(regs, key=lambda s: s["as_of"])


def classify(form: str | None, snapshots: list[dict], published: str | None) -> tuple[str, list[str]]:
    every = [ops(s["operations"]) for s in snapshots if s["kind"].startswith("fda_decrs_registration")]
    union = set().union(*every) if every else set()
    near = nearest(snapshots, published)
    also = []
    if (form or "").upper() == "GAS" and union and (union - {"MANUFACTURE"}) <= GAS_FILL:
        also.append("EXPLAINED_MEDICAL_GAS_FILLER")
    if PET in union:
        also.append("EXPLAINED_PET_PRODUCTION")
    if "MANUFACTURE" in union and near and "MANUFACTURE" in ops(near["operations"]):
        return "EXPLAINED_REGISTRATION_CHANGED", also
    if "EXPLAINED_MEDICAL_GAS_FILLER" in also:
        return "EXPLAINED_MEDICAL_GAS_FILLER", [a for a in also if a != "EXPLAINED_MEDICAL_GAS_FILLER"]
    if PET in union:
        return "EXPLAINED_PET_PRODUCTION", [a for a in also if a != "EXPLAINED_PET_PRODUCTION"]
    if every and "MANUFACTURE" not in union:
        return "CONFLICTING", also
    return "UNRESOLVED", also


def conflict_kind(union: set[str]) -> str | None:
    if "API MANUFACTURE" in union:
        return "API_MANUFACTURE_REGISTERED" + ("_WITH_LABEL_PACK" if union & {"LABEL", "PACK"} else "")
    if union & {"LABEL", "PACK"} and not union & {"REPACK", "RELABEL"}:
        return "LABEL_OR_PACK_ONLY"
    if union & {"REPACK", "RELABEL"}:
        return "REPACK_OR_RELABEL_REGISTERED"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint")
    a = ap.parse_args()
    rows, cache = [], {}
    with db.connect(a.db) as c:
        build = c.execute("SELECT max(build_id) FROM national.graph_build WHERE status = 'completed'").fetchone()[0]
        edges = c.execute(EDGES_SQL).fetchall()
        for (a_pk, doc_pk, prod_pk, ndc_raw, duns, fei, loc, op_code, reasons, name, form, approvals, reg_pk, reg_file,
             reg_line, reg_ops, as_of, expiration) in edges:
            if doc_pk not in cache:
                d = chk.doc_location(c, doc_pk)
                cache[doc_pk] = (d, chk.open_xml(d[0], d[1], d[2], d[3], d[4])[1])
            d, root = cache[doc_pk]
            el = chk.find_by_loc(root, loc)
            same_est = sorted({p["code"] for p in raw.performances(root)
                               if p["in_author"] and duns in (p["duns"] or []) and ndc_raw in p["product_codes"]})
            snaps = [{"kind": k, "file": f, "as_of": lbl, "line_no": ln, "operations": o,
                      "expiration": exp.isoformat() if exp else None, "exclusion_flag": ex}
                     for k, f, lbl, ln, o, exp, ex in c.execute(SNAPSHOTS_SQL, (duns,)).fetchall()]
            published = d[7].isoformat() if d[7] else None
            cls, also = classify(form, snaps, published)
            union = set().union(*[ops(s["operations"]) for s in snaps if s["kind"].startswith("fda_decrs_registration")])
            near = nearest(snaps, published)
            alt = c.execute(
                """SELECT count(*) FILTER (WHERE e2.confidence = 'DIRECT') FROM national.operation_edge e2
                   WHERE e2.report_product_pk = %s AND e2.is_manufacture AND e2.assertion_pk <> %s""",
                (prod_pk, a_pk)).fetchone()[0]
            rows.append({
                "assertion_pk": a_pk, "product_ndc": ndc_raw, "product_name": name, "dosage_form": form,
                "marketing_category": (approvals or [{}])[0].get("category") if approvals else None,
                "set_id": d[5], "version": d[6], "document_id": d[8], "published_date": published,
                "release_part": d[0], "member": d[1], "xml_sha256": d[4],
                "duns": duns, "fei": fei, "spl_operation_code": op_code, "spl_element_loc": loc,
                "spl_element": chk.verbatim(el) if el is not None else None,
                "establishment_operations_for_product_in_label": same_est,
                "evidence_registration": {"file": reg_file, "line_no": reg_line, "operations": reg_ops,
                                          "as_of": as_of.isoformat() if as_of else None,
                                          "expiration": expiration.isoformat() if expiration else None},
                "registration_snapshots": snaps,
                "snapshot_nearest_label": {k: near[k] for k in ("file", "as_of", "operations")} if near else None,
                "registered_operations_any_snapshot": sorted(union),
                "class": cls, "also_applies": also,
                "conflict_kind": conflict_kind(union) if cls == "CONFLICTING" else None,
                "other_direct_manufacture_edges_for_product": alt,
            })
    tally = Counter(r["class"] for r in rows)
    out = {
        "generated_at": raw.utc_now(), "graph_build": build, "rule": __doc__.split("Classes")[1].split("Output:")[0],
        "regulatory_sources": SOURCES,
        "tally": {
            "edges": len(rows), "establishments": len({r["duns"] for r in rows}),
            "products": len({r["product_ndc"] for r in rows}),
            "by_class": dict(sorted(tally.items())),
            "by_class_establishments": {k: len({r["duns"] for r in rows if r["class"] == k}) for k in sorted(tally)},
            "conflicting_by_kind": dict(Counter(r["conflict_kind"] for r in rows if r["class"] == "CONFLICTING")),
            "conflicting_products_with_no_other_direct_edge": sorted(
                {r["product_ndc"] for r in rows if r["class"] == "CONFLICTING"
                 and r["other_direct_manufacture_edges_for_product"] == 0}),
        },
        "edges": rows,
    }
    OUT_JSON.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["assertion_pk", "product_ndc", "product_name", "dosage_form", "marketing_category", "set_id",
                    "version", "published_date", "duns", "spl_operation_code", "operations_in_label",
                    "registered_operations_current", "snapshot_nearest_label", "registered_operations_any_snapshot",
                    "class", "also_applies", "conflict_kind", "other_direct_edges_for_product"])
        for r in rows:
            n = r["snapshot_nearest_label"]
            w.writerow([r["assertion_pk"], r["product_ndc"], r["product_name"], r["dosage_form"], r["marketing_category"],
                        r["set_id"], r["version"], r["published_date"], r["duns"], r["spl_operation_code"],
                        ";".join(r["establishment_operations_for_product_in_label"]),
                        r["evidence_registration"]["operations"], f"{n['as_of']}: {n['operations']}" if n else "",
                        "; ".join(r["registered_operations_any_snapshot"]), r["class"], ";".join(r["also_applies"]),
                        r["conflict_kind"] or "", r["other_direct_manufacture_edges_for_product"]])
    print(json.dumps(out["tally"], indent=1))


if __name__ == "__main__":
    sys.exit(main())
