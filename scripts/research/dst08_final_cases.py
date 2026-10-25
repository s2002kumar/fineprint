"""DST-08 final validation, Phase 4: the source-link review cases, frozen, then re-derived from original evidence.

  python -I scripts/research/dst08_final_cases.py select --db fineprint_dst08     # freeze the case list
  python -I scripts/research/dst08_final_cases.py evidence --db fineprint_dst08   # re-derive every case

``select`` (run once, committed before any case is reviewed) takes, with seed SEED:
  W   the 32 rows of the existing worksheet (human_review_worksheet.csv), all of them;
  V   for each outcome of the rule v2 version check among the 373 physical conflicts (class, and for the accepted
      classes whether the source's sites continued), up to 3 references;
  M   v2-eligible links without a version check whose source has 5 or more DIRECT sites (2) or 2 to 4 (2);
  P   v2-eligible links whose citing product is a tablet or capsule and that have no imprint to compare (3);
  A   ambiguous mappings: several candidate sources naming different DIRECT sites (2), and a package code whose
      product prefix would match exactly one product (1).
A reference already in W is not drawn again. Output: final_cases_manifest.json and final_cases_FREEZE.json.

``evidence`` re-derives each case through a code path independent of fineprint.lineage: the raw-XML walkers of
dst08_source_inventory.py and verify_audit_sample.py, candidates from the independent inventory extract
($FINEPRINT_DATA/research/dst08/products.jsonl.gz), the FDA registration files read directly, and, for a version
check, the archived source version read from the cache and verified against source_history_manifest.json. It records
every fact with its citation (set id, version, document id, element location, XML SHA-256) and whether it reproduces
the prototype's v1 and v2 results. It judges nothing; the AI-assisted reading is final_ai_validation.csv and human
adjudication is final_human_worksheet.csv. Output: final_cases_evidence.json and final_cases_digest.md.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import random
import re
import sys
import zipfile
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "research"))
import dst08_check_sample as chk  # noqa: E402
import dst08_source_inventory as inv  # noqa: E402  independent XML walk (no fineprint parser imports)
import verify_audit_sample as raw  # noqa: E402
from fineprint import db  # noqa: E402  database access only

DST08 = REPO / "docs" / "research" / "dst08"
WORKSHEET = DST08 / "human_review_worksheet.csv"
MANIFEST = DST08 / "final_cases_manifest.json"
FREEZE = DST08 / "final_cases_FREEZE.json"
HISTORY = DST08 / "source_history_manifest.json"
OUT = DST08 / "final_cases_evidence.json"
DIGEST = DST08 / "final_cases_digest.md"
CACHE = raw.DATA / "research" / "dst08" / "history"
PRODUCTS = raw.DATA / "research" / "dst08" / "products.jsonl.gz"
SEED = "fineprint-dst08-final-validation-2026-10-25"
NS = raw.NS
KEYS = {"SPLIMPRINT": "imprint", "SPLCOLOR": "color", "SPLSHAPE": "shape", "SPLSIZE": "size", "SPLSCORE": "score",
        "SPLFLAVOR": "flavor"}

REF_SQL = """
SELECT r.reference_pk, lower(d.set_id), d.version, r.loc, r.product_ndc_raw, r.source_code_raw
FROM lineage.source_reference r JOIN national.spl_document d ON d.document_pk = r.document_pk"""

STRATA_SQL = {
    "V": """SELECT c.reference_pk, c.classification || CASE WHEN c.classification IN ('NOTATION_ONLY', 'VERSION_DRIFT_RESOLVED',
                   'MULTIPLE_VALID_PRESENTATIONS') THEN (CASE WHEN v.status = 'ELIGIBLE' THEN ' / sites continue'
                   ELSE ' / sites changed' END) ELSE '' END
            FROM lineage.version_check c JOIN lineage.resolution_v2 v USING (reference_pk) ORDER BY 1""",
    "M": """SELECT v.reference_pk, CASE WHEN count(DISTINCT e.duns) >= 5 THEN '5 or more DIRECT source sites'
                   ELSE '2 to 4 DIRECT source sites' END
            FROM lineage.resolution_v2 v JOIN lineage.source_linked_evidence_v2 e USING (reference_pk)
            WHERE v.basis = 'v1' AND v.status = 'ELIGIBLE' GROUP BY 1 HAVING count(DISTINCT e.duns) >= 2 ORDER BY 1""",
    "P": """SELECT v.reference_pk, 'tablet or capsule, no imprint compared: ' || p.outcome
            FROM lineage.resolution_v2 v JOIN lineage.physical_check p USING (reference_pk)
            JOIN lineage.source_reference r USING (reference_pk)
            JOIN national.product cp ON cp.product_pk = r.product_pk
            WHERE v.status = 'ELIGIBLE' AND (cp.dosage_form LIKE 'TABLET%%' OR cp.dosage_form LIKE 'CAPSULE%%')
              AND p.outcome IN ('NOTHING_COMPARABLE', 'NO_IMPRINT_OTHERS_EQUAL') ORDER BY 1""",
    "A": """SELECT x.reference_pk, CASE WHEN x.resolution = 'MULTIPLE_CANDIDATES' THEN 'several candidates naming different DIRECT sites'
                   ELSE 'package code with one product-prefix match' END
            FROM lineage.source_resolution x JOIN lineage.source_reference r USING (reference_pk)
            WHERE (x.resolution = 'MULTIPLE_CANDIDATES' AND 1 < (
                       SELECT count(DISTINCT sites) FROM (
                           SELECT p.product_pk, array_agg(DISTINCT e.duns ORDER BY e.duns) FILTER (WHERE e.duns IS NOT NULL) AS sites
                           FROM unnest(x.candidate_product_pks) cand(pk)
                           JOIN national.product p ON p.product_pk = cand.pk
                           LEFT JOIN national.operation_edge e ON e.product_pk = p.product_pk AND e.report_product_pk = p.product_pk
                                AND e.product_scope = 'product' AND e.is_manufacture AND e.confidence = 'DIRECT'
                           GROUP BY 1) s))
               OR (r.validity = 'PACKAGE_CODE_NOT_PRODUCT_CODE' AND 1 = (
                       SELECT count(*) FROM national.product p JOIN national.set_version_selection s USING (document_pk)
                       WHERE p.kind = 'product' AND p.ndc_raw = split_part(r.source_code_raw, '-', 1) || '-' || split_part(r.source_code_raw, '-', 2)))
            ORDER BY 1""",
}
QUOTAS = {"V": {None: 3}, "M": {"5 or more DIRECT source sites": 2, "2 to 4 DIRECT source sites": 2}, "P": {None: 3},
          "A": {"several candidates naming different DIRECT sites": 2, "package code with one product-prefix match": 1}}


def select(c) -> dict:
    refs = {(s, v, loc): (pk, own, src) for pk, s, v, loc, own, src in c.execute(REF_SQL).fetchall()}
    by_pk = {pk: (s, v, loc, own, src) for (s, v, loc), (pk, own, src) in refs.items()}
    rng = random.Random(SEED)
    cases, taken = [], set()
    sample = {s["sample_id"]: s for s in json.loads((DST08 / "sample_manifest.json").read_text(encoding="utf-8"))["sample"]}
    for row in csv.DictReader(WORKSHEET.read_text(encoding="utf-8").splitlines()):
        if row["sample_id"] in sample:
            s = sample[row["sample_id"]]
            key = (s["set_id"].lower(), int(s["version"]), s["ref_loc"])
        else:
            key = next(k for k, (pk, own, src) in refs.items()
                       if k[0] == row["citing_set_id"].lower() and own == row["citing_ndc"])
        pk = refs[key][0]
        taken.add(pk)
        cases.append({"case_id": f"W-{row['sample_id']}", "stratum": "W existing worksheet", "detail": row["stratum"],
                      "reference_pk": pk, "set_id": key[0], "version": key[1], "ref_loc": key[2],
                      "citing_ndc": refs[key][1], "source_code": refs[key][2]})
    for stratum, sql in STRATA_SQL.items():
        groups: dict[str, list[int]] = defaultdict(list)
        for pk, detail in c.execute(sql).fetchall():
            if pk not in taken:
                groups[detail].append(pk)
        for detail in sorted(groups):
            quota = QUOTAS[stratum].get(detail, QUOTAS[stratum].get(None, 0))
            pool = sorted(groups[detail])
            for n, pk in enumerate(sorted(rng.sample(pool, min(quota, len(pool)))), 1):
                taken.add(pk)
                s, v, loc, own, src = by_pk[pk]
                cases.append({"case_id": f"{stratum}-{re.sub(r'[^A-Za-z0-9]+', '_', detail).strip('_')[:40]}-{n}",
                              "stratum": stratum, "detail": detail, "pool": len(pool), "reference_pk": pk, "set_id": s,
                              "version": v, "ref_loc": loc, "citing_ndc": own, "source_code": src})
    return {"seed": SEED, "rules": __doc__.split("``select``")[1].split("``evidence``")[0].strip(), "n": len(cases),
            "cases": cases}


# ---------------------------------------------------------------------------------------------------- independent reads

def dec(s: str) -> str:
    try:
        d = Decimal(s)
    except InvalidOperation:
        return s
    return format(d.normalize(), "f") if d.is_finite() else s


def chars_of(role) -> dict:
    vals: dict[str, set] = defaultdict(set)
    for so in role.findall(NS + "subjectOf") if role is not None else []:
        ch = so.find(NS + "characteristic")
        code = ch.find(NS + "code") if ch is not None else None
        k = KEYS.get(code.get("code")) if code is not None else None
        val = ch.find(NS + "value") if k else None
        if val is None:
            continue
        if k == "imprint":
            v = " ".join("".join(val.itertext()).split())
        elif k == "size":
            v = f"{dec(val.get('value') or '')} {val.get('unit') or ''}".strip()
        else:
            v = val.get("code") or val.get("value") or ""
        if v:
            vals[k].add(v)
    out = {k: sorted(v) for k, v in vals.items()}
    if "imprint" in out:
        out["imprint_as_written"] = out["imprint"]
        out["imprint"] = sorted({re.sub(r"[^0-9A-Z]", "", v.upper()) for v in out["imprint_as_written"]} - {""})
        out["imprint_marks"] = sorted({re.sub(r"[^0-9A-Z]", "", t.upper()) for v in out["imprint_as_written"]
                                       for t in re.split(r"[;,\s]+", v)} - {""})
        if not out["imprint"]:
            del out["imprint"], out["imprint_marks"]
    return out


def compare(a: dict, b: dict) -> dict:
    per = {}
    for k in KEYS.values():
        if k in a and k in b:
            per[k] = ("SAME" if a[k] == b[k] else
                      "SAME_MARKS" if k == "imprint" and a["imprint_marks"] == b["imprint_marks"] else
                      "ONE_OF_SEVERAL" if set(a[k]) < set(b[k]) else "DIFFERS")
        elif k in a or k in b:
            per[k] = "ONE_SIDE"
    return per


def product_view(root, prod: dict) -> dict:
    role = chk.find_by_loc(root, prod["loc"].rsplit("/", 1)[0])
    return {"code": prod["code"], "name": prod["name"], "form": prod["form"], "form_name": prod["form_name"],
            "active": sorted([[u, dec(nv), nu, dec(dv), du] for u, nv, nu, dv, du in prod["active"]]),
            "characteristics": chars_of(role), "loc": prod["loc"]}


def open_doc(c, set_id: str, version: int):
    pk = c.execute("SELECT document_pk FROM national.spl_document WHERE lower(set_id) = %s AND version = %s",
                   (set_id, version)).fetchone()[0]
    d = chk.doc_location(c, pk)
    xml, root = chk.open_xml(d[0], d[1], d[2], d[3], d[4])
    return root, {"set_id": d[5].lower(), "version": d[6], "document_id": (d[8] or "").lower(),
                  "published_date": d[7].isoformat() if d[7] else None, "release_part": d[0], "member": d[1],
                  "xml_sha256": d[4]}


def manufacture_sites(root, code: str) -> list[dict]:
    return [{"duns": p["duns"], "org": p["org_name"], "loc": p["loc"]} for p in raw.performances(root)
            if p["in_author"] and p["code"] == raw.MANUFACTURE and code in p["product_codes"]]


def registration(decrs: dict, duns: str) -> dict:
    cur = decrs["current"]["by_duns"].get(duns) or []
    return {"current_rows": [{"line": r["line"], "fei": r["fei"], "operations": r["operations"], "expiration": r["expiration"]}
                             for r in cur],
            "current_file": decrs["current"]["path"], "current_file_sha256": decrs["current"]["sha256"],
            "archived_operations": {a["generated_date"]: [r["operations"] for r in a["by_duns"].get(duns, [])]
                                    for a in decrs["archived"]}}


def archived_version(hist: dict, set_id: str, version: int):
    rec = next((d for d in hist["documents"] if d["set_id"] == set_id and d["version"] == version), None)
    if rec is None or rec["status"] != "ok":
        return None, rec
    data = (CACHE / rec["zip_path"]).read_bytes()
    if raw.sha256(data) != rec["zip_sha256"]:
        raise SystemExit(f"cached archive differs from the manifest: {rec['zip_path']}")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        xml = z.read(rec["xml_member"])
    if raw.sha256(xml) != rec["xml_sha256"]:
        raise SystemExit(f"cached XML differs from the manifest: {rec['zip_path']}")
    return raw.parse_xml(xml), rec


def version_check(hist: dict, citing: dict, citing_view: dict, source_set: str, source_now: int, code54: str,
                  conflicting: list[str], at_current: dict) -> dict:
    """Rule v2's version check, re-implemented on the independent reads."""
    h = hist["history"]
    d = next((v["published_at"] for v in (h.get(citing["set_id"]) or {}).get("versions", [])
              if v["version"] == citing["version"]), None) or citing["published_date"]
    versions = sorted((v for v in (h.get(source_set) or {}).get("versions", []) if v["version"] <= source_now),
                      key=lambda v: v["version"])
    out = {"relevant_date": d, "source_versions": [(v["version"], v["published_at"]) for v in versions]}

    def view(version):
        root, rec = archived_version(hist, source_set, version)
        if root is None:
            return None, rec
        prods = [p for p in inv.walk_products(root) if p["kind"] == "product" and raw.to_5_4(p["code"]) == code54]
        pooled: dict[str, set] = defaultdict(set)
        for p in prods:
            for k, v in product_view(root, p)["characteristics"].items():
                pooled[k].update(v)
        sites = sorted({u for p in prods for s in manufacture_sites(root, p["code"]) for u in s["duns"]})
        return ({"products": len(prods), "characteristics": {k: sorted(v) for k, v in pooled.items()}, "sites": sites},
                rec)

    def describes(per):
        return not any(v == "DIFFERS" for v in per.values()) and all(
            per.get(k) in ("SAME", "SAME_MARKS", "ONE_OF_SEVERAL") for k in conflicting)

    if not d:
        return {**out, "class": "MISSING_COMPARISON_EVIDENCE", "why": "citing_date_unknown"}
    if (h.get(source_set) or {}).get("status") != "ok" or not versions:
        return {**out, "class": "MISSING_COMPARISON_EVIDENCE", "why": "history_unavailable"}
    before = [v for v in versions if v["published_at"] <= d]
    others_match, others_missing = [], []
    app = max(before, key=lambda v: v["version"]) if before else None
    for v in versions:
        if app and v["version"] == app["version"]:
            continue
        vv, _ = view(v["version"])
        if vv is None:
            others_missing.append(v["version"])
        elif vv["products"] and describes(compare(citing_view["characteristics"], vv["characteristics"])):
            others_match.append(v["version"])
    out.update(versions_matching=others_match, versions_unretrievable=others_missing)
    if app is None:
        return {**out, "class": "UNRESOLVED_AMBIGUITY", "why": "source_set_not_published_by_citing_date"}
    av, rec = view(app["version"])
    out.update(applicable_version=app["version"], applicable_published_at=app["published_at"],
               applicable_document_id=rec.get("document_id") if rec else None,
               applicable_xml_sha256=rec.get("xml_sha256") if rec else None)
    if av is None:
        return {**out, "class": "MISSING_COMPARISON_EVIDENCE", "why": "applicable_version_not_retrievable"}
    if not av["products"]:
        return {**out, "class": "UNRESOLVED_AMBIGUITY", "why": "code_not_in_applicable_version"}
    per = compare(citing_view["characteristics"], av["characteristics"])
    out.update(applicable_characteristics=av["characteristics"], at_applicable=per, sites_at_applicable=av["sites"])
    if any(v == "DIFFERS" for v in per.values()):
        cls = "UNRESOLVED_AMBIGUITY" if (others_match or others_missing) else "CONFIRMED_CONFLICT"
    elif any(per.get(k) not in ("SAME", "SAME_MARKS", "ONE_OF_SEVERAL") for k in conflicting):
        cls = "MISSING_COMPARISON_EVIDENCE"
    elif any(v == "ONE_OF_SEVERAL" for v in per.values()):
        cls = "MULTIPLE_VALID_PRESENTATIONS"
    elif any(v in ("DIFFERS", "ONE_OF_SEVERAL") for v in at_current.values()):
        cls = "VERSION_DRIFT_RESOLVED"
    else:
        cls = "NOTATION_ONLY"
    return {**out, "class": cls}


def evidence_one(c, case: dict, by_code: dict, decrs: dict, hist: dict) -> dict:
    root, cdoc = open_doc(c, case["set_id"], case["version"])
    el = chk.find_by_loc(root, case["ref_loc"])
    prods = inv.walk_products(root)
    holder_loc = case["ref_loc"].rsplit("/", 1)[0]
    citing_prod = next(p for p in prods if p["loc"] == holder_loc)
    citing = product_view(root, citing_prod)
    ref = next(r for r in citing_prod["refs"] if r["loc"] == case["ref_loc"])
    pattern = inv.code_pattern(ref["src_code"])
    code54 = raw.to_5_4(ref["src_code"]) if pattern == "product" else None
    cands = [k for k in by_code.get(code54, []) if k[1] == "product" and k[0][0] != cdoc["set_id"]] if code54 else []
    out = {"case_id": case["case_id"], "stratum": case["stratum"], "detail": case["detail"],
           "citing": {**cdoc, "product": citing, "element_loc": case["ref_loc"],
                      "element": chk.verbatim(el) if el is not None else None},
           "source_code": {"raw": ref["src_code"], "system": ref["src_system"], "pattern": pattern, "normalised_5_4": code54,
                           "equivalence": [ref["class_code"], ref["eq_code"], ref["eq_system"]]},
           "candidates": []}
    if pattern == "package":
        prefix = raw.to_5_4("-".join(ref["src_code"].split("-")[:2]))
        out["package_prefix_matches_not_used"] = len([k for k in by_code.get(prefix, []) if k[1] == "product"])
    for (s, v), kind, ploc in cands:
        sroot, sdoc = open_doc(c, s, v)
        sp = next(p for p in inv.walk_products(sroot) if p["loc"] == ploc)
        sview = product_view(sroot, sp)
        sites = manufacture_sites(sroot, sp["code"])
        out["candidates"].append({
            **sdoc, "product": sview, "form_same": sview["form"] == citing["form"],
            "active_same": sview["active"] == citing["active"],
            "physical_now": compare(citing["characteristics"], sview["characteristics"]),
            "manufacture_sites": sites,
            "registration": {u: registration(decrs, u) for s_ in sites for u in s_["duns"]},
            "candidate_cites_a_source": bool(sp["refs"])})
    proto = c.execute(
        """SELECT x.status, x.reasons, lower(x.source_set_id), x.source_version, p.outcome, p.differing, p.per,
                  v.status, v.reasons, v.basis, vc.classification, vc.applicable_version, vc.continuing_sites,
                  ARRAY(SELECT DISTINCT duns FROM lineage.source_linked_evidence e WHERE e.reference_pk = x.reference_pk ORDER BY 1),
                  ARRAY(SELECT DISTINCT duns FROM lineage.source_linked_evidence_v2 e WHERE e.reference_pk = x.reference_pk ORDER BY 1)
           FROM lineage.source_resolution x LEFT JOIN lineage.physical_check p USING (reference_pk)
           JOIN lineage.resolution_v2 v USING (reference_pk) LEFT JOIN lineage.version_check vc USING (reference_pk)
           WHERE x.reference_pk = %s""", (case["reference_pk"],)).fetchone()
    keys = ("v1_status", "v1_reasons", "v1_source_set", "v1_source_version", "physical_outcome", "physical_differing",
            "physical_per", "v2_status", "v2_reasons", "v2_basis", "v2_class", "v2_applicable_version",
            "v2_continuing_sites", "v1_evidence_sites", "v2_evidence_sites")
    out["prototype"] = dict(zip(keys, proto))
    p = out["prototype"]
    repro = {"candidates_independent": len(out["candidates"])}
    if len(out["candidates"]) == 1:
        cand = out["candidates"][0]
        repro["source_set_reproduced"] = cand["set_id"] == p["v1_source_set"]
        repro["physical_now_reproduced"] = (p["physical_per"] or {}) == cand["physical_now"]
        repro["independent_manufacture_sites"] = sorted({u for s_ in cand["manufacture_sites"] for u in s_["duns"]})
        repro["v1_evidence_sites_within_label_sites"] = set(p["v1_evidence_sites"]) <= set(repro["independent_manufacture_sites"])
        if p["v2_class"]:
            vc = version_check(hist, cdoc, citing, cand["set_id"], cand["version"], code54, list(p["physical_differing"]),
                               cand["physical_now"])
            out["version_check_independent"] = vc
            repro["v2_class_reproduced"] = vc["class"] == p["v2_class"]
            repro["v2_applicable_version_reproduced"] = vc.get("applicable_version") == p["v2_applicable_version"]
            if vc["class"] in ("NOTATION_ONLY", "VERSION_DRIFT_RESOLVED", "MULTIPLE_VALID_PRESENTATIONS"):
                cont = sorted(set(vc.get("sites_at_applicable") or []) & set(p["v1_evidence_sites"]))
                repro["v2_continuing_sites_reproduced"] = cont == list(p["v2_continuing_sites"] or [])
    out["reproduced"] = repro
    return out


def digest(results: list[dict]) -> str:
    lines = ["# DST-08 final validation: review cases, re-derived from original evidence", "",
             "Generated by `scripts/research/dst08_final_cases.py evidence`. Facts and citations only; the AI-assisted "
             "reading is `final_ai_validation.csv`, and human adjudication is `final_human_worksheet.csv`.", ""]
    for r in results:
        cz, p = r["citing"], r["prototype"]
        lines += [f"## {r['case_id']} ({r['stratum']}: {r['detail']})", "",
                  f"- citing `{cz['product']['code']}` {cz['product']['name']} ({cz['product']['form_name']}); set "
                  f"`{cz['set_id']}` v{cz['version']} doc `{cz['document_id']}` published {cz['published_date']}; "
                  f"xml sha256 `{cz['xml_sha256'][:16]}…`; {cz['element_loc'].split('/subject')[1] if '/subject' in cz['element_loc'] else cz['element_loc']}",
                  f"- cited element: `{cz['element']}`",
                  f"- citing active {cz['product']['active']}; characteristics {json.dumps(cz['product']['characteristics'])}",
                  f"- source code {json.dumps(r['source_code'])}"
                  + (f"; package prefix would match {r['package_prefix_matches_not_used']} product(s), never used"
                     if "package_prefix_matches_not_used" in r else "")]
        for cand in r["candidates"]:
            lines += [f"- candidate `{cand['product']['code']}` {cand['product']['name']} ({cand['product']['form_name']}); set "
                      f"`{cand['set_id']}` v{cand['version']} doc `{cand['document_id']}` published {cand['published_date']}; "
                      f"form same {cand['form_same']}, active same {cand['active_same']}; cites a source "
                      f"{cand['candidate_cites_a_source']}",
                      f"  - characteristics {json.dumps(cand['product']['characteristics'])}; now {json.dumps(cand['physical_now'])}",
                      "  - MANUFACTURE scoped to the code: " + ("; ".join(
                          f"{','.join(s['duns'])} {s['org']}" for s in cand["manufacture_sites"]) or "none")]
            for u, reg in cand["registration"].items():
                lines.append(f"  - registration {u}: current {reg['current_rows']}; archived {reg['archived_operations']}")
        if not r["candidates"]:
            lines.append("- candidates: none (independent inventory)")
        if "version_check_independent" in r:
            vc = r["version_check_independent"]
            lines.append(f"- version check (independent): D {vc.get('relevant_date')}; source versions {vc.get('source_versions')}; "
                         f"applicable v{vc.get('applicable_version')} ({vc.get('applicable_published_at')}) doc "
                         f"`{vc.get('applicable_document_id')}`; characteristics {json.dumps(vc.get('applicable_characteristics'))}; "
                         f"at applicable {json.dumps(vc.get('at_applicable'))}; sites then {vc.get('sites_at_applicable')}; "
                         f"other matching {vc.get('versions_matching')}; unretrievable {vc.get('versions_unretrievable')}; "
                         f"class **{vc['class']}**{' (' + vc['why'] + ')' if vc.get('why') else ''}")
        lines += [f"- prototype: v1 {p['v1_status']} {list(p['v1_reasons'])}; physical {p['physical_outcome']} "
                  f"{list(p['physical_differing'] or [])}; v2 {p['v2_status']} {list(p['v2_reasons'])} basis {p['v2_basis']}"
                  f"{'; class ' + p['v2_class'] if p['v2_class'] else ''}; evidence sites v1 {list(p['v1_evidence_sites'])} "
                  f"v2 {list(p['v2_evidence_sites'])}",
                  f"- reproduced: {json.dumps(r['reproduced'])}", ""]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=("select", "evidence"))
    ap.add_argument("--db", default="fineprint_dst08")
    a = ap.parse_args()
    with db.connect(a.db) as c:
        if a.step == "select":
            if MANIFEST.exists():
                raise SystemExit("the case list is frozen; it is never redrawn")
            m = select(c)
            text = json.dumps(m, indent=1) + "\n"
            MANIFEST.write_text(text, encoding="utf-8", newline="\n")
            FREEZE.write_text(json.dumps({"manifest": MANIFEST.name, "sha256": hashlib.sha256(text.encode()).hexdigest(),
                                          "frozen_at": raw.utc_now(), "seed": SEED, "n": m["n"]}, indent=1) + "\n",
                              encoding="utf-8", newline="\n")
            print(json.dumps({"n": m["n"], "by_stratum": {s: sum(x["stratum"] == s for x in m["cases"])
                                                          for s in sorted({x["stratum"] for x in m["cases"]})}}))
            return
        text = MANIFEST.read_text(encoding="utf-8")
        if hashlib.sha256(text.encode()).hexdigest() != json.loads(FREEZE.read_text(encoding="utf-8"))["sha256"]:
            raise SystemExit("final_cases_manifest.json differs from its FREEZE hash")
        by_code: dict = defaultdict(list)
        with gzip.open(PRODUCTS, "rt", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                for p in d["products"]:
                    n = raw.to_5_4(p["code"])
                    if n:
                        by_code[n].append(((d["set_id"].lower(), d["version"]), p["kind"], p["loc"]))
        decrs = raw.load_decrs()
        hist = json.loads(HISTORY.read_text(encoding="utf-8"))
        results = [evidence_one(c, case, by_code, decrs, hist) for case in json.loads(text)["cases"]]
    OUT.write_text(json.dumps({"generated_at": raw.utc_now(), "manifest_sha256": hashlib.sha256(text.encode()).hexdigest(),
                               "results": results}, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    DIGEST.write_text(digest(results), encoding="utf-8", newline="\n")
    flags = defaultdict(lambda: defaultdict(int))
    for r in results:
        for k, v in r["reproduced"].items():
            if isinstance(v, bool):
                flags[k][v] += 1
    print(json.dumps({k: dict(v) for k, v in flags.items()}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
