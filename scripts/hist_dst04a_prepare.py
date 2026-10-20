"""DST-04A (plan amendment A4): draft, UNFROZEN historical candidate universe and its coverage.

HISTORICAL DOMAIN ONLY. Uses only evidence published/listed on or before 2023-07-18, never
touches the national database, never reads the outcome appendix, never classifies sites.

  python -I scripts/hist_dst04a_prepare.py --config config/dst00_targets.json \
      --out evidence/historical/dst04a_candidates_draft.json \
      --manifest-out evidence/historical/historical_source_manifest.json
"""

import argparse
import json
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import config, dailymed, historical, ndc, net  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402

LABELER = "0409"
REPO = Path(__file__).resolve().parents[1]


def ended_by(marketing, cutoff8):
    return any(m.get("high") and m["high"][:8] <= cutoff8 for m in marketing or [])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--labeler-search", default="Hospira")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--manifest-out", required=True, type=Path)
    a = ap.parse_args(argv)
    cutoff = json.loads(a.config.read_text(encoding="utf-8"))["cutoff"]
    cut8 = cutoff.replace("-", "")
    f = historical.Fetcher(config.data_dir() / "raw" / "historical" / "frame_reconcile")
    started = net.utc_now()

    D = historical.load_ndc_directory(f, cutoff, LABELER)
    snap = D["snapshot_date"]
    print("D", snap, len(D["by_doc"]), "documents", file=sys.stderr)

    a_sets, page = set(), 1
    while True:
        qs = urllib.parse.urlencode({"labeler": a.labeler_search, "pagesize": 100, "page": page})
        p, _ = f.get(f"{dailymed.SPLS_SEARCH}?{qs}", f"search/labeler_{a.labeler_search}_p{page}.json",
                     role="documentation")
        d = json.loads(p.read_text(encoding="utf-8"))
        a_sets |= {h["setid"].lower() for h in d["data"]}
        if int(d["metadata"]["current_page"]) >= int(d["metadata"]["total_pages"]):
            break
        page += 1

    # 1. every D document by document ID (exact pre-event SPL bytes)
    d_docs = {}
    for docid in sorted(D["by_doc"]):
        d_docs[docid] = historical.fetch_by_document_id(f, docid, labeler_segment=LABELER)
    d_set_of = {docid: (s.get("set_id") or "").lower() for docid, s in d_docs.items() if s.get("set_id")}
    print("D docs fetched", sum(1 for s in d_docs.values() if "failure" not in s), "/", len(d_docs), file=sys.stderr)

    # 2. universe and cutoff versions
    universe = sorted(a_sets | set(d_set_of.values()))
    sets = {}
    for sid in universe:
        src = ("A" if sid in a_sets else "") + ("D" if sid in d_set_of.values() else "")
        vers = historical.history(f, sid)
        row = {"set_id": sid, "sources": src, "history_available": vers is not None,
               "versions_listed": len(vers or [])}
        cv = dailymed.latest_admissible(vers, cutoff) if vers else None
        if cv:
            got = historical.fetch_version(f, sid, cv["version"], labeler_segment=LABELER)
            row.update(cutoff_version=cv["version"], cutoff_version_published=cv["published_at"])
            if "failure" not in got and got["served_matches_request"]:
                row.update(cutoff_status="fetched", document=got)
            else:
                # A4.1: the exact same set+version retrieved by document ID may stand in; anything else may not.
                same = [d_docs[x] for x, s in d_set_of.items() if s == sid and "failure" not in d_docs[x]
                        and str(d_docs[x]["version"]) == str(cv["version"])]
                row.update(getfile_failure=got.get("failure") or "served_mismatch",
                           cutoff_status="cutoff_version_by_document_id" if same else "cutoff_version_not_retrievable",
                           document=same[0] if same else None)
        elif vers:
            row.update(cutoff_status="first_published_after_cutoff")
        else:
            dd = [docid for docid, s in d_set_of.items() if s == sid]
            best = max((d_docs[x] for x in dd if "failure" not in d_docs[x]), key=lambda s: int(s["version"]),
                       default=None)
            row.update(cutoff_status="cutoff_version_unverified" if best else "missing", document=best,
                       basis="FDA SPL by document ID, listed in NDC Directory generated " + snap if best else None)
        sets[sid] = row
    # A4.2: recover not-retrievable cutoff versions from DailyMed monthly archives (range reads only)
    missing = {sid: r["cutoff_version"] for sid, r in sets.items()
               if r["cutoff_status"] == "cutoff_version_not_retrievable"}
    monthly = None
    if missing:
        first = min(sets[s]["cutoff_version_published"] for s in missing)
        monthly = historical.recover_from_monthly(f, missing, historical.months_between(first, cutoff),
                                                  labeler_segment=LABELER)
        for sid, doc in monthly["recovered"].items():
            sets[sid].update(cutoff_status="cutoff_version_from_monthly_archive", document=doc)
    print("sets", len(sets), dict(Counter(r["cutoff_status"] for r in sets.values())), file=sys.stderr)

    # 3. packages in scope, with exclusions and mappings
    d_pkgs = {}  # package raw -> (docid, listing info)
    for docid, dd in D["by_doc"].items():
        for pkg, info in dd["packages"].items():
            d_pkgs.setdefault(pkg, []).append((docid, info))
    packages, excluded = [], Counter()
    spl_pkg_index = {}
    for sid, row in sets.items():
        doc = row.get("document")
        if not doc or "failure" in doc:
            continue
        for p in doc["products"]:
            if not p["in_scope"]:
                continue
            for k in p["packages"]:
                raw = k["package_ndc_raw"]
                if not raw:
                    excluded["no_package_code"] += 1
                    continue
                n11 = ndc.to_11_digit(raw)
                if n11 is None:
                    excluded["ambiguous_ndc_format"] += 1
                    continue
                status = "candidate"
                if ended_by(k["marketing"], cut8) or (not k["marketing"] and ended_by(p["marketing"], cut8)):
                    status = "excluded:marketing_ended_pre_cutoff"
                    excluded["marketing_ended_pre_cutoff"] += 1
                packages.append({"package_ndc_11": n11, "package_ndc_raw": raw, "product_ndc_raw": p["product_ndc_raw"],
                                 "maps_to_product_by_segments": ndc.package_belongs_to_product(raw, p["product_ndc_raw"]),
                                 "set_id": sid, "version": doc["version"], "cutoff_status": row["cutoff_status"],
                                 "sources": row["sources"], "status": status, "in_d_listing": raw in d_pkgs,
                                 "product_has_manufacture_assertion": p["has_manufacture_assertion"],
                                 "marketing_unknown": not k["marketing"] and not p["marketing"]})
                spl_pkg_index.setdefault(raw, []).append(sid)
    dup = Counter(p["package_ndc_11"] for p in packages)

    # 4. D packages vs cutoff documents (unresolved mappings)
    d_cov = Counter()
    unresolved = []
    for pkg, refs in sorted(d_pkgs.items()):
        docid = refs[0][0]
        sid = d_set_of.get(docid)
        if sid is None:
            d_cov["document_not_retrievable"] += 1
            unresolved.append({"package": pkg, "reason": "D document not retrievable by ID", "document_id": docid})
        elif sets[sid]["cutoff_status"] not in ("fetched", "cutoff_version_unverified", "cutoff_version_by_document_id",
                                                "cutoff_version_from_monthly_archive"):
            d_cov[f"set_{sets[sid]['cutoff_status']}"] += 1
            unresolved.append({"package": pkg, "reason": f"set {sets[sid]['cutoff_status']}", "set_id": sid})
        elif pkg in spl_pkg_index:
            d_cov["present_in_cutoff_document"] += 1
        else:
            d_cov["absent_from_cutoff_document"] += 1
            unresolved.append({"package": pkg, "reason": "listed in D but absent from the set's cutoff document",
                               "set_id": sid, "cutoff_version": sets[sid].get("cutoff_version")})

    a1 = json.loads((REPO / "evidence/historical/frame_reconcile.json").read_text(encoding="utf-8"))
    prev_absent = {r["d_document_id"] for r in a1["d_rows"] if r["cls"] == "absent_from_a"}  # the A1 gap
    recovered = {docid: d_set_of.get(docid) for docid in sorted(prev_absent)}
    cand = [p for p in packages if p["status"] == "candidate"]
    summary = {
        "status": "DRAFT — NOT FROZEN (plan amendment A4); no outcome data used; no site classification",
        "cutoff": cutoff, "d_snapshot_fda_generated": snap,
        "universe_sets": len(sets), "sets_by_source": dict(Counter(r["sources"] for r in sets.values())),
        "sets_by_cutoff_status": dict(Counter(r["cutoff_status"] for r in sets.values())),
        "sets_without_dailymed_history": sum(1 for r in sets.values() if not r["history_available"]),
        "d_documents": len(D["by_doc"]),
        "d_documents_retrieved_by_id": sum(1 for s in d_docs.values() if "failure" not in s),
        "d_documents_failed": {k: v for k, v in Counter(s.get("failure") for s in d_docs.values()
                                                        if "failure" in s).items()},
        "previously_absent_documents": len(prev_absent),
        "previously_absent_now_resolved_to_set": sum(1 for v in recovered.values() if v),
        "previously_absent_sets_with_dailymed_history": sum(
            1 for v in set(recovered.values()) if v and sets[v]["history_available"]),
        "in_scope_packages_listed": len(packages),
        "candidate_packages": len(cand), "distinct_candidate_package_ndc_11": len({p["package_ndc_11"] for p in cand}),
        "package_ndc_in_multiple_sets": sum(1 for v in dup.values() if v > 1),
        "excluded": dict(excluded),
        "candidates_by_cutoff_status": dict(Counter(p["cutoff_status"] for p in cand)),
        "candidates_marketing_unknown": sum(1 for p in cand if p["marketing_unknown"]),
        "candidates_not_mapping_to_product_by_segments": sum(1 for p in cand if not p["maps_to_product_by_segments"]),
        "candidates_in_d_listing": sum(1 for p in cand if p["in_d_listing"]),
        "candidates_not_in_d_listing": sum(1 for p in cand if not p["in_d_listing"]),
        "candidates_whose_product_has_any_manufacture_assertion": sum(1 for p in cand
                                                                     if p["product_has_manufacture_assertion"]),
        "d_packages": len(d_pkgs), "d_packages_vs_cutoff_documents": dict(d_cov),
    }
    write_json(a.out, {"run": {"started_at": started, "finished_at": net.utc_now(),
                               "plan": "docs/historical_panel_plan.md amendment A4"},
                       "summary": summary, "sets": sets, "packages": packages, "unresolved_d_packages": unresolved,
                       "d_document_resolution": {k: {"set_id": v.get("set_id"), "version": v.get("version"),
                                                     "failure": v.get("failure"),
                                                     "served_matches_request": v.get("served_matches_request")}
                                                 for k, v in d_docs.items()},
                       "previously_absent_resolution": recovered,
                       "monthly_archive_recovery": monthly})
    write_json(a.manifest_out, {"generated_at": net.utc_now(), "domain": "historical (pre-2023-07-18 evidence)",
                                "cutoff": cutoff, "sealed": list(historical.SEALED),
                                "ndc_directory_capture": {k: D[k] for k in ("capture", "zip_sha256",
                                                                            "archive_digest_matches", "member_dates")},
                                "sources": sorted({x["url"]: x for x in f.log}.values(), key=lambda x: x["url"]),
                                "n_sources": len({x["url"] for x in f.log})})
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
