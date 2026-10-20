"""DST-04B step 2 (plan A5 §7–9): verify the seal, retrieve the outcome appendix, score.

Refuses to run unless every frozen file equals its blob at tag `dst04b-freeze` and the
audit verdicts are committed. The outcome list is a low-inventory WARNING list, not a
manufacturing ground truth: unlisted packages are never treated as negatives.

  python -I scripts/hist_dst04b_unseal_and_score.py --out evidence/historical/evaluation_results.json
"""

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))  # works under python -I
from fineprint import config, net, pdftext  # noqa: E402
from fineprint import historical_eval as he  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402

TAG = "dst04b-freeze"
FROZEN = "evidence/historical/frozen"
OUTCOME_URL = "https://www.fda.gov/media/170647/download"


def git(*a):
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True, check=True).stdout


def verify_seal() -> dict:
    manifest_at_tag = git("show", f"{TAG}:{FROZEN}/FREEZE_MANIFEST.json")
    if (REPO / FROZEN / "FREEZE_MANIFEST.json").read_bytes() != manifest_at_tag:
        raise SystemExit("seal broken: FREEZE_MANIFEST.json differs from the tagged version")
    m = json.loads(manifest_at_tag)
    for name, sha in m["files"].items():
        blob = git("show", f"{TAG}:{FROZEN}/{name}")
        disk = (REPO / FROZEN / name).read_bytes()
        if hashlib.sha256(blob).hexdigest() != sha or disk != blob:
            raise SystemExit(f"seal broken: {name}")
    audit = f"{FROZEN}/audit_verdicts.json"
    git("ls-files", "--error-unmatch", audit)
    if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", audit], cwd=REPO).returncode != 0:
        raise SystemExit("audit verdicts must be committed before unsealing")
    return {"tag": TAG, "tag_commit": git("rev-list", "-n1", TAG).decode().strip(),
            "manifest_sha256": hashlib.sha256(manifest_at_tag).hexdigest(), "files_verified": len(m["files"])}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    seal = verify_seal()
    print("seal verified:", seal, file=sys.stderr)

    # --- unseal: the outcome appendix is retrieved only here ---------------------------------
    dest = config.data_dir() / "raw" / "historical" / "outcome" / "fda_media_170647.pdf"
    if dest.exists():
        pdf = dest.read_bytes()
        retrieved = json.loads(dest.with_name(dest.name + ".json").read_text(encoding="utf-8"))
    else:
        r = net.fetch(OUTCOME_URL, dest)
        retrieved = r.provenance()
        retrieved.pop("path", None)
        dest.with_name(dest.name + ".json").write_text(json.dumps(retrieved), encoding="utf-8", newline="\n")
        pdf = dest.read_bytes()
    pages = pdftext.page_texts(pdf)
    tokens = [(i, t) for i, txt in enumerate(pages, 1) for t in he.extract_ndc_tokens(txt)]
    normalized, unparsed = {}, []
    for page, t in tokens:
        n = he.normalize_outcome_ndc(t)
        if n is None:
            unparsed.append({"page": page, "token": t})
        else:
            normalized.setdefault(n, []).append({"page": page, "token": t})
    P = set(normalized)
    outcome = {"url": OUTCOME_URL, "sha256": hashlib.sha256(pdf).hexdigest(), "bytes": len(pdf),
               "retrieved_at": retrieved.get("retrieved_at"), "last_modified": (retrieved.get("headers") or {})
               .get("last-modified"), "pages": len(pages), "tokens_found": len(tokens),
               "distinct_package_ndc_11": len(P), "unparsed_tokens": unparsed,
               "labeler_segments": dict(Counter(n.split("-")[0] for n in P)),
               "duplicate_mentions": {k: len(v) for k, v in normalized.items() if len(v) > 1},
               "text_layer_chars": sum(len(t) for t in pages)}
    print("outcome:", {k: outcome[k] for k in ("pages", "tokens_found", "distinct_package_ndc_11",
                                                 "labeler_segments")}, file=sys.stderr)
    if not P:
        write_json(a.out, {"seal": seal, "outcome": outcome, "status": "BLOCKED: no package NDCs in text layer"})
        raise SystemExit("no NDCs extracted from the outcome text layer; scoring blocked (no OCR, no guessing)")

    # --- score -------------------------------------------------------------------------------
    E = json.loads((REPO / FROZEN / "cohort_E.json").read_text(encoding="utf-8"))["packages"]
    M_keys = set(json.loads((REPO / FROZEN / "cohort_M.json").read_text(encoding="utf-8"))["packages"])
    draft = json.loads((REPO / "evidence/historical/dst04a_candidates_draft.json").read_text(encoding="utf-8"))
    universe_products = {p["product_ndc_raw"] for p in draft["packages"]}
    excluded_rows = {p["package_ndc_11"]: p["status"] for p in draft["packages"] if p["status"] != "candidate"}
    results = {}
    for name, keys in (("E", set(E)), ("M", M_keys)):
        cohort = {k: E[k] for k in keys}
        flags = {
            "B1_all_hospira_00409": set(cohort),
            "B2_injectables": {k for k, v in cohort.items() if v["b2"] == "INJECTABLE"},
            "graph_rocky_mount_direct": {k for k, v in cohort.items() if v["graph_flag"]},
        }
        m = {meth: he.metrics(set(cohort), f, P) for meth, f in flags.items()}
        g = m["graph_rocky_mount_direct"]["recall_named"]
        for b in ("B1_all_hospira_00409", "B2_injectables"):
            m[b]["expected_size_to_match_graph_recall"] = he.size_to_match_recall(g, m[b])
        hit = P & set(cohort)
        missed = hit - flags["graph_rocky_mount_direct"]
        results[name] = {
            "metrics": m, "B3_already_short": "NOT EVALUABLE (plan A5 §5)",
            "positives_in_cohort_by_class": dict(Counter(cohort[k]["classification"] for k in hit)),
            "positives_in_cohort_not_flagged_by_class": dict(Counter(cohort[k]["classification"] for k in missed)),
            "flagged_not_listed": len(flags["graph_rocky_mount_direct"] - P),
            "positives_in_cohort": sorted(hit), "missed_positives": sorted(missed),
        }
    uncovered = {}
    for n in sorted(P - set(E)):
        seg = n.split("-")
        product_raw = f"{seg[0][1:]}-{seg[1]}" if seg[0].startswith("0") else None  # 00409-xxxx -> 0409-xxxx
        if seg[0] != "00409":
            reason = "other_labeler_code"
        elif n in excluded_rows:
            reason = f"in_universe_but_{excluded_rows[n]}"
        elif product_raw in universe_products:
            reason = "product_in_universe_but_package_absent_from_cutoff_document"
        else:
            reason = "not_in_universe (no admissible pre-cutoff SPL found)"
        uncovered[n] = reason
    out = {"seal": seal, "outcome": outcome, "cohorts": results,
           "uncovered_positives": uncovered, "uncovered_by_reason": dict(Counter(uncovered.values())),
           "caveats": [
               "The outcome is Pfizer's low-inventory warning list after warehouse damage, not a list of products "
               "made at Rocky Mount; unlisted packages are not negatives.",
               "overlap_density is |flags ∩ P| / N and is not precision.",
               "Graph identity: DUNS 093132819 per 2013/2015 SPL filings and the 2022-10-13 registration record; "
               "2023 registration status is not established (plan A2).",
           ]}
    write_json(a.out, out)
    print(json.dumps({k: {mk: {x: v[x] for x in ("N", "X", "recall_named", "recall_panel_conditional",
                                                   "reduction_vs_B1", "overlap_density")} for mk, v in r["metrics"].items()}
                      for k, r in results.items()}, indent=1))
    print("uncovered:", out["uncovered_by_reason"], file=sys.stderr)


if __name__ == "__main__":
    main()
