"""Pure rules for the DST-04B historical evaluation (plan amendment A5). No I/O, no database.

Everything here was fixed before the outcome list was retrieved; tests pin the behaviour.
"""

from __future__ import annotations

import hashlib
import re

from . import ndc, spl

ROCKY_MOUNT = "093132819"
MANUFACTURE = spl.MANUFACTURE_CODE
PRECEDENCE = ("DIRECT", "KIT_PART_ONLY", "OTHER_SITE", "RM_SECONDARY_ONLY", "UNKNOWN_MANUFACTURE_WITHOUT_DUNS",
              "UNKNOWN_NO_ESTABLISHMENT", "UNKNOWN_UNSCOPED_OPERATION", "UNKNOWN_NO_MANUFACTURE_OP")
INJECTABLE_ROUTES = {"INTRAVENOUS", "INTRAMUSCULAR", "SUBCUTANEOUS", "INTRADERMAL", "INTRATHECAL", "EPIDURAL",
                     "INTRA-ARTERIAL", "INTRA-ARTICULAR", "INTRACARDIAC", "INTRACAVERNOUS", "INTRAOSSEOUS",
                     "INTRAPERITONEAL", "INTRAVENTRICULAR", "INTRAVITREAL", "INTRALESIONAL", "INFILTRATION",
                     "PERINEURAL", "INTRACAMERAL", "INTRASPINAL"}


def product_evidence(doc: dict) -> dict:
    """Per raw product code: the operation evidence needed by classify() (one parsed SPL)."""
    edges = spl.operation_edges(doc)
    unscoped = any(e["product_code"] is None for e in edges)
    out = {}
    for p in doc["products"]:
        code = p["product_ndc_raw"]
        part_codes = {part["code"] for part in p["parts"] if part["code"]}
        ev = out.setdefault(code, {"mfg_duns": set(), "mfg_without_duns": False, "rm_ops": set(), "rm_mfg_locs": [],
                                   "rm_part_mfg": False, "form": p["form"],
                                   "routes": {r["display_name"] for r in p["routes"] if r["display_name"]}})
        ev["routes"] |= {r["display_name"] for r in p["routes"] if r["display_name"]}
        for e in edges:
            if e["product_code"] == code:
                if e["operation_code"] == MANUFACTURE:
                    if e["duns"]:
                        ev["mfg_duns"].add(e["duns"])
                    else:
                        ev["mfg_without_duns"] = True
                if e["duns"] == ROCKY_MOUNT:
                    ev["rm_ops"].add(e["operation_code"])
                    if e["operation_code"] == MANUFACTURE:
                        ev["rm_mfg_locs"].append(e["loc"])
            elif e["product_code"] in part_codes and e["duns"] == ROCKY_MOUNT and e["operation_code"] == MANUFACTURE:
                ev["rm_part_mfg"] = True
    has_block = bool(spl.establishments(doc))
    for ev in out.values():
        ev["has_establishment_block"] = has_block
        ev["document_has_unscoped_operation"] = unscoped
    return out


def classify(ev: dict) -> str:
    """A5 §4 precedence for one product's evidence in one admissible document."""
    if ROCKY_MOUNT in ev["mfg_duns"]:
        return "DIRECT"
    if ev["rm_part_mfg"]:
        return "KIT_PART_ONLY"
    if ev["mfg_duns"]:
        return "OTHER_SITE"
    if ev["rm_ops"]:
        return "RM_SECONDARY_ONLY"
    if ev["mfg_without_duns"]:
        return "UNKNOWN_MANUFACTURE_WITHOUT_DUNS"
    if not ev["has_establishment_block"]:
        return "UNKNOWN_NO_ESTABLISHMENT"
    if ev["document_has_unscoped_operation"]:
        return "UNKNOWN_UNSCOPED_OPERATION"
    return "UNKNOWN_NO_MANUFACTURE_OP"


def combine(classes: list[str]) -> str:
    """Multi-provenance package: the highest-precedence class wins (flag if ANY row is DIRECT)."""
    return min(classes, key=PRECEDENCE.index)


def injectable(form: str | None, routes) -> str:
    """A5/§5 B2 rule: 'INJECTABLE', 'NOT_INJECTABLE' or 'UNCLASSIFIED' (no form and no route)."""
    routes = {r.upper() for r in routes or ()}
    if form and "INJECT" in form.upper():
        return "INJECTABLE"
    if routes & INJECTABLE_ROUTES:
        return "INJECTABLE"
    if not form and not routes:
        return "UNCLASSIFIED"
    return "NOT_INJECTABLE"


# Tokens must be delimited (no adjacent letters, digits, '_' or '-'), so lot/serial fragments are not NDCs.
NDC_TOKEN = re.compile(r"(?<![\w-])(\d{4,5}-\d{3,4}-\d{1,2}|\d{11})(?![\w-])")


def normalize_outcome_ndc(token: str) -> str | None:
    """A5 §7: hyphenated 10-digit -> 5-4-2; hyphenated 5-4-2 kept; bare 11 digits split 5-4-2; else None."""
    t = token.strip()
    if re.fullmatch(r"\d{11}", t):
        return f"{t[:5]}-{t[5:9]}-{t[9:]}"
    if re.fullmatch(r"\d{5}-\d{4}-\d{2}", t):
        return t
    return ndc.to_11_digit(t)


def audit_order(seed: str, key: str) -> str:
    return hashlib.sha256(f"{seed}|{key}".encode()).hexdigest()


def metrics(cohort: set[str], flags: set[str], positives: set[str]) -> dict:
    """A5 §8. 'overlap_density' is |flags ∩ P| / N and is NOT a precision."""
    n, m = len(flags), len(cohort)
    x = len(flags & positives)
    p_in = positives & cohort
    return {
        "N": n, "cohort_size": m, "positives": len(positives), "positives_in_cohort": len(p_in),
        "X": x,
        "recall_named": round(x / len(positives), 4) if positives else None,
        "recall_panel_conditional": round(len(flags & p_in) / len(p_in), 4) if p_in else None,
        "reduction_vs_B1": round(1 - n / m, 4) if m else None,
        "overlap_density": round(x / n, 4) if n else None,
    }


def size_to_match_recall(target_recall: float | None, baseline: dict) -> float | None:
    """Expected list size if the baseline list were uniformly subsampled to reach target recall."""
    r = baseline.get("recall_named")
    if not target_recall or not r:
        return None
    return round(min(1.0, target_recall / r) * baseline["N"], 1)
