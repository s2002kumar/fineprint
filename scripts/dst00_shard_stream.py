"""DST-00 step 4a: stream EVERY member of one locally downloaded bulk part (one bounded shard).

Bounded memory: one nested SPL ZIP in memory at a time (hard cap), XML parsed
incrementally. Counts are for this shard only and are not national statistics.

Usage:
  python -I scripts/dst00_shard_stream.py --zip <part.zip> --advertised evidence/dst00/bulk_part6_download.json \
      --duns-index <data>/decrs_current/duns_index.json --records <data>/part6_records.jsonl \
      --out evidence/dst00/bulk_shard_part6.json
"""

import argparse
import hashlib
import json
import platform
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import bulk, net, safezip  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True, type=Path)
    ap.add_argument("--advertised", type=Path, help="download record with advertised counts/MD5")
    ap.add_argument("--duns-index", type=Path)
    ap.add_argument("--records", required=True, type=Path, help="per-member JSONL (kept out of git)")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args(argv)

    limits = safezip.DEFAULT_LIMITS
    started = net.utc_now()
    t0 = time.perf_counter()
    tally = bulk.Tally()
    read_s = proc_s = 0.0
    largest = 0
    a.records.parent.mkdir(parents=True, exist_ok=True)
    rec_hash = hashlib.sha256()
    with zipfile.ZipFile(a.zip) as zf, open(a.records, "w", encoding="utf-8", newline="\n") as rout:
        scan = safezip.scan_directory(zf, limits)
        infos = [i for i in zf.infolist() if not i.is_dir()]
        if a.limit:
            infos = infos[: a.limit]
        for n, info in enumerate(infos, 1):
            problems = safezip.member_problems(info, limits)
            if problems:
                rec = {"member": info.filename, "member_bytes": info.file_size, "status": "failed",
                       "failure": f"unsafe_outer_member:{problems}"}
            else:
                r0 = time.perf_counter()
                try:
                    data = safezip.read_member(zf, info, limits.max_member_bytes)
                except (safezip.ZipSafetyError, zipfile.BadZipFile, OSError) as e:
                    data = None
                    rec = {"member": info.filename, "member_bytes": info.file_size, "status": "failed",
                           "failure": f"outer_read_error:{type(e).__name__}:{e}"}
                r1 = time.perf_counter()
                read_s += r1 - r0
                if data is not None:
                    largest = max(largest, len(data))
                    rec = bulk.process_nested_zip(info.filename, data, limits)
                    del data
                proc_s += time.perf_counter() - r1
            tally.add(rec)
            line = json.dumps(rec, sort_keys=True) + "\n"
            rec_hash.update(line.encode("utf-8"))
            rout.write(line)
            if n % 500 == 0:
                print(f"{n}/{len(infos)} {time.perf_counter() - t0:.1f}s peak_rss={bulk.peak_rss_bytes()}", file=sys.stderr)
    wall = time.perf_counter() - t0
    duns_index = json.loads(a.duns_index.read_text(encoding="utf-8")) if a.duns_index else None
    advertised = json.loads(a.advertised.read_text(encoding="utf-8")) if a.advertised else None
    summary = tally.to_dict(duns_index)
    out = {
        "run": {"started_at": started, "finished_at": net.utc_now(), "limit": a.limit,
                "python": sys.version.split()[0], "platform": platform.platform(),
                "processor": platform.processor(), "cpu_count": __import__("os").cpu_count()},
        "source": {"zip_name": a.zip.name, "zip_bytes": a.zip.stat().st_size,
                   "advertised": advertised["advertised"] if advertised else None,
                   "download_sha256": advertised["download"]["sha256"] if advertised else None,
                   "md5_matches_advertised": advertised["md5_matches_advertised"] if advertised else None},
        "outer_directory": {k: scan[k] for k in ("members", "directories", "compressed_bytes",
                                                 "uncompressed_bytes", "duplicate_names", "flagged")},
        "outer_members_match_advertised": (scan["members"] == advertised["advertised"]["advertised_number_of_files"]
                                           if advertised else None),
        "performance": {"wall_seconds": round(wall, 2), "read_seconds": round(read_s, 2),
                        "process_seconds": round(proc_s, 2),
                        "members_per_second": round(len(infos) / wall, 2),
                        "member_MB_per_second": round(summary["counts"]["member_bytes"] / wall / 1e6, 2),
                        "xml_MB_per_second": round(summary["counts"].get("xml_bytes", 0) / wall / 1e6, 2),
                        "largest_member_bytes": largest, "peak_rss_bytes": bulk.peak_rss_bytes()},
        "records": {"path": a.records.name, "sha256": rec_hash.hexdigest(), "lines": len(infos)},
        "summary": summary,
    }
    write_json(a.out, out)
    print(json.dumps({"performance": out["performance"], "counts": summary["counts"],
                      "failures": summary["failures_by_kind"]}, indent=1))


if __name__ == "__main__":
    main()
