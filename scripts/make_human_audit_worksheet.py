"""Write the human audit worksheet: a seeded, stratified sample of published records with the public source
URLs a person can use to check each one without running fineprint.

  python -I scripts/make_human_audit_worksheet.py      # writes docs/HUMAN_AUDIT_WORKSHEET.md and docs/human_audit_verdicts.csv

Reads only site/data/ (the files the explorer publishes), so it needs no database. Same seed, same sample.
"""

import csv
import io
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "site" / "data"
SEED = "fineprint-human-audit-2026-10-20"
RM, MCP = "093132819", "030606222"
DM = "https://dailymed.nlm.nih.gov/dailymed"
DECRS_SEARCH = "https://www.accessdata.fda.gov/scripts/cder/drls/default.cfm"
OP_CODES = {"MANUFACTURE": "C43360", "ANALYSIS": "C25391", "PACK": "C84731", "LABEL": "C84732"}


def load(rel):
    return json.loads((DATA / rel).read_text(encoding="utf-8"))


def rows_of(bundle):
    for raw in bundle["edges"]:
        e = dict(zip(bundle["edge_columns"], raw))
        p = dict(zip(bundle["product_columns"], bundle["products"][str(e["product"])])) if e["product"] else None
        d = dict(zip(bundle["document_columns"], bundle["documents"][e["set_id"]]))
        yield e, p, d


def current_samples(rng):
    idx = load("current/facilities.json")
    fac = {r[0]: dict(zip(idx["columns"], r)) for r in idx["rows"]}
    national = []
    for f in sorted((DATA / "current" / "manufacture").glob("*.json")):
        national += [r for r in rows_of(load(f"current/manufacture/{f.name}")) if r[0]["duns"] not in (RM, MCP)]
    ex = {d: list(rows_of(load(f"current/examples/{d}.json"))) for d in (RM, MCP)}
    pick = lambda pool, n: rng.sample(sorted(pool, key=lambda r: r[0]["evidence_id"]), n)  # noqa: E731
    plan = [
        ("DIRECT MANUFACTURE, national", pick([r for r in national if r[0]["confidence"] == "DIRECT"], 8)),
        ("DIRECT MANUFACTURE, Rocky Mount", pick([r for r in ex[RM] if r[0]["operation"] == "MANUFACTURE"
                                                 and r[0]["confidence"] == "DIRECT"], 2)),
        ("DIRECT MANUFACTURE, McPherson", pick([r for r in ex[MCP] if r[0]["operation"] == "MANUFACTURE"], 2)),
        ("TENTATIVE MANUFACTURE", pick([r for r in national if r[0]["confidence"] == "TENTATIVE"], 3)),
        ("UNKNOWN MANUFACTURE", pick([r for r in national + ex[RM] if r[0]["confidence"] == "UNKNOWN"], 3)),
        ("Control: PACK or LABEL is not MANUFACTURE", pick([r for r in ex[RM] if r[0]["operation"] in ("PACK", "LABEL")], 2)),
    ]
    out, n = [], 0
    for stratum, rows in plan:
        for e, p, d in rows:
            n += 1
            f = fac[e["duns"]]
            out.append({"id": f"C{n:02d}", "stratum": stratum, "e": e, "p": p, "d": d, "f": f})
    return out


def historical_samples(rng):
    h = load("historical/rocky_mount_2023.json")
    pk = [dict(zip(h["package_columns"], r)) for r in h["packages"]]
    by = lambda cls, flag=None, listed=None: sorted(  # noqa: E731
        (p for p in pk if p["classification"] == cls and (listed is None or p["on_warning_list"] == listed)),
        key=lambda p: p["package_ndc_11"])
    plan = [("DIRECT, on Pfizer's list", rng.sample(by("DIRECT", listed=True), 2)),
            ("DIRECT, not on Pfizer's list", rng.sample(by("DIRECT", listed=False), 2)),
            ("OTHER_SITE", rng.sample(by("OTHER_SITE"), 3)),
            ("RM_SECONDARY_ONLY", rng.sample(by("RM_SECONDARY_ONLY"), 1)),
            ("UNKNOWN_NO_ESTABLISHMENT", rng.sample(by("UNKNOWN_NO_ESTABLISHMENT"), 1)),
            ("UNKNOWN_NO_MANUFACTURE_OP", rng.sample(by("UNKNOWN_NO_MANUFACTURE_OP"), 1)),
            ("Uncovered warning-list NDC", by("NOT_IN_COHORT")[:1])]
    out, n = [], 0
    for stratum, rows in plan:
        for p in rows:
            n += 1
            prov = [dict(zip(h["provenance_columns"], v)) for v in p["provenance"]]
            out.append({"id": f"H{n:02d}", "stratum": stratum, "p": p, "prov": prov})
    return h, out


def md_current(s):
    e, p, d, f = s["e"], s["p"], s["d"], s["f"]
    prod = f"`{p['ndc_5_4']}` {p['name']} ({p['dosage_form']})" if p else "no product (operation not tied to one)"
    op = e["operation"]
    lines = [f"### {s['id']} · {s['stratum']}",
             f"- **fineprint says:** label set `{e['set_id']}` version {d['version']} (published {d['published_date']}) "
             f"asserts **{op}** (`{OP_CODES.get(op, op)}`) by DUNS `{e['duns']}` for {prod}. "
             f"Status **{e['confidence']}**" + (f"; reasons: {', '.join(e['reasons'])}" if e["reasons"] else "") + ".",
             f"- **Identity in fineprint:** {f['status']}" + (f", FEI {f['fei']}, {f['firm_name']}, {f['address']}"
                                                              if f["fei"] else "") + ".",
             f"- **Check 1 (label):** open the exact version, [FDA SPL XML by document ID]"
             f"(https://www.accessdata.fda.gov/spl/data/{d['document_id']}/{d['document_id']}.xml) "
             f"(expected SHA-256 `{d['xml_sha256']}`). At `{e['loc']}` there should be a `<performance>` whose "
             f"`actDefinition/code` is `{OP_CODES.get(op, op)}`, inside the establishment whose `id` has extension "
             f"`{e['duns']}`" + (f", naming product code `{e['operation_product_code']}`." if e["operation_product_code"]
                                 else ", with no product code.") +
             f" Easier view: the [DailyMed label]({DM}/drugInfo.cfm?setid={e['set_id']}) lists establishments and "
             f"their operations near the end; first confirm it still shows version {d['version']}.",
             f"- **Check 2 (identity):** search DUNS `{e['duns']}`" + (f" or FEI `{f['fei']}`" if f["fei"] else "")
             + f" in [FDA DECRS]({DECRS_SEARCH}). " + ("Expect the same FEI and address."
                                                       if f["status"] == "CURRENT_REGISTERED" else
                                                       "fineprint found no current registration line with an FEI; "
                                                       "a hit today may reflect a change after 2026-10-19."),
             ""]
    return lines


def md_hist(s):
    p, prov = s["p"], s["prov"]
    lines = [f"### {s['id']} · {s['stratum']}",
             f"- **fineprint says:** package `{p['package_ndc_11']}` is **{p['classification']}**; flagged: "
             f"{'yes' if p['graph_flag'] else 'no'}; on Pfizer's July 21, 2023 list: "
             f"{'yes' if p['on_warning_list'] else 'no'}." + (f" Note: {p['note']}." if p["note"] else "")]
    for v in prov:
        lines.append(f"- **Pre-cutoff label:** set `{v['set_id']}` version {v['version']}, published "
                     f"{v['published_date']} ({v['document_kind']}): [{v['document_url']}]({v['document_url']}) "
                     f"(XML SHA-256 `{v['xml_sha256']}`). Confirm the publication date in the "
                     f"[version history]({DM}/services/v2/spls/{v['set_id']}/history.json).")
        if v["rocky_mount_manufacture_locs"]:
            lines.append(f"  - Expect `C43360` (MANUFACTURE) by DUNS `093132819` for product `{v['product_ndc_raw']}` "
                         f"at `{'`, `'.join(v['rocky_mount_manufacture_locs'])}`.")
        else:
            lines.append(f"  - Expect **no** MANUFACTURE by DUNS `093132819` for product `{v['product_ndc_raw']}`. "
                         f"Manufacturing DUNS fineprint read: {', '.join(v['manufacture_duns']) or 'none'}.")
    if not prov:
        lines.append(f"- **Check:** search DailyMed for NDC `{p['package_ndc_11']}` "
                     f"([search]({DM}/search.cfm?labeltype=all&query={p['package_ndc_11']})). fineprint expects no "
                     "drug label to exist for this product.")
    lines.append("")
    return lines


def main():
    rng = random.Random(SEED)
    cur = current_samples(rng)
    hist, his = historical_samples(rng)
    man = load("manifest.json")
    md = [
        "# Human audit worksheet",
        "",
        "**Status: not yet performed.** No person has independently audited fineprint's records. The 40-link "
        "audit in `evidence/historical/frozen/audit_worksheet.md` was carried out by the AI assistant that built "
        "the project, using its own code paths. It is useful as a self-check, not as independent verification.",
        "",
        "This worksheet lets a person check a seeded random sample using only public sources (DailyMed, FDA), "
        "without running fineprint. Record each verdict in "
        "[`human_audit_verdicts.csv`](human_audit_verdicts.csv): `VERIFIED`, `FAILED` (say what differs) or "
        "`CANNOT_TELL` (say why). Expect about 2–3 hours.",
        "",
        f"- Sample seed: `{SEED}` (regenerate with `python -I scripts/make_human_audit_worksheet.py`).",
        f"- Current graph: DailyMed release {man['datasets']['current']['dailymed_release']}, FDA registration files "
        f"as of {man['datasets']['current']['fda_registration_as_of']}. Labels change: if DailyMed now shows a newer "
        "version, check the exact version through the FDA XML link, which is fixed by document ID.",
        f"- Historical replay: only label versions published on or before {hist['cutoff']}.",
        "- Opening the XML: any browser shows it; search the page for the DUNS. The XML location is an XPath; "
        "`assignedEntity[2]` means the second establishment block, and so on.",
        "- To check a SHA-256 (optional): `certutil -hashfile file.xml SHA256` on Windows, "
        "`shasum -a 256 file.xml` on macOS, `sha256sum file.xml` on Linux.",
        "",
        "## Part 1 · Current graph links (20)",
        "",
    ]
    for s in cur:
        md += md_current(s)
    md += ["## Part 2 · Historical replay packages (11)", ""]
    for s in his:
        md += md_hist(s)
    md += ["## Part 3 · Facility identity (2)", "",
           "### I01 · Rocky Mount, 2022 identity used by the historical replay",
           f"- **fineprint says:** DUNS `093132819` ↔ FEI `{hist['site']['fei']}` ↔ {hist['site']['address']}, from "
           f"FDA's registration file generated {hist['site']['identity_fda_generated']}.",
           f"- **Check:** download the archived file [{hist['site']['identity_source']}]"
           f"({hist['site']['identity_source']}) (expected SHA-256 `{hist['site']['identity_source_sha256']}`) and find "
           "the row with that DUNS.", "",
           "### I02 · McPherson, current identity",
           f"- **fineprint says:** DUNS `030606222` ↔ FEI `1925262` ↔ 1776 North Centennial Drive, McPherson, Kansas.",
           f"- **Check:** search FEI `1925262` in [FDA DECRS]({DECRS_SEARCH}).", ""]
    (REPO / "docs" / "HUMAN_AUDIT_WORKSHEET.md").write_text("\n".join(md), encoding="utf-8", newline="\n")

    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["sample_id", "stratum", "record", "verdict", "auditor_initials", "date_checked", "notes"])
    for s in cur:
        w.writerow([s["id"], s["stratum"], f"evidence {s['e']['evidence_id']} / set {s['e']['set_id']} "
                    f"v{s['d']['version']} / DUNS {s['e']['duns']}", "", "", "", ""])
    for s in his:
        w.writerow([s["id"], s["stratum"], f"package {s['p']['package_ndc_11']}", "", "", "", ""])
    w.writerow(["I01", "identity", "DUNS 093132819 (2022 file)", "", "", "", ""])
    w.writerow(["I02", "identity", "DUNS 030606222 (current)", "", "", "", ""])
    (REPO / "docs" / "human_audit_verdicts.csv").write_text(buf.getvalue(), encoding="utf-8", newline="\n")
    print(f"{len(cur)} current, {len(his)} historical, 2 identity samples")


if __name__ == "__main__":
    sys.exit(main())
