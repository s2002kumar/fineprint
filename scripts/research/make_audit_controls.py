"""Replacement negative controls for the human audit (research workstream B2), frozen as a separate sample.

The original worksheet's C19/C20 (PACK or LABEL by Rocky Mount) are weak product-level negatives because the same
labels also assert MANUFACTURE by the same DUNS for the same product. They are retained as operation-level checks.
This script draws genuinely independent product-level negative controls from the current graph, each with an
explicit expectation and the premise that makes it a negative:

  N1 PACK without MANUFACTURE          N2 LABEL without MANUFACTURE        N3 ANALYSIS without MANUFACTURE
  N4 API MANUFACTURE only              N5 API site versus finished-dose site (different DUNS)
  N6 MANUFACTURE with no product scope (single-product label: the tempting case)
  N7 MANUFACTURE by an unresolved DUNS (NOT_FOUND)   N8 MANUFACTURE by a stale-registration DUNS

Every control's premise is re-checked in the raw XML by an independent walk (scripts/research/verify_audit_sample.py
helpers, which import nothing from fineprint), and the expectation is checked against the graph tables. The original
worksheet is not modified; this is a new, frozen file with its own seed and hash.

  python -I scripts/research/make_audit_controls.py --db fineprint
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import random
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "research"))
import verify_audit_sample as raw  # noqa: E402  independent XML helpers
from fineprint import config, db  # noqa: E402  database access only

SEED = "fineprint-audit-controls-v2-2026-10-22"
MFG, API = "C43360", "C82401"
DM = "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={set_id}"
FDA = "https://www.accessdata.fda.gov/spl/data/{docid}/{docid}.xml"

BASE = """
SELECT p.product_pk, s.set_id, s.selected_version AS version, d.document_id, d.xml_sha256, p.ndc_raw, p.name,
       d.member_name, d.xml_member_name, f.local_path, m.member_sha256, v.manufacturing_status, v.evidence_status,
       (SELECT count(*) FROM national.product q WHERE q.document_pk = p.document_pk AND q.kind = 'product') AS products_in_document
FROM national.product p
JOIN national.set_version_selection s ON s.document_pk = p.document_pk
JOIN national.spl_document d ON d.document_pk = p.document_pk
JOIN national.archive_member m ON m.document_pk = d.document_pk AND m.status = 'loaded'
JOIN national.source_file f ON f.source_file_id = m.source_file_id
JOIN national.v_product_manufacturing_status v ON v.product_pk = p.product_pk
WHERE p.kind = 'product' AND p.ndc_raw IS NOT NULL AND {where}
ORDER BY s.set_id, p.ndc_raw, p.loc
"""

NO_MFG_FOR_PRODUCT = """NOT EXISTS (SELECT 1 FROM national.operation_assertion a WHERE a.product_pk = p.product_pk
                              AND a.operation_code = 'C43360')"""


def op_only(code):
    return (f"""EXISTS (SELECT 1 FROM national.operation_assertion a WHERE a.product_pk = p.product_pk
                       AND a.operation_code = '{code}' AND a.duns IS NOT NULL) AND {NO_MFG_FOR_PRODUCT}
              AND v.manufacturing_status = 'NO_MANUFACTURE_EVIDENCE'""")


TYPES = [
    ("N1", "PACK without MANUFACTURE", 3, op_only("C84731"),
     "The product's only operations include PACK (C84731) by a DUNS; no establishment asserts MANUFACTURE (C43360) for it.",
     "No MANUFACTURE edge for the product; manufacturing_status NO_MANUFACTURE_EVIDENCE; the PACK edge has is_manufacture = false.",
     "A reader who treats the packer as the maker would wrongly assign a manufacturing site."),
    ("N2", "LABEL without MANUFACTURE", 3, op_only("C84732"),
     "The product's only operations include LABEL (C84732) by a DUNS; no MANUFACTURE for it.",
     "No MANUFACTURE edge; status NO_MANUFACTURE_EVIDENCE; LABEL edge is_manufacture = false.",
     "Treating the labeling site as the maker."),
    ("N3", "ANALYSIS without MANUFACTURE", 3, op_only("C25391"),
     "The product's only operations include ANALYSIS (C25391) by a DUNS; no MANUFACTURE for it.",
     "No MANUFACTURE edge; status NO_MANUFACTURE_EVIDENCE; ANALYSIS edge is_manufacture = false.",
     "Treating a testing laboratory as the maker."),
    ("N4", "API MANUFACTURE only", 3, op_only("C82401"),
     "An establishment asserts API MANUFACTURE (C82401) for the product; nobody asserts finished-dose MANUFACTURE (C43360).",
     "No MANUFACTURE edge; status NO_MANUFACTURE_EVIDENCE; the C82401 edge has is_manufacture = false and operation_name "
     "'API MANUFACTURE'.",
     "Collapsing the API (drug substance) maker into the finished-product maker."),
    ("N5", "API site versus finished-dose site", 3,
     f"""EXISTS (SELECT 1 FROM national.operation_assertion a WHERE a.product_pk = p.product_pk AND a.operation_code = '{API}'
                 AND a.duns IS NOT NULL AND NOT EXISTS (SELECT 1 FROM national.operation_assertion b
                 WHERE b.product_pk = p.product_pk AND b.operation_code = '{MFG}' AND b.duns = a.duns))
         AND EXISTS (SELECT 1 FROM national.operation_assertion b WHERE b.product_pk = p.product_pk
                 AND b.operation_code = '{MFG}' AND b.duns IS NOT NULL)""",
     "DUNS X asserts only API MANUFACTURE for the product while a different DUNS Y asserts MANUFACTURE.",
     "X is not among the product's MANUFACTURE DUNS; Y is. The API edge is_manufacture = false.",
     "Counting the API supplier as a second finished-dose site."),
    ("N6", "MANUFACTURE with no product scope (single-product label)", 3,
     f"""EXISTS (SELECT 1 FROM national.operation_assertion a WHERE a.document_pk = p.document_pk
                 AND a.product_scope = 'no_product_scope' AND a.operation_code = '{MFG}' AND a.duns IS NOT NULL)
         AND {NO_MFG_FOR_PRODUCT}
         AND (SELECT count(*) FROM national.product q WHERE q.document_pk = p.document_pk AND q.kind = 'product') = 1
         AND v.evidence_status = 'ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT'""",
     "The label has exactly one product, and an establishment asserts MANUFACTURE without naming any product code.",
     "The product's manufacturing_status is NO_MANUFACTURE_EVIDENCE (ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT); the "
     "MANUFACTURE edge is UNKNOWN with reason scope:no_product_scope and product_pk NULL.",
     "The tempting inference 'there is only one product, so the unscoped MANUFACTURE must be for it'. The rule does not "
     "make it; this control pins that."),
    ("N7", "MANUFACTURE by an unresolved DUNS", 3,
     f"""EXISTS (SELECT 1 FROM national.operation_assertion a JOIN national.duns_identity i ON i.duns = a.duns
                 WHERE a.product_pk = p.product_pk AND a.operation_code = '{MFG}' AND i.status = 'NOT_FOUND')
         AND NOT EXISTS (SELECT 1 FROM national.operation_assertion a JOIN national.duns_identity i ON i.duns = a.duns
                 WHERE a.product_pk = p.product_pk AND a.operation_code = '{MFG}' AND i.status <> 'NOT_FOUND')""",
     "The only MANUFACTURE assertion for the product names a DUNS absent from every loaded FDA registration file.",
     "manufacturing_status UNKNOWN_SITE; the edge is UNKNOWN with reason identity:NOT_FOUND; no FEI; never DIRECT.",
     "Promoting an unregistered DUNS to a physical site on the strength of the SPL alone."),
    ("N8", "MANUFACTURE by a stale-registration DUNS", 2,
     f"""EXISTS (SELECT 1 FROM national.operation_assertion a JOIN national.duns_identity i ON i.duns = a.duns
                 WHERE a.product_pk = p.product_pk AND a.operation_code = '{MFG}' AND i.status = 'STALE_REGISTERED')
         AND NOT EXISTS (SELECT 1 FROM national.operation_assertion a JOIN national.duns_identity i ON i.duns = a.duns
                 WHERE a.product_pk = p.product_pk AND a.operation_code = '{MFG}' AND i.status <> 'STALE_REGISTERED')""",
     "The only MANUFACTURE assertion names a DUNS listed in an archived registration file but not the current one.",
     "manufacturing_status TENTATIVE; the edge is TENTATIVE with reason identity:STALE_REGISTERED; never DIRECT.",
     "Reporting a site whose registration has lapsed as currently confirmed."),
]


def raw_xml(local_path: str, member: str, xml_member: str, member_sha: str, xml_sha: str) -> bytes:
    with zipfile.ZipFile(config.data_dir() / local_path) as outer:
        data = outer.read(member)
    assert raw.sha256(data) == member_sha, "member hash differs from the ingested record"
    with zipfile.ZipFile(io.BytesIO(data)) as inner:
        xml = inner.read(xml_member)
    assert raw.sha256(xml) == xml_sha, "XML hash differs from the ingested record"
    return xml


def check_control(conn, t: tuple, row: dict) -> dict:
    code, title, _, _, premise, expectation, trap = t
    xml = raw_xml(row["local_path"], row["member_name"], row["xml_member_name"], row["member_sha256"], row["xml_sha256"])
    root = raw.parse_xml(xml)
    perfs = [p for p in raw.performances(root) if p["in_author"]]
    prods = raw.products(root)
    ndc = row["ndc_raw"]
    for_prod = [p for p in perfs if ndc in p["product_codes"]]
    mfg_for_prod = [p for p in for_prod if p["code"] == MFG]
    api_for_prod = [p for p in for_prod if p["code"] == API]
    unscoped_mfg = [p for p in perfs if not p["product_codes"] and p["code"] == MFG]
    obs = {"operations_for_product": sorted({(p["code"], p["display_name"], d) for p in for_prod for d in (p["duns"] or [None])}),
           "manufacture_duns_for_product": sorted({d for p in mfg_for_prod for d in p["duns"]}),
           "api_duns_for_product": sorted({d for p in api_for_prod for d in p["duns"]}),
           "unscoped_manufacture_duns": sorted({d for p in unscoped_mfg for d in p["duns"]}),
           "products_in_section": [q["code"] for q in prods], "performances_outside_author":
           sum(1 for p in raw.performances(root) if not p["in_author"])}
    edges = [dict(zip(("assertion_pk", "operation_code", "operation_name", "is_manufacture", "duns", "confidence",
                       "confidence_reasons", "product_scope", "fei", "identity_status"), r)) for r in conn.execute(
        """SELECT assertion_pk, operation_code, operation_name, is_manufacture, duns, confidence, confidence_reasons,
                  product_scope, fei, identity_status FROM national.operation_edge
           WHERE report_product_pk = %s OR (document_pk = (SELECT document_pk FROM national.product WHERE product_pk = %s)
                                            AND product_scope = 'no_product_scope') ORDER BY assertion_pk""",
        (row["product_pk"], row["product_pk"]))]
    status = row["manufacturing_status"]
    mfg_edges = [e for e in edges if e["is_manufacture"] and e["product_scope"] != "no_product_scope"]
    premise_ok, expectation_ok = False, False
    if code in ("N1", "N2", "N3", "N4"):
        want = {"N1": "C84731", "N2": "C84732", "N3": "C25391", "N4": API}[code]
        premise_ok = any(p["code"] == want and p["duns"] for p in for_prod) and not mfg_for_prod
        expectation_ok = (not mfg_edges and status == "NO_MANUFACTURE_EVIDENCE" and
                          all(not e["is_manufacture"] for e in edges if e["operation_code"] == want))
    elif code == "N5":
        api_only = set(obs["api_duns_for_product"]) - set(obs["manufacture_duns_for_product"])
        premise_ok = bool(api_only) and bool(mfg_for_prod)
        expectation_ok = (bool(api_only) and not (api_only & {e["duns"] for e in mfg_edges}) and
                          set(obs["manufacture_duns_for_product"]) == {e["duns"] for e in mfg_edges} and
                          all(not e["is_manufacture"] for e in edges if e["operation_code"] == API))
        obs["api_only_duns"] = sorted(api_only)
    elif code == "N6":
        premise_ok = bool(unscoped_mfg) and not mfg_for_prod and len(prods) == 1
        un = [e for e in edges if e["product_scope"] == "no_product_scope" and e["is_manufacture"]]
        expectation_ok = (status == "NO_MANUFACTURE_EVIDENCE" and row["evidence_status"] == "ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT"
                          and not mfg_edges and un and all(e["confidence"] == "UNKNOWN" and
                                                            "scope:no_product_scope" in e["confidence_reasons"] for e in un))
    elif code in ("N7", "N8"):
        want = "NOT_FOUND" if code == "N7" else "STALE_REGISTERED"
        premise_ok = bool(mfg_for_prod) and all(e["identity_status"] == want for e in mfg_edges) and bool(mfg_edges)
        exp_status = "UNKNOWN_SITE" if code == "N7" else "TENTATIVE"
        exp_conf = "UNKNOWN" if code == "N7" else "TENTATIVE"
        expectation_ok = (status == exp_status and all(e["confidence"] == exp_conf and f"identity:{want}" in e["confidence_reasons"]
                                                       and e["confidence"] != "DIRECT" for e in mfg_edges))
    return {"premise_holds_in_raw_xml": premise_ok, "expectation_holds_in_graph": expectation_ok,
            "raw_observation": obs, "graph_edges": edges}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint")
    ap.add_argument("--out-dir", default=str(REPO / "docs" / "research"))
    a = ap.parse_args()
    out_dir = Path(a.out_dir)
    rng = random.Random(SEED)
    controls, n = [], 0
    with db.connect(a.db) as c:
        build = c.execute("SELECT max(build_id) FROM national.graph_build WHERE status = 'completed'").fetchone()[0]
        for t in TYPES:
            code, title, k, where, premise, expectation, trap = t
            cur = c.execute(BASE.format(where=where))
            cols = [d.name for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            # one control per label set, so a single unusual label cannot dominate a type
            by_set = {}
            for r in rows:
                by_set.setdefault(r["set_id"], r)
            pool = sorted(by_set.values(), key=lambda r: (r["set_id"], r["ndc_raw"]))
            for r in rng.sample(pool, min(k, len(pool))):
                n += 1
                chk = check_control(c, t, r)
                controls.append({
                    "id": f"N{n:02d}", "type": code, "title": title, "premise": premise, "expectation": expectation,
                    "trap": trap, "eligible_products": len(rows), "eligible_sets": len(pool),
                    "product": {k2: r[k2] for k2 in ("set_id", "version", "document_id", "xml_sha256", "ndc_raw", "name",
                                                     "manufacturing_status", "evidence_status", "products_in_document")},
                    "source": {"release_member": r["member_name"], "member_sha256": r["member_sha256"],
                               "fda_spl_xml": FDA.format(docid=r["document_id"]), "dailymed": DM.format(set_id=r["set_id"])},
                    **chk})
        retained = [{"id": "C19", "role": "operation-level check only", "why_weak_as_product_negative":
                     "set 92b7ddaa… also asserts MANUFACTURE (C43360) by DUNS 093132819 for 0409-4596 (edge 113220)",
                     "check": "the LABEL edge 113224 has is_manufacture = false"},
                    {"id": "C20", "role": "operation-level check only", "why_weak_as_product_negative":
                     "set e8808230… also asserts MANUFACTURE by DUNS 093132819 for 0409-9158 (edge 121361)",
                     "check": "the PACK edge 121363 has is_manufacture = false"}]
        for r in retained:
            pk = int(r["check"].split("edge ")[1].split()[0])
            r["is_manufacture_in_graph"] = c.execute("SELECT is_manufacture FROM national.operation_edge WHERE assertion_pk = %s",
                                                     (pk,)).fetchone()[0]
            r["ok"] = r["is_manufacture_in_graph"] is False
    out = {"generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
           "seed": SEED, "graph_build": build, "database": a.db,
           "status": "FROZEN replacement negative controls; the original worksheet (seed fineprint-human-audit-2026-10-20) is unchanged",
           "auditor_note": "premises re-checked by an independent raw-XML walk; expectations checked against the graph tables; "
                           "AI-assisted, not a human audit",
           "retained_operation_level_checks": retained,
           "controls": controls,
           "summary": {"n": len(controls),
                       "premise_holds": sum(1 for x in controls if x["premise_holds_in_raw_xml"]),
                       "expectation_holds": sum(1 for x in controls if x["expectation_holds_in_graph"]),
                       "by_type": {t[0]: sum(1 for x in controls if x["type"] == t[0]) for t in TYPES}}}
    p = out_dir / "audit_controls_v2.json"
    p.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8", newline="\n")
    write_md(out, out_dir / "AUDIT_CONTROLS_V2.md", hashlib.sha256(p.read_bytes()).hexdigest())
    print(json.dumps(out["summary"]))


def write_md(out: dict, path: Path, h: str):
    L = ["# Audit controls v2: independent product-level negative controls", "",
         f"**Status: frozen {out['generated_at']}** (seed `{out['seed']}`, graph build {out['graph_build']}; "
         f"machine-readable `audit_controls_v2.json`, SHA-256 `{h}`). The original worksheet sample "
         "(`docs/HUMAN_AUDIT_WORKSHEET.md`, seed `fineprint-human-audit-2026-10-20`) is unchanged; this file adds to it.", "",
         "## Why the original C19/C20 are weak", "",
         "C19 (LABEL by Rocky Mount for Precedex 0409-4596) and C20 (PACK by Rocky Mount for Vitamin K1 0409-9158) do test that "
         "a PACK or LABEL element is not recorded as MANUFACTURE. But both labels also contain a separate MANUFACTURE "
         "assertion by the same DUNS for the same product, so at product level the graph's answer ('Rocky Mount makes it') "
         "is correct either way. They cannot catch a classifier that conflates operations. They are retained as "
         "operation-level checks:", ""]
    for r in out["retained_operation_level_checks"]:
        L.append(f"- **{r['id']}**: {r['check']} — observed is_manufacture = `{r['is_manufacture_in_graph']}` "
                 f"({'ok' if r['ok'] else 'FAILED'}). Weak because {r['why_weak_as_product_negative']}.")
    L += ["", "## New controls", "",
          "Each control names a product whose label contains a specific non-manufacturing or non-attributable assertion, "
          "and states what the graph must say. A person checks the label (FDA XML by document ID, fixed bytes; or DailyMed) "
          "and then the explorer or `fp.py product <ndc>`. 'Premise' was re-checked in the raw XML by an independent walk; "
          "'expectation' was checked against the graph tables.", "",
          "| Id | Type | Product | Label | Premise holds | Expectation holds |", "|---|---|---|---|---|---|"]
    for x in out["controls"]:
        p = x["product"]
        L.append(f"| {x['id']} | {x['type']} {x['title']} | `{p['ndc_raw']}` {p['name']} | set `{p['set_id'][:8]}…` v{p['version']} | "
                 f"{'yes' if x['premise_holds_in_raw_xml'] else 'NO'} | {'yes' if x['expectation_holds_in_graph'] else 'NO'} |")
    L += [""]
    seen = set()
    for x in out["controls"]:
        p, s, o = x["product"], x["source"], x["raw_observation"]
        if x["type"] not in seen:
            seen.add(x["type"])
            L += [f"### {x['type']} · {x['title']}", "", f"- **Premise:** {x['premise']}", f"- **Expectation:** {x['expectation']}",
                  f"- **What it catches:** {x['trap']}", f"- Eligible: {x['eligible_products']} products in {x['eligible_sets']} sets.", ""]
        L += [f"#### {x['id']} · `{p['ndc_raw']}` {p['name']}",
              f"- Label set `{p['set_id']}` version {p['version']}: [FDA SPL XML by document ID]({s['fda_spl_xml']}) "
              f"(expected XML SHA-256 `{p['xml_sha256']}`), [DailyMed]({s['dailymed']}). Products in label: {p['products_in_document']}.",
              f"- Raw XML operations naming this product: {o['operations_for_product'] or 'none'}; MANUFACTURE DUNS for it: "
              f"{o['manufacture_duns_for_product'] or 'none'}" + (f"; unscoped MANUFACTURE DUNS in label: {o['unscoped_manufacture_duns']}"
                                                                   if o["unscoped_manufacture_duns"] else "") + ".",
              f"- Graph: manufacturing_status **{p['manufacturing_status']}** ({p['evidence_status']}); edges: " +
              "; ".join(f"{e['operation_name']} {e['duns']} {e['confidence']}{' ' + str(e['confidence_reasons']) if e['confidence_reasons'] else ''}"
                        f" [{e['assertion_pk']}]" for e in x["graph_edges"]) + ".",
              f"- Premise holds: **{'yes' if x['premise_holds_in_raw_xml'] else 'NO'}**; expectation holds: "
              f"**{'yes' if x['expectation_holds_in_graph'] else 'NO'}**.", ""]
    s = out["summary"]
    L += ["## Summary", "", f"{s['n']} controls: premise holds for {s['premise_holds']}, expectation holds for "
          f"{s['expectation_holds']}. By type: {s['by_type']}.", "",
          "A human audit of these controls records, per control, whether the label really contains the premise and whether "
          "the explorer shows the expectation. Verdicts go in a new CSV, not in `docs/human_audit_verdicts.csv`.", ""]
    path.write_text("\n".join(L), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    sys.exit(main())
