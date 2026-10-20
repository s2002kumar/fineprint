"""Merge every evidence file's source records into one source_manifest.json.

Also records the six bulk parts as observed by HEAD/central directory (SHA-256 only
where a part was actually downloaded) and lists the outcome source as SEALED.

Usage:
  python -I scripts/build_manifest.py --evidence evidence/dst00 --data-dir <dir> --out evidence/dst00/source_manifest.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import dailymed, net  # noqa: E402
from fineprint.manifest import source_record, write_json  # noqa: E402

OUTCOME_URL = "https://www.fda.gov/media/170647/download"
DOC_PAGES = [dailymed.WEB_SERVICES_DOC, dailymed.ARCHIVES_DOC,
             "https://www.fda.gov/drugs/drug-approvals-and-databases/drug-establishments-current-registration-site-decrs"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True, type=Path)
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)

    records = []
    for f in sorted(a.evidence.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for s in d.get("sources", []):
            records.append({**s, "evidence_file": f.as_posix()})

    dl = json.loads((a.evidence / "bulk_part6_download.json").read_text(encoding="utf-8"))
    probe = json.loads((a.evidence / "bulk_probe.json").read_text(encoding="utf-8"))
    parts = []
    for p in probe["parts"]:
        name = p["advertised"]["name"]
        downloaded = dl["advertised"]["name"] == name
        parts.append({
            "kind": "dailymed_bulk_release_part", "source_role": "current", "name": name,
            "url": p["advertised"]["https_url"],
            "advertised": p["advertised"],
            "head": p["head"],
            "observed_members": p.get("central_directory", {}).get("members"),
            "members_match_advertised": p.get("members_match_advertised"),
            "downloaded_in_dst00": downloaded,
            "sha256": dl["download"]["sha256"] if downloaded else None,
            "md5": dl["download"]["md5"] if downloaded else None,
            "md5_matches_advertised": dl["md5_matches_advertised"] if downloaded else None,
            "note": None if downloaded else "Not downloaded in DST-00: only central directory + 25 sampled members read by HTTP Range.",
            "evidence_file": "evidence/dst00/bulk_probe.json",
        })
    for key, kind, role in (("download", "dailymed_bulk_release_part_download", "current"),
                            ("release_page", "dailymed_bulk_release_page", "documentation")):
        rec = source_record(_Stored(dl[key]), kind=kind, role=role, data_dir=a.data_dir)
        records.append({**rec, "evidence_file": "evidence/dst00/bulk_part6_download.json"})

    for url in DOC_PAGES:
        r = net.fetch(url, a.data_dir / "doc_pages" / (url.rstrip("/").split("/")[-1] or "index") )
        records.append(source_record(r, kind="documentation_page", role="documentation", data_dir=a.data_dir))

    seen, unique = set(), []
    for r in records:
        key = (r.get("url"), r.get("sha256"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    unique.sort(key=lambda r: (r["source_role"], r["kind"], r.get("url") or ""))
    manifest = {
        "generated_at": net.utc_now(),
        "card": "DST-00",
        "time_fields": "published_at = publisher-asserted date (null when not stated); captured_at = third-party "
                       "archive capture; retrieved_at = our fetch. They are never substituted for each other.",
        "bulk_release_parts": parts,
        "sources": unique,
        "sealed_sources": [{"kind": "pfizer_low_inventory_appendix", "source_role": "outcome", "url": OUTCOME_URL,
                            "status": "SEALED: not retrieved in DST-00; see docs/historical_panel_plan.md section 6"}],
    }
    write_json(a.out, manifest)
    roles = {}
    for r in unique:
        roles[r["source_role"]] = roles.get(r["source_role"], 0) + 1
    print("sources", len(unique), roles, "parts", len(parts))


class _Stored:
    """A FetchResult stand-in rebuilt from a provenance dict already on disk."""

    def __init__(self, prov):
        self._prov = prov

    def provenance(self):
        return self._prov


if __name__ == "__main__":
    main()
