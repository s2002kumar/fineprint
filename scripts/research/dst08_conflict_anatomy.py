"""DST-08 final validation: what the rule v2 CONFIRMED_CONFLICT references actually differ in.

  python -I scripts/research/dst08_conflict_anatomy.py --db fineprint_dst08
Output: docs/research/dst08/conflict_anatomy.json

A confirmed conflict means the citing label and the source label in force when it was published describe the product
differently. That is not the same as a false link, so each one is put in exactly one descriptive category (first that
applies), comparing the citing product with the applicable source version (read from the hash-verified archive cache):

  SIBLING_STRENGTH_IMPRINT    the citing imprint is the imprint of another product in the same source label (the
                              citing label describes a different strength of the cited source)
  IMPRINT_AND_OTHER_FIELDS    the imprint and at least one other characteristic differ
  IMPRINT_ONE_CHARACTER       only the imprint differs, by one character in the normalised text ('O;25' / '0;25')
  IMPRINT_MARKS_CONTAINED     only the imprint differs, and one side's marks contain the other's ('IG;228' /
                              '100;mg;IG;228')
  IMPRINT_DISTINCT            only the imprint differs, otherwise ('IG;209' / 'D;74')
  CODED_FIELD_ONLY            the imprint is equal or absent; only colour, shape, score, size or flavour differs
Nothing here changes a classification; the categories describe the evidence for the report and the reviewer.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from fineprint import config, db, lineage  # noqa: E402

OUT = REPO / "docs" / "research" / "dst08" / "conflict_anatomy.json"
HISTORY = REPO / "docs" / "research" / "dst08" / "source_history_manifest.json"


def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def category(at: dict, cch: dict, ach: dict, siblings: list[str]) -> str:
    differing = sorted(k for k, v in at.items() if v == "DIFFERS")
    if "imprint" not in differing:
        return "CODED_FIELD_ONLY"
    if siblings:
        return "SIBLING_STRENGTH_IMPRINT"
    if differing != ["imprint"]:
        return "IMPRINT_AND_OTHER_FIELDS"
    if min(edit_distance(a, b) for a in cch["imprint"] for b in ach["imprint"]) == 1:
        return "IMPRINT_ONE_CHARACTER"
    a, b = set(cch["imprint_tokens"]), set(ach["imprint_tokens"])
    if a < b or b < a:
        return "IMPRINT_MARKS_CONTAINED"
    return "IMPRINT_DISTINCT"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint_dst08")
    a = ap.parse_args()
    cache = config.data_dir() / "research" / "dst08" / "history"
    docs = {(d["set_id"], d["version"]): d for d in json.loads(HISTORY.read_text(encoding="utf-8"))["documents"]}
    with db.connect(a.db) as c:
        rows = c.execute(
            """SELECT citing_ndc, citing_set_id, citing_version, citing_published_at, source_ndc, source_set_id,
                      applicable_version, applicable_published_at, at_applicable, citing_characteristics,
                      applicable_characteristics, sites_at_applicable, sites_now_direct
               FROM lineage.version_check WHERE classification = 'CONFIRMED_CONFLICT' ORDER BY citing_ndc""").fetchall()
    cases, tally = [], Counter()
    for (citing, cset, cver, cpub, src, sset, ver, apub, at, cch, ach, then, now) in rows:
        siblings = []
        if "imprint" in cch:
            label = lineage.read_label_version(lineage._manifest_xml(cache, docs[(sset, ver)]))
            siblings = sorted(p["code"] for p in label["products"]
                              if lineage.ndc.to_product_5_4(p["code"]) != lineage.ndc.to_product_5_4(src)
                              and set(p["characteristics"].get("imprint", [])) & set(cch["imprint"]))
        cat = category(at, cch, ach, siblings)
        tally[cat] += 1
        cases.append({"citing_ndc": citing, "citing": f"{cset} v{cver} ({cpub})", "source_ndc": src,
                      "applicable": f"{sset} v{ver} ({apub})", "category": cat,
                      "differing": sorted(k for k, v in at.items() if v == "DIFFERS"),
                      "citing_imprint": cch.get("imprint_raw"), "source_imprint": ach.get("imprint_raw"),
                      "sibling_products_with_citing_imprint": siblings,
                      "sites_then_continue_now": bool(set(then or ()) & set(now)) if then else None})
    out = {"confirmed_conflicts": len(cases), "by_category": dict(tally.most_common()),
           "rule": __doc__.split("applies), ")[1].split("Nothing here")[0].strip(), "cases": cases}
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out["by_category"]))


if __name__ == "__main__":
    sys.exit(main())
