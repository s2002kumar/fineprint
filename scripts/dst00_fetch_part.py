"""DST-00: download ONE bounded human-Rx bulk part, verify the advertised MD5, record SHA-256.

Usage:
  python -I scripts/dst00_fetch_part.py --part dm_spl_release_human_rx_part6.zip \
      --data-dir <dir outside the repo> --out evidence/dst00/bulk_part_download.json

The part list is discovered from the live release page; the page itself is hashed.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import dailymed, net  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True)
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)

    page = net.fetch(dailymed.BULK_PAGE, a.data_dir / "pages" / "spl-resources-all-drug-labels.html")
    parts = dailymed.parse_release_parts(Path(page.path).read_text(encoding="utf-8"))
    match = [p for p in parts if p["name"] == a.part]
    if not match:
        sys.exit(f"part {a.part} not advertised on {dailymed.BULK_PAGE}; saw {[p['name'] for p in parts]}")
    part = match[0]
    res = net.fetch(part["https_url"], a.data_dir / "bulk" / part["name"], timeout=600)
    record = {
        "release_page": page.provenance(),
        "advertised": part,
        "download": res.provenance(),
        "md5_matches_advertised": res.md5 == part["advertised_md5"],
        "throughput_MBps": round(res.bytes / res.elapsed_s / 1e6, 2) if res.elapsed_s else None,
    }
    write_json(a.out, record)
    print(json.dumps({k: record[k] for k in ("md5_matches_advertised", "throughput_MBps")}))
    print(res.sha256, res.bytes)


if __name__ == "__main__":
    main()
