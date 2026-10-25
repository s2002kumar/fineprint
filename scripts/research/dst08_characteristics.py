"""DST-08 post-hoc diagnostic: do eligible source references name the same physical product?

The Implementation Guide (3.2.2.4-3.2.2.9) also requires a product's size, shape, colour, imprint, flavour and scoring
to equal its source's. Rule ``dst08-lineage-v1`` was fixed before the sample was drawn and compares only dosage form and
active ingredients, so this script changes nothing: it reads every ELIGIBLE reference from the lineage schema of the
scratch database, re-reads both products from the release XML (hash-verified), and compares the
``subjectOf/characteristic`` values of their ``manufacturedProduct`` roles.

  SPLIMPRINT  text, compared upper-cased with everything but letters and digits removed ('M;30' equals 'M 30');
              the text as written is kept. A lenient token-set comparison (split on ';', ',' and spaces) is reported
              beside it, because the same mark stated for one side or both ('RX692' against 'RX692;RX692') differs
              in the strict form
  SPLCOLOR, SPLSHAPE, SPLFLAVOR  coded values, compared as sets of codes
  SPLSIZE     exact decimal and unit, no tolerance
  SPLSCORE    the value as written

Per reference: IMPRINT_EQUAL_ALL_EQUAL, IMPRINT_EQUAL_OTHER_DIFFERS, IMPRINT_DIFFERS, NO_IMPRINT_OTHERS_EQUAL,
NO_IMPRINT_OTHER_DIFFERS, NOTHING_COMPARABLE (no characteristic stated on both sides).

  python -I scripts/research/dst08_characteristics.py --db fineprint_dst08
Output: docs/research/dst08/characteristics_diagnostic.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "research"))
import dst08_check_sample as chk  # noqa: E402
import verify_audit_sample as raw  # noqa: E402
from fineprint import config, db, lineage  # noqa: E402

OUT = REPO / "docs" / "research" / "dst08" / "characteristics_diagnostic.json"
MANIFEST = REPO / "docs" / "research" / "dst08" / "sample_manifest.json"
HL7 = lineage.HL7
KEYS = {"SPLIMPRINT": "imprint", "SPLCOLOR": "color", "SPLSHAPE": "shape", "SPLSIZE": "size", "SPLSCORE": "score",
        "SPLFLAVOR": "flavor"}

ELIGIBLE_SQL = """
SELECT r.reference_pk, lower(cd.set_id), cd.version, r.loc, cp.loc, cp.ndc_raw, cd.published_date,
       cf.local_path, cd.member_name, cm.member_sha256, cd.xml_member_name, cd.xml_sha256,
       lower(sd.set_id), sd.version, sp.loc, sp.ndc_raw, sd.published_date,
       sf.local_path, sd.member_name, sm.member_sha256, sd.xml_member_name, sd.xml_sha256, pa.form_code,
       v.direct_tier_status
FROM lineage.source_resolution x
JOIN lineage.source_reference r USING (reference_pk)
JOIN lineage.v_product_coverage v ON v.product_pk = r.product_pk
JOIN national.product cp ON cp.product_pk = r.product_pk
JOIN national.spl_document cd ON cd.document_pk = r.document_pk
JOIN national.archive_member cm ON cm.document_pk = cd.document_pk AND cm.status = 'loaded'
JOIN national.source_file cf ON cf.source_file_id = cm.source_file_id
JOIN national.product sp ON sp.product_pk = x.source_product_pk
JOIN national.spl_document sd ON sd.document_pk = x.source_document_pk
JOIN national.archive_member sm ON sm.document_pk = sd.document_pk AND sm.status = 'loaded'
JOIN national.source_file sf ON sf.source_file_id = sm.source_file_id
LEFT JOIN lineage.product_attributes pa ON pa.product_pk = r.product_pk
WHERE x.status = 'ELIGIBLE'
ORDER BY r.reference_pk"""


def characteristics(holder) -> dict:
    vals: dict[str, list[str]] = defaultdict(list)
    for so in holder.findall(HL7 + "subjectOf"):
        ch = so.find(HL7 + "characteristic")
        code = ch.find(HL7 + "code") if ch is not None else None
        key = KEYS.get(code.get("code")) if code is not None else None
        val = ch.find(HL7 + "value") if key else None
        if val is None:
            continue
        if key == "imprint":
            v = " ".join("".join(val.itertext()).split())
        elif key == "size":
            v = f"{lineage.decimal_text(val.get('value') or '')} {val.get('unit') or ''}".strip()
        else:
            v = val.get("code") or val.get("value") or ""
        if v:
            vals[key].append(v)
    out = {k: sorted(set(v)) for k, v in vals.items()}
    if "imprint" in out:
        out["imprint_raw"] = out["imprint"]
        out["imprint_tokens"] = sorted({re.sub(r"[^0-9A-Z]", "", t.upper()) for v in out["imprint"]
                                        for t in re.split(r"[;,\s]+", v)} - {""})
        out["imprint"] = sorted({re.sub(r"[^0-9A-Z]", "", v.upper()) for v in out["imprint"]} - {""})
        if not out["imprint"]:
            del out["imprint"], out["imprint_tokens"]
    return out


def compare(a: dict, b: dict) -> tuple[str, dict]:
    per = {}
    for k in KEYS.values():
        if k in a and k in b:
            per[k] = "SAME" if a[k] == b[k] else "DIFFERS"
        elif k in a or k in b:
            per[k] = "ONE_SIDE"
    both = {k: v for k, v in per.items() if v in ("SAME", "DIFFERS")}
    others_differ = any(v == "DIFFERS" for k, v in both.items() if k != "imprint")
    if "imprint" in both:
        if both["imprint"] == "DIFFERS":
            return "IMPRINT_DIFFERS", per
        return ("IMPRINT_EQUAL_OTHER_DIFFERS" if others_differ else "IMPRINT_EQUAL_ALL_EQUAL"), per
    if not both:
        return "NOTHING_COMPARABLE", per
    return ("NO_IMPRINT_OTHER_DIFFERS" if others_differ else "NO_IMPRINT_OTHERS_EQUAL"), per


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint_dst08")
    a = ap.parse_args()
    data_dir = config.data_dir()
    with db.connect(a.db) as c:
        rows = c.execute(ELIGIBLE_SQL).fetchall()
        build = c.execute("SELECT build_id, rule_version, code_commit FROM lineage.build WHERE status = 'completed' "
                          "ORDER BY build_id DESC LIMIT 1").fetchone()
    need: dict[tuple, set] = defaultdict(set)          # document location -> product locs to read
    for r in rows:
        need[tuple(r[7:12])].add(r[4])
        need[tuple(r[17:22])].add(r[14])
    found: dict[tuple, dict] = {}
    by_part: dict[str, list] = defaultdict(list)
    for loc in need:
        by_part[loc[0]].append(loc)
    for part_path, docs in sorted(by_part.items()):
        with zipfile.ZipFile(data_dir / part_path) as part:
            for loc in sorted(docs, key=lambda d: d[1]):
                root = raw.parse_xml(lineage._read_xml(data_dir, *loc, part))
                for ploc in need[loc]:
                    # characteristics hang off the manufacturedProduct ROLE (subject/manufacturedProduct/subjectOf),
                    # the parent of the product element whose location the parser stores
                    el = chk.find_by_loc(root, ploc.rsplit("/", 1)[0])
                    found[(loc, ploc)] = characteristics(el) if el is not None else {"missing": True}
    tally, by_temporal, by_form = Counter(), defaultdict(Counter), defaultdict(Counter)
    per_key = defaultdict(Counter)
    results, examples = {}, defaultdict(list)
    lenient, not_direct_conflicts = Counter(), Counter()
    for r in rows:
        ca, cb = found[(tuple(r[7:12]), r[4])], found[(tuple(r[17:22]), r[14])]
        outcome, per = compare(ca, cb)
        tally[outcome] += 1
        if per.get("imprint") == "DIFFERS":
            lenient["imprint_token_sets_equal" if ca["imprint_tokens"] == cb["imprint_tokens"]
                    else "imprint_token_sets_differ"] += 1
        if outcome in ("IMPRINT_DIFFERS", "IMPRINT_EQUAL_OTHER_DIFFERS", "NO_IMPRINT_OTHER_DIFFERS") and r[23] != "DIRECT":
            not_direct_conflicts[outcome] += 1
        newer = "source_newer" if (r[16] and r[6] and r[16] > r[6]) else "source_not_newer"
        by_temporal[newer][outcome] += 1
        by_form[r[22] or "none"][outcome] += 1
        for k, v in per.items():
            per_key[k][v] += 1
        key = (r[1], r[2], r[3])
        results[key] = {"outcome": outcome, "per_characteristic": per, "citing": ca, "source": cb}
        if outcome in ("IMPRINT_DIFFERS", "IMPRINT_EQUAL_OTHER_DIFFERS", "NO_IMPRINT_OTHER_DIFFERS") and len(examples[outcome]) < 15:
            examples[outcome].append({"citing_ndc": r[5], "citing_set_id": r[1], "citing_version": r[2],
                                      "citing_published": r[6], "source_ndc": r[15], "source_set_id": r[12],
                                      "source_version": r[13], "source_published": r[16], "citing": ca, "source": cb,
                                      "per_characteristic": per})
    sample = {}
    for s in json.loads(MANIFEST.read_text(encoding="utf-8"))["sample"]:
        hit = results.get((s["set_id"].lower(), int(s["version"]), s["ref_loc"]))
        if hit:
            sample[s["sample_id"]] = {"outcome": hit["outcome"], "per_characteristic": hit["per_characteristic"],
                                      "citing_imprint": hit["citing"].get("imprint_raw"),
                                      "source_imprint": hit["source"].get("imprint_raw")}
    out = {
        "generated_at": raw.utc_now(), "note": "post-hoc diagnostic; rule dst08-lineage-v1 and eligibility unchanged",
        "lineage_build": {"build_id": build[0], "rule_version": build[1], "code_commit": build[2]},
        "eligible_references": len(rows), "documents_read": len(need), "outcomes": dict(tally.most_common()),
        "per_characteristic": {k: dict(v) for k, v in sorted(per_key.items())},
        "strict_imprint_differences_by_lenient_comparison": dict(lenient),
        "conflicting_references_on_products_not_direct": dict(not_direct_conflicts),
        # every citing product carries exactly one reference (lineage_build.json), so references are products here
        "source_linked_products_now": sum(r[23] != "DIRECT" for r in rows),
        "source_linked_products_if_conflicts_were_excluded":
            sum(r[23] != "DIRECT" for r in rows) - sum(not_direct_conflicts.values()),
        "outcomes_by_source_newer_than_citing": {k: dict(v.most_common()) for k, v in sorted(by_temporal.items())},
        "outcomes_by_citing_form_top10": {k: dict(v.most_common()) for k, v in
                                          sorted(by_form.items(), key=lambda kv: -sum(kv[1].values()))[:10]},
        "sample_eligible": dict(sorted(sample.items())), "examples": dict(examples),
    }
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("eligible_references", "documents_read", "outcomes", "per_characteristic",
                                          "outcomes_by_source_newer_than_citing")}, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
