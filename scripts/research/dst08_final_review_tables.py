"""DST-08 final validation, Phase 4: the AI-assisted validation table and the human adjudication worksheet.

  python -I scripts/research/dst08_final_review_tables.py

Inputs:
  final_cases_evidence.json            the frozen cases re-derived from original evidence (dst08_final_cases.py)
  final_ai_verdicts.json               the AI-assisted reading of each case, written after reading the evidence digest:
                                       verdict, risk, rationale, and whether a person must adjudicate it before production
  registration_operations_audit.json   the DIRECT edges whose registration lacks MANUFACTURE (Phase 3)
Outputs:
  final_ai_validation.csv              one row per case, every citation filled from the evidence, never typed by hand;
                                       every row says it is AI-assisted and not a human adjudication
  final_human_worksheet.csv            the minimum set a person must adjudicate before production, with the human
                                       columns blank. Nothing here fills or signs a human verdict.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DST08 = REPO / "docs" / "research" / "dst08"
AI_NOTE = "AI-assisted reading of the re-derived evidence (Claude); not a human adjudication"
HUMAN_COLUMNS = ["human_source_identity_confirmed", "human_physical_description_matches_at_relevant_date",
                 "human_manufacturing_statement_from_correct_source_and_version", "human_verdict", "human_reviewer",
                 "human_review_date", "human_note"]


def cite(doc: dict | None) -> str:
    if not doc:
        return ""
    return (f"set {doc['set_id']} v{doc['version']} doc {doc.get('document_id') or '?'} published "
            f"{doc.get('published_date') or doc.get('published_at') or '?'} xml sha256 {(doc.get('xml_sha256') or '')[:16]}")


def main():
    ev = {r["case_id"]: r for r in json.loads((DST08 / "final_cases_evidence.json").read_text(encoding="utf-8"))["results"]}
    verdicts = json.loads((DST08 / "final_ai_verdicts.json").read_text(encoding="utf-8"))
    missing = sorted(set(ev) - set(verdicts["cases"]))
    if missing:
        raise SystemExit(f"cases without an AI-assisted reading: {missing}")
    rows, human = [], []
    for cid, r in ev.items():
        v, p, cz = verdicts["cases"][cid], r["prototype"], r["citing"]
        vc = r.get("version_check_independent") or {}
        cands = r["candidates"]
        src = cands[0] if len(cands) == 1 else None
        rows.append({
            "case_id": cid, "stratum": r["stratum"], "detail": r["detail"],
            "citing_ndc": cz["product"]["code"], "citing_name": cz["product"]["name"], "citing_form": cz["product"]["form_name"],
            "citing_citation": cite(cz), "cited_element_loc": cz["element_loc"], "source_code": r["source_code"]["raw"],
            "source_citation": cite(src) if src else f"{len(cands)} candidates: " + " | ".join(cite(c) for c in cands),
            "source_sites_in_label": ";".join(sorted({u for s in (src or {}).get("manufacture_sites", []) for u in s["duns"]})),
            "applicable_version_citation": (f"set {src['set_id']} v{vc.get('applicable_version')} doc "
                                            f"{vc.get('applicable_document_id')} published {vc.get('applicable_published_at')} "
                                            f"xml sha256 {(vc.get('applicable_xml_sha256') or '')[:16]}") if vc else "",
            "relevant_date": vc.get("relevant_date", ""),
            "v1": f"{p['v1_status']} {';'.join(p['v1_reasons'] or [])}".strip(),
            "physical_now": f"{p['physical_outcome'] or ''} {';'.join(p['physical_differing'] or [])}".strip(),
            "v2": f"{p['v2_status']} {';'.join(p['v2_reasons'] or [])}".strip(), "v2_class": p["v2_class"] or "",
            "v2_evidence_sites": ";".join(p["v2_evidence_sites"] or []),
            "independently_reproduced": ";".join(f"{k}={v}" for k, v in r["reproduced"].items() if isinstance(v, bool)),
            "ai_verdict": v["verdict"], "risk": v["risk"], "ai_rationale": v["rationale"],
            "human_required": v["human_required"], "reviewer": AI_NOTE,
        })
        if v["human_required"]:
            human.append({"item_id": cid, "kind": "source link", "question": v["human_question"],
                          "citing": f"{cz['product']['code']} {cz['product']['name']}; {cite(cz)}; element {cz['element_loc']}",
                          "source": rows[-1]["source_citation"], "relevant_version": rows[-1]["applicable_version_citation"],
                          "prototype": f"v1 {rows[-1]['v1']}; v2 {rows[-1]['v2']} {rows[-1]['v2_class']}".strip(),
                          "ai_reading": f"{v['verdict']}: {v['rationale']}", **{k: "" for k in HUMAN_COLUMNS}})
    reg = json.loads((DST08 / "registration_operations_audit.json").read_text(encoding="utf-8"))
    for item in verdicts.get("direct_edges", []):
        e = next(x for x in reg["edges"] if x["assertion_pk"] == item["assertion_pk"])
        human.append({"item_id": f"DIRECT-{e['assertion_pk']}", "kind": "DIRECT edge (registration lacks MANUFACTURE)",
                      "question": item["human_question"],
                      "citing": f"{e['product_ndc']} {e['product_name']}; set {e['set_id']} v{e['version']} doc "
                                f"{e['document_id']} published {e['published_date']}; element {e['spl_element_loc']}",
                      "source": f"DUNS {e['duns']}; registration {e['evidence_registration']['file']} line "
                                f"{e['evidence_registration']['line_no']}: {e['evidence_registration']['operations']}",
                      "relevant_version": f"snapshot nearest the label: {e['snapshot_nearest_label']}",
                      "prototype": f"DIRECT (unchanged); audit class {e['class']}",
                      "ai_reading": item["ai_reading"], **{k: "" for k in HUMAN_COLUMNS}})
    for name, data in (("final_ai_validation.csv", rows), ("final_human_worksheet.csv", human)):
        with (DST08 / name).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(data)
    print(json.dumps({"cases": len(rows), "human_items": len(human),
                      "verdicts": {k: sum(r["ai_verdict"] == k for r in rows) for k in sorted({r["ai_verdict"] for r in rows})}}))


if __name__ == "__main__":
    sys.exit(main())
