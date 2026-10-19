"""DST-00 step 4b: inspect ALL advertised human-Rx parts remotely, without downloading them.

For each part (discovered from the live release page): HTTP Range reads of the ZIP
central directory give the exact member count and sizes; then a deterministic
hash-seeded sample of K members per part is fetched by range and parsed.
Sample tallies describe the sample only; they are not national estimates.

Usage:
  python -I scripts/dst00_bulk_probe.py --data-dir <dir> --sample-per-part 25 --seed fineprint-dst00 \
      --duns-index <data>/decrs_current/duns_index.json --out evidence/dst00/bulk_probe.json
"""

import argparse
import hashlib
import json
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import bulk, dailymed, net, safezip  # noqa: E402
from fineprint.manifest import source_record, write_json  # noqa: E402


def sample(names, seed, k):
    return sorted(names, key=lambda n: hashlib.sha256(f"{seed}|{n}".encode()).hexdigest())[:k]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--sample-per-part", type=int, default=25)
    ap.add_argument("--seed", default="fineprint-dst00")
    ap.add_argument("--duns-index", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)

    limits = safezip.DEFAULT_LIMITS
    page = net.fetch(dailymed.BULK_PAGE, a.data_dir / "pages" / "spl-resources-all-drug-labels.html")
    parts = dailymed.parse_release_parts(Path(page.path).read_text(encoding="utf-8"))
    sources = [source_record(page, kind="dailymed_bulk_release_page", role="documentation", data_dir=a.data_dir)]
    overall = bulk.Tally()
    part_results = []
    for p in parts:
        t0 = time.perf_counter()
        reader = net.HttpRangeReader(p["https_url"])
        res = {"advertised": p, "head": {"content_length": reader.size, "etag": reader.etag,
                                         "last_modified": reader.head.headers.get("last-modified"),
                                         "x_amz_version_id": reader.head.headers.get("x-amz-version-id"),
                                         "retrieved_at": reader.head.retrieved_at}}
        try:
            with zipfile.ZipFile(reader) as zf:
                scan = safezip.scan_directory(zf, limits)
                cd_stats = dict(reader.stats())
                infos = {i.filename: i for i in zf.infolist() if not i.is_dir()}
                names = list(infos)
                bad_names = [n for n in names if not bulk.MEMBER_NAME.match(n)]
                chosen = sample(names, a.seed, a.sample_per_part)
                tally = bulk.Tally()
                recs = []
                for n in chosen:
                    info = infos[n]
                    probs = safezip.member_problems(info, limits)
                    if probs:
                        rec = {"member": n, "member_bytes": info.file_size, "status": "failed",
                               "failure": f"unsafe_outer_member:{probs}"}
                    else:
                        data = safezip.read_member(zf, info, limits.max_member_bytes)
                        rec = bulk.process_nested_zip(n, data, limits)
                    tally.add(rec)
                    overall.add(rec)
                    recs.append(rec)
                res.update({
                    "central_directory": {k: scan[k] for k in ("members", "directories", "compressed_bytes",
                                                               "uncompressed_bytes", "duplicate_names", "flagged")},
                    "central_directory_fetch": cd_stats,
                    "members_match_advertised": scan["members"] == p["advertised_number_of_files"],
                    "content_length_vs_advertised_size": {"content_length": reader.size,
                                                          "advertised": p["advertised_file_size"]},
                    "member_names_not_matching_pattern": bad_names[:20],
                    "n_member_names_not_matching_pattern": len(bad_names),
                    "member_size_bytes": {"min": min(i.file_size for i in infos.values()),
                                          "max": max(i.file_size for i in infos.values()),
                                          "median": sorted(i.file_size for i in infos.values())[len(infos) // 2]},
                    "sample": {"seed": a.seed, "k": len(chosen), "members": chosen, "records": recs,
                               "summary": tally.to_dict()},
                })
        except Exception as e:  # report, never hide, a part that cannot be inspected
            res["failure"] = f"{type(e).__name__}: {e}"
        res["range_reader_stats"] = reader.stats()
        res["elapsed_seconds"] = round(time.perf_counter() - t0, 2)
        part_results.append(res)
        print(p["name"], res.get("central_directory", {}).get("members"), "advertised", p["advertised_number_of_files"],
              "sample_ok", res.get("sample", {}).get("summary", {}).get("counts", {}).get("ok"),
              "fail", res.get("failure"), f'{res["elapsed_seconds"]}s', file=sys.stderr)

    duns_index = json.loads(a.duns_index.read_text(encoding="utf-8")) if a.duns_index else None
    totals = {
        "parts_advertised": len(parts),
        "parts_inspected": sum(1 for r in part_results if "central_directory" in r),
        "advertised_files_total": sum(p["advertised_number_of_files"] for p in parts),
        "observed_members_total": sum(r.get("central_directory", {}).get("members", 0) for r in part_results),
        "content_length_bytes_total": sum(r["head"]["content_length"] for r in part_results),
        "sampled_members_total": sum(r.get("sample", {}).get("k", 0) for r in part_results),
    }
    write_json(a.out, {"run": {"finished_at": net.utc_now(), "seed": a.seed, "k": a.sample_per_part},
                       "totals": totals, "parts": part_results,
                       "sample_summary_all_parts": overall.to_dict(duns_index), "sources": sources})
    print(json.dumps(totals, indent=1))


if __name__ == "__main__":
    main()
