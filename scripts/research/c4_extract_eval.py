"""Rules-versus-LLM free-text extraction experiment (research workstream C4), extraction step only.

Question: on the 120 frozen sample labels, does a tightly constrained LLM extract the physically-manufacturing
company (and its printed location) from label text better than the deterministic baseline in
scripts/research/coverage_diagnose.py? Facility matching is evaluated separately and deterministically.

  --prepare   write one input file per batch under $FINEPRINT_DATA/research/c4/ (label text: the sections that carry
              signature blocks, each truncated to its last 1,500 characters) plus the baseline's answers.
  --score     score the baseline and the LLM answers (batch_*.json written by the LLM step) against the frozen gold
              file docs/research/c4_gold_makers.json; write docs/research/c4_results.json.

The gold file was adjudicated by the AI assistant from the label text before either method was scored; the LLM is a
Claude subagent run inside this session (no API charge was incurred). Both facts limit independence and are
reported as such.
"""

from __future__ import annotations

import argparse
import glob
import io
import json
import re
import sys
import time
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "research"))
import coverage_diagnose as cd  # noqa: E402
import verify_audit_sample as raw  # noqa: E402

D = REPO / "docs" / "research"
WORK = raw.DATA / "research" / "c4"
SIG_SECTIONS = {"34069-5", "34076-0", "42229-5", "51945-4", "42231-1", "42230-3", "88436-1", "34093-5", "44425-7", "59845-8",
                "68498-5"}
TAIL = 1000
BATCH = 20


KEYWORDS = re.compile(r"manufactur|mfd|mfg|distribut|market|made in|product of|produced|packed|packaged|labeled|labelled|"
                      r"repackaged|relabeled|imported", re.I)
LABEL_CAP = 4000


STRONG = re.compile(r"manufactur|mfd|mfg", re.I)
WINDOW = 500
LABEL_CAP = 6000


def label_text(root) -> str:
    """Declared pre-filter, identical for both methods: a window of WINDOW characters either side of every keyword
    match in every section, overlapping windows merged, windows holding a manufacturing keyword first, at most
    LABEL_CAP characters per label. (Round 1 used whole sections in document order capped at 4,000 characters,
    which dropped the signature block of several labels; its outputs are kept under c4/round1 and not scored.)"""
    windows = []
    for s in cd.section_texts(root):
        t = s["text"] or ""
        spans = []
        for m in KEYWORDS.finditer(t):
            a, b = max(0, m.start() - WINDOW), min(len(t), m.end() + WINDOW)
            if spans and a <= spans[-1][1]:
                spans[-1][1] = max(spans[-1][1], b)
            else:
                spans.append([a, b])
        for a, b in spans:
            w = t[a:b]
            windows.append((0 if STRONG.search(w) else 1, s["i"], a,
                            f"[section {s['code'] or 'none'} {s['title'] or ''} @{a}] {'…' if a else ''}{w}{'…' if b < len(t) else ''}"))
    windows.sort()
    parts, total = [], 0
    for _, _, _, chunk in windows:
        if total + len(chunk) > LABEL_CAP:
            continue
        parts.append(chunk)
        total += len(chunk)
    return "\n".join(parts)


def tokens(s: str | None) -> set[str]:
    if not s:
        return set()
    s = cd.norm_name(s)
    return {t for t in s.split() if len(t) > 2 and t not in {"THE", "AND", "FOR", "LTD", "INC", "LLC"}}


def company_match(pred: str | None, gold: str | None) -> bool:
    """Normalised token overlap: the prediction must contain at least two thirds of the gold's distinctive tokens."""
    if not gold or not pred:
        return False
    g, p = tokens(gold), tokens(pred)
    if not g:
        return cd.norm_name(pred) == cd.norm_name(gold)
    return len(g & p) >= max(1, round(len(g) * 2 / 3))


def city_token(loc: str | None) -> str | None:
    if not loc:
        return None
    m = re.search(r"([A-Za-z][A-Za-z .'-]{2,}?),?\s+(?:[A-Z]{2}|[A-Z][a-z]+)\s+\d{5}", loc)
    if m:
        return m.group(1).strip().upper()
    return None


def location_match(pred: str | None, gold: str | None) -> bool | None:
    if not gold:
        return None
    if not pred:
        return False
    gp, pp = tokens(gold), tokens(pred)
    return bool(gp) and len(gp & pp) >= max(1, round(len(gp) / 2))


def prepare():
    man = json.loads((D / "coverage_sample_manifest.json").read_text("utf-8"))
    cases = {c["sample_id"]: c for c in json.loads((D / "coverage_cases.json").read_text("utf-8"))["cases"]}
    parts = {p.name: p for p in (raw.DATA / "raw" / "dailymed" / "human_rx_full").glob("*/dm_spl_release_human_rx_part*.zip")}
    WORK.mkdir(parents=True, exist_ok=True)
    texts, baseline = {}, {}
    for s in man["products"]:
        with zipfile.ZipFile(parts[s["part"]]) as outer:
            data = outer.read(s["member_name"])
        with zipfile.ZipFile(io.BytesIO(data)) as inner:
            xml = inner.read(s["xml_member_name"])
        assert raw.sha256(xml) == s["xml_sha256"]
        root = raw.parse_xml(xml)
        txt = label_text(root)
        texts[s["sample_id"]] = txt
        # the deterministic baseline runs on exactly the excerpt the LLM sees
        hits = cd.free_text_hits([{"i": 0, "code": None, "title": None, "text": txt}])
        b = [x for x in cd.baseline_extract(hits) if x["role"] in ("MANUFACTURED_BY", "MANUFACTURER")]
        if b:
            h = [x for x in hits if x["role"] in ("MANUFACTURED_BY", "MANUFACTURER")][0]
            baseline[s["sample_id"]] = {"maker_named": True, "maker_company": b[0]["company"],
                                        "maker_location": b[0]["location"] or None, "role": b[0]["role"],
                                        "supporting_quote": h["statement"][:200]}
        else:
            baseline[s["sample_id"]] = {"maker_named": False, "maker_company": None, "maker_location": None, "role": "NONE",
                                        "supporting_quote": None}
    ids = sorted(texts)
    for i in range(0, len(ids), BATCH):
        batch = ids[i: i + BATCH]
        n = i // BATCH + 1
        out = ["# Label texts for extraction. Each label starts with '=== <id> ==='.", ""]
        for sid in batch:
            out += [f"=== {sid} ===", texts[sid], ""]
        (WORK / f"batch_{n}.txt").write_text("\n".join(out), encoding="utf-8", newline="\n")
    (WORK / "baseline.json").write_text(json.dumps(baseline, indent=1), encoding="utf-8", newline="\n")
    (WORK / "texts.json").write_text(json.dumps(texts), encoding="utf-8", newline="\n")
    print(f"{len(ids)} labels in {(len(ids) + BATCH - 1) // BATCH} batches under {WORK}; total chars {sum(len(t) for t in texts.values())}")


def score_method(pred: dict, gold: dict, texts: dict) -> dict:
    m = {"n": 0, "maker_named_correct": 0, "true_positive_company": 0, "false_assertion_no_maker": 0,
         "wrong_company": 0, "missed_maker": 0, "location_correct": 0, "location_evaluable": 0,
         "unsupported_quote": 0, "quotes_given": 0, "per_label": {}}
    for sid, g in gold.items():
        p = pred.get(sid) or {"maker_named": False, "maker_company": None, "maker_location": None}
        m["n"] += 1
        named = bool(p.get("maker_named"))
        has_gold = g is not None
        row = {"gold": g, "pred": {k: p.get(k) for k in ("maker_named", "maker_company", "maker_location", "supporting_quote")}}
        if named == has_gold:
            m["maker_named_correct"] += 1
        if named and not has_gold:
            m["false_assertion_no_maker"] += 1
            row["outcome"] = "false_assertion"
        elif not named and has_gold:
            m["missed_maker"] += 1
            row["outcome"] = "missed"
        elif named and has_gold:
            if company_match(p.get("maker_company"), g["maker"]):
                m["true_positive_company"] += 1
                row["outcome"] = "correct_company"
            else:
                m["wrong_company"] += 1
                row["outcome"] = "wrong_company"
            lm = location_match(p.get("maker_location"), g.get("location"))
            if lm is not None:
                m["location_evaluable"] += 1
                m["location_correct"] += int(lm)
        else:
            row["outcome"] = "correct_none"
        q = p.get("supporting_quote")
        if q:
            m["quotes_given"] += 1
            if re.sub(r"\s+", " ", q).strip() not in re.sub(r"\s+", " ", texts.get(sid, "")):
                m["unsupported_quote"] += 1
                row["unsupported_quote"] = True
        m["per_label"][sid] = row
    return m


def facility_matching(gold: dict) -> dict:
    """Deterministic matching of each gold maker to FDA DECRS: exact normalised firm name, then city token."""
    decrs = raw.load_decrs()["current"]
    by_name: dict[str, list] = {}
    for rows in decrs["by_duns"].values():
        for r in rows:
            by_name.setdefault(cd.norm_name(r["firm"]), []).append(r)
    out = {"makers": 0, "exact_name_rows_any": 0, "exact_name_unique_fei": 0, "name_and_city_unique_fei": 0, "no_match": 0,
           "per_label": {}}
    for sid, g in gold.items():
        if not g:
            continue
        out["makers"] += 1
        rows = by_name.get(cd.norm_name(g["maker"]), [])
        feis = sorted({r["fei"] for r in rows if r["fei"]})
        city = city_token(g.get("location"))
        city_rows = [r for r in rows if city and city in (r["address"] or "").upper()]
        cfeis = sorted({r["fei"] for r in city_rows if r["fei"]})
        if rows:
            out["exact_name_rows_any"] += 1
        else:
            out["no_match"] += 1
        if len(feis) == 1:
            out["exact_name_unique_fei"] += 1
        if len(cfeis) == 1:
            out["name_and_city_unique_fei"] += 1
        out["per_label"][sid] = {"maker": g["maker"], "city_token": city, "exact_name_feis": feis[:10], "name_and_city_feis": cfeis[:10]}
    return out


def score():
    gold_full = json.loads((D / "c4_gold_makers.json").read_text("utf-8"))["labels"]
    texts = json.loads((WORK / "texts.json").read_text("utf-8"))
    # the gold was adjudicated on the whole label; a maker whose name is not in the excerpt is unreachable for
    # both methods and is scored as "no maker in excerpt" (counted separately)
    gold, not_in_excerpt = {}, []
    for sid, g in gold_full.items():
        if g and not company_match(texts.get(sid, ""), g["maker"]):
            not_in_excerpt.append(sid)
            gold[sid] = None
        else:
            gold[sid] = g
    baseline = json.loads((WORK / "baseline.json").read_text("utf-8"))
    llm, timing = {}, []
    for f in sorted(glob.glob(str(WORK / "batch_*.json"))):
        d = json.loads(Path(f).read_text("utf-8"))
        llm.update(d.get("labels", {}))
        if "seconds" in d:
            timing.append({"batch": Path(f).name, "seconds": d["seconds"], "labels": len(d.get("labels", {}))})
    res = {"generated_at": raw.utc_now(), "gold_labels": len(gold), "gold_with_maker": sum(1 for g in gold.values() if g),
           "gold_makers_on_full_label": sum(1 for g in gold_full.values() if g),
           "gold_makers_not_in_excerpt": not_in_excerpt,
           "baseline": score_method(baseline, gold, texts), "llm": score_method(llm, gold, texts) if llm else None,
           "llm_labels_answered": len(llm), "llm_timing": timing,
           "facility_matching_of_gold_makers": facility_matching(gold),
           "caveats": ["gold adjudicated by the AI assistant, not a human",
                       "LLM = Claude subagent inside this session; same model family as the adjudicator; no API charge",
                       "extraction only: no facility is verified by any method here"]}
    (D / "c4_results.json").write_text(json.dumps(res, indent=1), encoding="utf-8", newline="\n")
    for k in ("baseline", "llm"):
        if res[k]:
            print(k, {kk: v for kk, v in res[k].items() if kk != "per_label"})
    print("facility", {k: v for k, v in res["facility_matching_of_gold_makers"].items() if k != "per_label"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--score", action="store_true")
    a = ap.parse_args()
    if a.prepare:
        prepare()
    if a.score:
        score()


if __name__ == "__main__":
    sys.exit(main())
