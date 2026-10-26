"""Root-cause counts and population-weighted estimates from the adjudicated coverage sample (research workstream C3).

Inputs: docs/research/coverage_sample_manifest.json (frozen; stratum populations) and
docs/research/coverage_adjudication.csv (hand-written, AI-assisted adjudication, one row per sampled product).

The sample is stratified with deliberate oversampling of small strata, so population estimates weight each stratum
by its population size. Per-stratum proportions get Wilson 95% intervals; the weighted total gets a stratified
normal-approximation interval with finite-population correction. With 15-25 products per stratum these intervals are
wide; a zero count is reported with the rule-of-three upper bound. None of this is a precision measurement of the
graph: it describes why evidence is missing, not whether any link is wrong.

  python -I scripts/research/coverage_estimates.py
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
D = REPO / "docs" / "research"
CATEGORIES = {"A": "evidence truly absent from the inspected label",
              "B": "manufacturing information in structured XML but missed by the parser",
              "C": "manufacturing information in free text, absent from structured establishment operations",
              "D": "manufacturing operation present but not attributable to a specific product",
              "E": "facility identity missing, stale or conflicting",
              "F": "data/version inconsistency or another error",
              "G": "unresolved after inspection",
              "P": "positive control: structured MANUFACTURE present and correct"}
RECOVER = ["parser_omission", "structured_cross_reference", "free_text_candidate", "identity_blocker", "genuine_absence",
           "human_judgment", "positive_control"]
NO_EVIDENCE = ["OTHER_OPERATIONS_ONLY", "NO_ESTABLISHMENT_BLOCK", "ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT",
               "ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT"]


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def main():
    man = json.loads((D / "coverage_sample_manifest.json").read_text("utf-8"))
    pop = man["dataset"]["population_counts"]
    rows = list(csv.DictReader((D / "coverage_adjudication.csv").open(encoding="utf-8", newline="")))
    by_id = {p["sample_id"]: p for p in man["products"]}
    assert len(rows) == len(by_id) == 120, (len(rows), len(by_id))
    assert {r["sample_id"] for r in rows} == set(by_id)
    for r in rows:
        assert r["primary"] in CATEGORIES, r
        assert r["recoverable"] in RECOVER, r
        assert r["stratum"] == by_id[r["sample_id"]]["stratum"], r["sample_id"]
    strata = [s["stratum"] for s in man["plan"]]
    out = {"n": len(rows), "strata": {}, "weighted": {}, "definitions": {"categories": CATEGORIES, "recoverability": RECOVER}}
    for s in strata:
        rs = [r for r in rows if r["stratum"] == s]
        n = len(rs)
        cats = {c: sum(1 for r in rs if r["primary"] == c) for c in CATEGORIES}
        rec = {c: sum(1 for r in rs if r["recoverable"] == c) for c in RECOVER}
        flags = {"physical_text_claim": sum(1 for r in rs if r["physical_text_claim"] == "yes"),
                 "raw_candidate_link": sum(1 for r in rs if r["raw_candidate_link"] == "yes"),
                 "verified_link": sum(1 for r in rs if r["verified_link"] == "yes"),
                 "structured_source_ndc": sum(1 for r in rs if r["structured_source_ndc"] == "yes"),
                 "newer_version_today": sum(1 for r in rs if r["newer_version_today"] == "yes")}
        out["strata"][s] = {"population": pop[s], "n": n, "primary": cats, "recoverable": rec, "flags": flags,
                            "intervals": {k: {"k": v, "p": round(v / n, 3), "wilson95": [round(x, 3) for x in wilson(v, n)],
                                              "rule_of_three_upper": round(3 / n, 3) if v == 0 else None}
                                          for k, v in {**{f"primary_{c}": cats[c] for c in CATEGORIES},
                                                       **{f"recoverable_{c}": rec[c] for c in RECOVER},
                                                       **{f"flag_{c}": flags[c] for c in flags}}.items()}}
    # population-weighted totals over the four no-evidence strata (54,457 products) and over all seven strata
    def weighted(keyfn, strata_subset):
        est, var, lo, hi = 0.0, 0.0, 0.0, 0.0
        for s in strata_subset:
            st = out["strata"][s]
            N, n = st["population"], st["n"]
            k = keyfn(st)
            p = k / n
            est += N * p
            var += N * N * p * (1 - p) / n * (1 - n / N)
            w = wilson(k, n)
            lo += N * w[0]
            hi += N * w[1]
        z = 1.959964
        return {"estimate": round(est), "normal95": [round(max(0.0, est - z * math.sqrt(var))), round(est + z * math.sqrt(var))],
                "sum_of_wilson95": [round(lo), round(hi)], "denominator": sum(out["strata"][s]["population"] for s in strata_subset)}
    for name, subset in (("no_evidence_54457", NO_EVIDENCE), ("all_seven_strata", strata)):
        out["weighted"][name] = {
            **{f"primary_{c}": weighted(lambda st, c=c: st["primary"][c], subset) for c in CATEGORIES},
            **{f"recoverable_{c}": weighted(lambda st, c=c: st["recoverable"][c], subset) for c in RECOVER},
            **{f"flag_{c}": weighted(lambda st, c=c: st["flags"][c], subset) for c in
               ("physical_text_claim", "raw_candidate_link", "verified_link", "structured_source_ndc", "newer_version_today")}}
    (D / "coverage_estimates.json").write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps({s: {"n": v["n"], "primary": v["primary"], "recoverable": v["recoverable"], "flags": v["flags"]}
                      for s, v in out["strata"].items()}, indent=1))
    print(json.dumps({k: {kk: vv["estimate"] for kk, vv in v.items()} for k, v in out["weighted"].items()}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
