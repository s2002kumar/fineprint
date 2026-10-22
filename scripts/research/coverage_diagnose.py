"""Inspect the raw source of every product in the frozen coverage sample (research workstream C2).

For each sampled product the script re-opens the label from the DailyMed release part (hash-verified), then:
  * structured scan (independent XML walk, no fineprint code): every <performance> in the document, operations that
    name this product, MANUFACTURE anywhere in the label, unscoped MANUFACTURE, API MANUFACTURE, kit relations,
    operation product codes that match nothing, source NDCs cited through asEquivalentEntity (repackager labels),
    FEI ids and addresses carried by establishment blocks;
  * free-text scan: narrative section text searched for manufacturing-role statements ("Manufactured by", "Manufactured
    for", "Distributed by", "Made in", ...), each excerpt recorded with its section code, title and character offset;
  * a deterministic baseline extractor that turns "<role> by/for: <name>, <address>" statements into candidate
    (role, company, location) triples, and compares the company with the label's own establishment names and with
    FDA DECRS firm names. Those are RAW CANDIDATES: nothing here verifies a physical site;
  * identity facts for the DUNS involved (dated DECRS files), and a live DailyMed version history to flag version drift.

Output: docs/research/coverage_cases.json (full detail) and docs/research/coverage_cases_digest.md (for reading and
adjudication). Adjudication itself is a separate, hand-written file.

  python -I scripts/research/coverage_diagnose.py [--offline]
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import re
import sys
import time
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "research"))
import verify_audit_sample as raw  # noqa: E402  independent XML/DECRS helpers (no fineprint imports)

NS = raw.NS
MFG, API = "C43360", "C82401"
ROLE = re.compile(r"\b(Manufactured|Mfd\.?|Mfg\.?|Made|Produced|Distributed|Dist\.?|Marketed|Packaged|Packed|Labeled|"
                  r"Labelled|Relabeled|Repackaged|Imported|Manufacturer|Product of)\b(?:\s*[:.]?\s*)(by|for|in|of)?\b",
                  re.I)
STOP = re.compile(r"\b(Manufactured|Mfd\.?|Mfg\.?|Made in|Distributed|Dist\.?|Marketed|Packaged|Packed|Labeled|Labelled|"
                  r"Relabeled|Repackaged|Imported|Revised|Rev\.|Issued|Iss\.|Product of|Licensed|For more information|"
                  r"Questions|Call|Copyright|©|U\.S\. Patent|Patent)\b", re.I)
COUNTRY_HINT = re.compile(r"\b(USA|U\.S\.A\.|United States|India|China|Canada|Italy|Germany|Israel|Ireland|Switzerland|"
                          r"France|Spain|Japan|Korea|Taiwan|UK|United Kingdom|England|Mexico|Brazil|Hungary|Poland|Czech|"
                          r"Slovenia|Croatia|Austria|Belgium|Netherlands|Denmark|Sweden|Finland|Norway|Portugal|Greece|"
                          r"Turkey|Jordan|Malta|Iceland|Australia|New Zealand|Singapore|Malaysia|Indonesia|Thailand|Vietnam|"
                          r"Bangladesh|Pakistan|Egypt|South Africa|Argentina|Chile|Colombia|Puerto Rico|PR)\b")
SUFFIX = re.compile(r"\b(inc|incorporated|llc|l\.l\.c|ltd|limited|corp|corporation|co|company|plc|gmbh|s\.?a\.?|s\.?p\.?a\.?|"
                    r"pvt|private|lp|llp|ag|bv|b\.v|nv|n\.v|sas|srl|s\.r\.l|kg|ab|oy|pty|usa|us|u\.s\.a|u\.s)\b\.?", re.I)


def norm_name(s: str | None) -> str:
    if not s:
        return ""
    s = s.upper().replace("&", " AND ")
    s = SUFFIX.sub(" ", s)
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    return " ".join(s.split())


def section_texts(root) -> list[dict]:
    """Own text of every section (title + direct <text>), in document order, with codes."""
    out = []
    for i, sec in enumerate(root.iter(NS + "section")):
        code = sec.find(NS + "code")
        title = sec.find(NS + "title")
        parts = []
        for t in sec.findall(NS + "text"):
            parts.append(" ".join("".join(t.itertext()).split()))
        txt = " ".join(p for p in parts if p)
        if not txt and title is None:
            continue
        out.append({"i": i, "code": code.get("code") if code is not None else None,
                    "title": " ".join("".join(title.itertext()).split()) if title is not None else None, "text": txt})
    return out


def author_orgs(root) -> list[dict]:
    """Organizations in the author tree with depth (1 labeler, 2 registrant, 3 establishment), ids and address."""
    out = []

    def rec(elem, depth):
        for child in elem:
            t = raw.local(child.tag)
            if t == "assignedEntity":
                d = depth + 1
                org = next((o for o in child if raw.local(o.tag) in ("assignedOrganization", "representedOrganization")), None)
                if org is not None:
                    name = org.find(NS + "name")
                    addr = org.find(NS + "addr")
                    ids = [(i.get("root"), i.get("extension")) for i in org.findall(NS + "id")]
                    out.append({"depth": d, "name": " ".join("".join(name.itertext()).split()) if name is not None else None,
                                "duns": [e for r, e in ids if r == raw.DUNS_ROOT and e],
                                "fei": [e for r, e in ids if r == raw.FEI_ROOT and e],
                                "other_ids": [(r, e) for r, e in ids if r not in (raw.DUNS_ROOT, raw.FEI_ROOT)],
                                "address": " ".join("".join(addr.itertext()).split()) if addr is not None else None,
                                "n_performances": sum(1 for x in child if raw.local(x.tag) == "performance")})
                rec(child, d)
            else:
                rec(child, depth)

    for a in root.findall(NS + "author"):
        rec(a, 0)
    return out


def free_text_hits(sections: list[dict]) -> list[dict]:
    hits = []
    for s in sections:
        txt = s["text"] or ""
        for m in ROLE.finditer(txt):
            kw = m.group(1).lower().rstrip(".")
            prep = (m.group(2) or "").lower()
            if kw in ("made", "product") and prep not in ("in", "of", "by"):
                continue
            if kw == "manufacturer" and not re.match(r"\s*[:.]", txt[m.end(1):m.end(1) + 3]):
                continue
            role = {"manufactured": "MANUFACTURED", "mfd": "MANUFACTURED", "mfg": "MANUFACTURED", "produced": "MANUFACTURED",
                    "manufacturer": "MANUFACTURER", "made": "MADE", "product": "PRODUCT_OF", "distributed": "DISTRIBUTED",
                    "dist": "DISTRIBUTED", "marketed": "MARKETED", "packaged": "PACKAGED", "packed": "PACKAGED",
                    "labeled": "LABELED", "labelled": "LABELED", "relabeled": "RELABELED", "repackaged": "REPACKAGED",
                    "imported": "IMPORTED"}[kw]
            role = f"{role}_{prep.upper()}" if prep else role
            start = max(0, m.start() - 120)
            tail = txt[m.end():m.end() + 320]
            stop = STOP.search(tail, 3)
            after = tail[: stop.start()] if stop else tail
            hits.append({"section_index": s["i"], "section_code": s["code"], "section_title": s["title"],
                         "offset": m.start(), "role": role, "match": m.group(0),
                         "context": txt[start: m.end() + 320], "statement": (m.group(0) + after).strip()})
    return hits


def baseline_extract(hits: list[dict]) -> list[dict]:
    """Deterministic baseline: (role, company, location) from each statement; no matching, no inference."""
    out = []
    for h in hits:
        body = h["statement"][len(h["match"]):].strip(" :.-,")
        if not body:
            continue
        # company = text up to the first comma/period that is followed by an address-like token or a country
        m = re.match(r"(?P<company>[^,.;]{2,80}?)(?:[,.;]\s*|\s{2,})(?P<rest>.*)", body)
        company = (m.group("company") if m else body[:80]).strip()
        rest = (m.group("rest") if m else "").strip()
        country = COUNTRY_HINT.search(rest) or COUNTRY_HINT.search(company)
        physical = h["role"] in ("MANUFACTURED_BY", "MANUFACTURER", "MADE_IN", "PRODUCT_OF", "MANUFACTURED",
                                 "PACKAGED_BY", "LABELED_BY", "REPACKAGED_BY", "RELABELED_BY")
        out.append({"role": h["role"], "physical_claim": physical, "company": company, "company_norm": norm_name(company),
                    "location": rest[:160], "country_hint": country.group(0) if country else None,
                    "section_code": h["section_code"], "offset": h["offset"]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(REPO / "docs" / "research" / "coverage_sample_manifest.json"))
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--out", default=str(REPO / "docs" / "research" / "coverage_cases.json"))
    ap.add_argument("--digest", default=str(REPO / "docs" / "research" / "coverage_cases_digest.md"))
    a = ap.parse_args()
    t0 = time.time()
    man = json.loads(Path(a.manifest).read_text("utf-8"))
    freeze = json.loads((Path(a.manifest).parent / "coverage_sample_FREEZE.json").read_text("utf-8"))
    assert raw.sha256(Path(a.manifest).read_bytes()) == freeze["sha256"], "manifest differs from its freeze hash"
    decrs = raw.load_decrs()
    firm_index: dict[str, list] = {}
    for d in decrs["current"]["by_duns"].values():
        for r in d:
            firm_index.setdefault(norm_name(r["firm"]), []).append(r)
    parts = {p.name: p for p in (raw.DATA / "raw" / "dailymed" / "human_rx_full").glob("*/dm_spl_release_human_rx_part*.zip")}
    cases = []
    for s in man["products"]:
        with zipfile.ZipFile(parts[s["part"]]) as outer:
            data = outer.read(s["member_name"])
        assert raw.sha256(data) == s["member_sha256"], s["sample_id"]
        with zipfile.ZipFile(io.BytesIO(data)) as inner:
            xml = inner.read(s["xml_member_name"])
        assert raw.sha256(xml) == s["xml_sha256"], s["sample_id"]
        root = raw.parse_xml(xml)
        perfs = raw.performances(root)
        prods = raw.products(root)
        orgs = author_orgs(root)
        ndc = s["ndc_raw"]
        me = [p for p in prods if p["code"] == ndc]
        my_parts = {k for p in me for k in p["parts"]}
        for_me = [p for p in perfs if ndc in p["product_codes"]]
        all_codes = {p["code"] for p in prods} | {k for p in prods for k in p["parts"]}
        pkg_codes = {k for p in prods for k in p["packages"] if k}
        unmatched = [(p["loc"], c) for p in perfs for c in p["product_codes"] if c not in all_codes]
        unmatched_detail = []
        for loc, c in unmatched:
            kind = "package_code" if c in pkg_codes else ("normalizes_to_a_product" if raw.to_5_4(c) in {raw.to_5_4(x) for x in all_codes if x}
                                                          else "no_match")
            unmatched_detail.append({"loc": loc, "code": c, "kind": kind})
        est = [o for o in orgs if o["depth"] == 3]
        structured = {
            "performances_total": len(perfs), "performances_outside_author": sum(1 for p in perfs if not p["in_author"]),
            "performances_not_depth3": sum(1 for p in perfs if p["depth"] != 3),
            "establishments": len(est), "establishments_with_fei_id": sum(1 for o in est if o["fei"]),
            "establishments_with_address": sum(1 for o in est if o["address"]),
            "establishment_names": [o["name"] for o in est], "establishment_duns": [d for o in est for d in o["duns"]],
            "registrant": [o["name"] for o in orgs if o["depth"] == 2], "labeler": [o["name"] for o in orgs if o["depth"] == 1],
            "products_in_label": [p["code"] for p in prods], "product_section": me[0]["section"] if me else None,
            "operations_for_product": sorted({(p["code"], p["display_name"], d) for p in for_me for d in (p["duns"] or [None])}),
            "manufacture_duns_for_product": sorted({d for p in for_me if p["code"] == MFG for d in p["duns"]}),
            "manufacture_without_duns_for_product": any(p["code"] == MFG and not p["duns"] for p in for_me),
            "api_duns_for_product": sorted({d for p in for_me if p["code"] == API for d in p["duns"]}),
            "manufacture_for_other_products": sorted({(c, d) for p in perfs if p["code"] == MFG for c in p["product_codes"]
                                                      for d in p["duns"] if c != ndc}),
            "manufacture_for_my_kit_parts": sorted({(c, d) for p in perfs if p["code"] == MFG for c in p["product_codes"]
                                                    for d in p["duns"] if c in my_parts}),
            "unscoped_operations": sorted({(p["code"], p["display_name"], d) for p in perfs if not p["product_codes"]
                                           for d in (p["duns"] or [None])}),
            "unscoped_manufacture_duns": sorted({d for p in perfs if not p["product_codes"] and p["code"] == MFG for d in p["duns"]}),
            "unmatched_operation_codes": unmatched_detail,
            "source_ndcs_for_product": [c for p in me for c in p["source_ndcs"]],
            "source_ndcs_in_label": sorted({c for p in prods for c in p["source_ndcs"] if c}),
            "effective_time": raw.header(root)["effective_time"],
        }
        sections = section_texts(root)
        hits = free_text_hits(sections)
        base = baseline_extract(hits)
        est_norm = {norm_name(o["name"]) for o in est if o["name"]}
        for b in base:
            b["matches_label_establishment_name"] = bool(b["company_norm"]) and b["company_norm"] in est_norm
            rows = firm_index.get(b["company_norm"], []) if b["company_norm"] else []
            b["decrs_exact_name_matches"] = [{"fei": r["fei"], "duns": r["duns"], "address": r["address"]} for r in rows[:5]]
            b["decrs_exact_name_match_count"] = len(rows)
        ids = {}
        for d in set(structured["establishment_duns"]) | {e["duns"] for e in s.get("manufacture_edges", []) if e["duns"]}:
            r = raw.resolve_identity(d, decrs)
            ids[d] = {"status": r["status"], "fei": r["row"]["fei"] if r["row"] else None,
                      "firm": r["row"]["firm"] if r["row"] else None, "as_of": r["file"]["generated_date"] if r["file"] else None,
                      "registrant_only_in_current": r["registrant_only_in_current"], "fei_changed": r["fei_changed"]}
        hist = None
        if not a.offline or (raw.DL / "dailymed" / f"history_{s['set_id']}.json").exists():
            f = raw.fetch(raw.DM_HISTORY.format(setid=s["set_id"]), raw.DL / "dailymed" / f"history_{s['set_id']}.json",
                          offline=a.offline)
            if f.get("sha256"):
                h = json.loads((raw.DL / "dailymed" / f"history_{s['set_id']}.json").read_text("utf-8"))
                rows = (h.get("data") or {}).get("history") or []
                vers = sorted(int(r["spl_version"]) for r in rows)
                mine = [r for r in rows if int(r["spl_version"]) == s["version"]]
                hist = {"versions_today": vers[-1] if vers else None, "n_versions": len(vers),
                        "sampled_version_listed": bool(mine),
                        "sampled_version_published": dt.datetime.strptime(mine[0]["published_date"], "%b %d, %Y").date().isoformat() if mine else None,
                        "newer_version_exists_today": bool(vers) and vers[-1] > s["version"]}
            else:
                hist = {"error": f.get("error")}
        cases.append({"sample_id": s["sample_id"], "stratum": s["stratum"], "product": {k: s[k] for k in (
            "set_id", "version", "document_id", "xml_sha256", "ndc_raw", "ndc_product_5_4", "name", "dosage_form",
            "labeler_names", "manufacturing_status", "evidence_status", "selection_class", "published_date", "effective_time_raw",
            "n_products", "n_establishments", "n_operation_assertions", "part", "member_name")},
            "graph": {"manufacture_edges": s["manufacture_edges"], "all_edges": s["graph_edges_for_product"],
                      "unscoped_in_document": s["unscoped_operations_in_document"]},
            "structured": structured, "identity": ids, "free_text_hits": hits, "baseline_extraction": base,
            "dailymed_history_today": hist})
        print(s["sample_id"], s["stratum"], file=sys.stderr)
    out = {"generated_at": raw.utc_now(), "manifest_sha256": freeze["sha256"], "seconds": round(time.time() - t0, 1),
           "decrs_files": {k: {kk: v[kk] for kk in ("path", "sha256", "generated")} for k, v in
                           (("current", decrs["current"]), ("excluded", decrs["excluded"]))},
           "cases": cases}
    Path(a.out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8", newline="\n")
    write_digest(out, Path(a.digest))


def write_digest(out: dict, path: Path):
    L = ["# Coverage sample: per-case digest (generated; read-only input to adjudication)", "",
         f"Generated {out['generated_at']} from the frozen manifest (SHA-256 `{out['manifest_sha256'][:16]}…`). "
         "Full detail in `coverage_cases.json`.", ""]
    for c in out["cases"]:
        p, st, g = c["product"], c["structured"], c["graph"]
        L += [f"## {c['sample_id']} · {c['stratum']} · `{p['ndc_raw']}` {p['name']}",
              f"- set `{p['set_id']}` v{p['version']} (published {p['published_date']}, effective {st['effective_time']}); "
              f"labeler {p['labeler_names']}; {p['n_products']} products, {st['establishments']} establishments "
              f"({st['establishments_with_fei_id']} with FEI id, {st['establishments_with_address']} with address); "
              f"graph {p['manufacturing_status']} / {p['evidence_status']}.",
              f"- establishments: {list(zip(st['establishment_names'], st['establishment_duns']))}",
              f"- ops for this product: {st['operations_for_product'] or 'none'}; MANUFACTURE DUNS: {st['manufacture_duns_for_product'] or 'none'}"
              + (f"; API DUNS: {st['api_duns_for_product']}" if st["api_duns_for_product"] else "")
              + (f"; MANUFACTURE for other products: {st['manufacture_for_other_products']}" if st["manufacture_for_other_products"] else "")
              + (f"; kit-part MANUFACTURE: {st['manufacture_for_my_kit_parts']}" if st["manufacture_for_my_kit_parts"] else "")
              + (f"; unscoped ops: {st['unscoped_operations']}" if st["unscoped_operations"] else "")
              + (f"; UNMATCHED op codes: {st['unmatched_operation_codes']}" if st["unmatched_operation_codes"] else "")
              + (f"; source NDC (asEquivalentEntity): {st['source_ndcs_for_product']}" if st["source_ndcs_for_product"] else "")
              + (f"; outside-author performances: {st['performances_outside_author']}" if st["performances_outside_author"] else "") + "."]
        if c["identity"]:
            L.append("- identity: " + "; ".join(f"{d} {v['status']}" + (f" FEI {v['fei']} ({v['firm']})" if v["fei"] else "")
                                                + (" [registrant-only]" if v["registrant_only_in_current"] else "")
                                                for d, v in sorted(c["identity"].items())))
        if g["manufacture_edges"]:
            L.append("- graph MANUFACTURE edges: " + "; ".join(f"{e['duns']} {e['confidence']} {e['confidence_reasons']}" for e in g["manufacture_edges"]))
        h = c["dailymed_history_today"]
        if h and "error" not in h:
            L.append(f"- DailyMed today: latest v{h['versions_today']} ({h['n_versions']} versions); sampled version listed: "
                     f"{h['sampled_version_listed']}" + (f", published {h['sampled_version_published']}" if h["sampled_version_published"] else "")
                     + ("; NEWER VERSION EXISTS" if h["newer_version_exists_today"] else ""))
        if c["free_text_hits"]:
            L.append(f"- free text ({len(c['free_text_hits'])} hits):")
            for hh in c["free_text_hits"][:8]:
                L.append(f"  - [{hh['role']}] §{hh['section_code']} {hh['section_title'] or ''} @{hh['offset']}: "
                         f"“{hh['statement'][:220]}”")
            for b in c["baseline_extraction"][:6]:
                L.append(f"  - baseline: {b['role']} → company “{b['company']}” | location “{b['location'][:80]}” | "
                         f"label-establishment name match: {b['matches_label_establishment_name']}; DECRS exact-name rows: "
                         f"{b['decrs_exact_name_match_count']}")
        else:
            L.append("- free text: no manufacturing-role statement found")
        L.append("")
    path.write_text("\n".join(L), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    sys.exit(main())
