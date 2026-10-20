"""DST-04B link audit worksheet (plan A5 §6), produced BEFORE unsealing.

For each pre-drawn sample package it re-reads the hash-verified raw cutoff document and extracts
operations with an independent ElementTree walk (not fineprint.spl's edge logic), then quotes the
raw XML. The auditor records verdicts in audit_verdicts.json.

  python -I scripts/hist_dst04b_audit_worksheet.py
"""

import io
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))  # works under python -I
sys.path.insert(0, str(REPO / "scripts"))
from fineprint import config  # noqa: E402
from fineprint import historical_eval as he  # noqa: E402
from hist_dst04b_freeze import load_document  # noqa: E402  (same hash-verified loader as the freeze)

NS = "{urn:hl7-org:v3}"
FROZEN = REPO / "evidence" / "historical" / "frozen"


def raw_xml(root, sid, row):
    """Return raw XML bytes of the cutoff document (hash-verified by load_document)."""
    import zipfile
    doc, prov = load_document(root, sid, row)
    d, status = row["document"], row["cutoff_status"]
    if status == "fetched":
        z = zipfile.ZipFile(root / "spl" / f"{sid}_v{row['cutoff_version']}.zip")
    elif status == "cutoff_version_from_monthly_archive":
        arch = d["archive"].rsplit("_", 1)[-1][:-4]
        z = zipfile.ZipFile(io.BytesIO((root / "monthly" / arch / d["member"].replace("/", "__")).read_bytes()))
    else:
        return (root / "fda_spl" / f"{d['document_id']}.xml").read_bytes(), prov
    name = [n for n in z.namelist() if n.lower().endswith(".xml")][0]
    return z.read(name), prov


def independent_operations(xml: bytes, code: str):
    """Walk every <performance> under <author>; return (duns, op_code, op_name) for this product code."""
    root = ET.fromstring(xml)
    parent = {c: p for p in root.iter() for c in p}
    ops = []
    for perf in root.iter(f"{NS}performance"):
        codes = [c.get("code") for c in perf.iter(f"{NS}code") if c.get("codeSystem") == "2.16.840.1.113883.6.69"]
        if code not in codes:
            continue
        ent = parent[perf]
        org = ent.find(f"{NS}assignedOrganization")
        duns = next((i.get("extension") for i in (org.findall(f"{NS}id") if org is not None else [])
                     if i.get("root") == "1.3.6.1.4.1.519.1"), None)
        act = perf.find(f"{NS}actDefinition/{NS}code")
        ops.append((duns, act.get("code") if act is not None else None,
                    act.get("displayName") if act is not None else None, perf))
    return ops


def main():
    draft = json.loads((REPO / "evidence/historical/dst04a_candidates_draft.json").read_text(encoding="utf-8"))
    cohort = json.loads((FROZEN / "cohort_E.json").read_text(encoding="utf-8"))["packages"]
    sample = json.loads((FROZEN / "audit_sample.json").read_text(encoding="utf-8"))["sample"]
    root = config.data_dir() / "raw" / "historical" / "frame_reconcile"
    lines = ["# DST-04B link audit worksheet (generated before unsealing)", "",
             "Independent extraction: raw ElementTree walk of every `<performance>` element; DUNS taken from the "
             "enclosing `assignedOrganization`. Raw source re-hashed before use.", ""]
    auto = []
    for i, s in enumerate(sample, 1):
        e = cohort[s["package_ndc_11"]]
        lines.append(f"## {i}. {s['package_ndc_11']} — frozen class {e['classification']} ({s['bucket']})")
        rows_ok = []
        for p in e["provenance"]:
            xml, prov = raw_xml(root, p["set_id"], draft["sets"][p["set_id"]])
            ops = independent_operations(xml, p["product_ndc_raw"])
            ind_mfg = sorted({d for d, c, _, _ in ops if c == he.MANUFACTURE and d})
            ind_rm = sorted({c for d, c, _, _ in ops if d == he.ROCKY_MOUNT})
            ind_class_direct = he.ROCKY_MOUNT in ind_mfg
            agrees = (ind_class_direct == (p["classification"] == "DIRECT")
                      and ind_mfg == p["manufacture_duns"])
            rows_ok.append(agrees)
            lines.append(f"- set `{p['set_id']}` v{p['version']} ({prov['kind']}, published {prov['published_date']}, "
                         f"sha256 `{prov['sha256'][:16]}…`), package `{p['package_ndc_raw']}` in product "
                         f"`{p['product_ndc_raw']}` — form {p['form']}")
            lines.append(f"  - independent: MANUFACTURE DUNS {ind_mfg or 'none'}; Rocky Mount ops {ind_rm or 'none'}; "
                         f"all ops {sorted({(d, n) for d, _, n, _ in ops}) or 'none'}")
            lines.append(f"  - frozen: MANUFACTURE DUNS {p['manufacture_duns'] or 'none'}; class {p['classification']}"
                         f" → independent extraction {'AGREES' if agrees else 'DISAGREES'}")
            rm_perf = [perf for d, c, _, perf in ops if d == he.ROCKY_MOUNT and c == he.MANUFACTURE]
            if rm_perf:
                ET.register_namespace("", "urn:hl7-org:v3")
                snippet = " ".join(ET.tostring(rm_perf[0], encoding="unicode").split())
                lines.append(f"  - raw: `{snippet[:400]}`")
        auto.append({"package_ndc_11": s["package_ndc_11"], "bucket": s["bucket"],
                     "frozen_classification": e["classification"], "independent_agrees": all(rows_ok)})
        lines.append("")
    (FROZEN / "audit_worksheet.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    (FROZEN / "audit_independent_check.json").write_text(json.dumps(auto, indent=2) + "\n", encoding="utf-8",
                                                         newline="\n")
    print(sum(a["independent_agrees"] for a in auto), "of", len(auto), "independent extractions agree")


if __name__ == "__main__":
    main()
