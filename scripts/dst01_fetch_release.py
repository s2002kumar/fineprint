"""DST-01: discover and download ALL current human-Rx full-release parts (resumable, verified).

Parts are discovered from the live release page (hashed and saved). Files land in
$FINEPRINT_DATA/raw/dailymed/human_rx_full/<advertised_last_modified>/ with a .json
provenance record per part; a release manifest is written to --out.

  python -I scripts/dst01_fetch_release.py --out evidence/dst01/release_manifest.json [--parallel 3]
  # resume test: --only dm_spl_release_human_rx_part6.zip --interrupt-after-mb 300
"""

import argparse
import concurrent.futures as cf
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import config, dailymed, download, net  # noqa: E402
from fineprint.manifest import write_json  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--only", action="append", help="part name(s) to fetch (default: all advertised)")
    ap.add_argument("--interrupt-after-mb", type=int, help="test hook: abort each fetched part after N MB")
    ap.add_argument("--offline", type=Path, metavar="MANIFEST",
                    help="no network: re-verify the parts/metadata recorded in MANIFEST against their SHA-256")
    a = ap.parse_args(argv)
    if a.offline:
        return verify_offline(a.offline, a.out)

    raw = config.data_dir() / "raw" / "dailymed"
    page = net.fetch(dailymed.BULK_PAGE, raw / "pages" / f"spl-resources-all-drug-labels.{net.utc_now()[:10]}.html")
    parts = dailymed.parse_release_parts(Path(page.path).read_text(encoding="utf-8"))
    if not parts:
        sys.exit("no human-Rx parts advertised; refusing to continue")
    dates = sorted({p["advertised_last_modified"] for p in parts})
    release_dir = raw / "human_rx_full" / dates[-1]
    todo = [p for p in parts if not a.only or p["name"] in a.only]
    stop = a.interrupt_after_mb * (1 << 20) if a.interrupt_after_mb else None

    def one(p):
        try:
            rec = download.download(p["https_url"], release_dir / p["name"], expected_md5=p["advertised_md5"],
                                    stop_after_bytes=stop, log=lambda m: print(m, file=sys.stderr))
            return p["name"], rec, None
        except Exception as e:  # reported per part; other parts continue
            return p["name"], None, f"{type(e).__name__}: {e}"

    results = {}
    with cf.ThreadPoolExecutor(max_workers=max(1, a.parallel)) as ex:
        for name, rec, err in ex.map(one, todo):
            results[name] = {"record": rec, "error": err}
            print(name, (rec or {}).get("status"), (rec or {}).get("md5_matches_advertised"),
                  (rec or {}).get("transfer_seconds"), err, file=sys.stderr)

    # Official per-zip metadata (UPLOAD_DATE = documented publication date), same release.
    mpage = net.fetch(dailymed.MAPPING_PAGE, raw / "pages" / f"spl-resources-all-mapping-files.{net.utc_now()[:10]}.html")
    meta_adv = dailymed.parse_advertised_file(Path(mpage.path).read_text(encoding="utf-8"), dailymed.ZIP_METADATA_FILE)
    meta = {"advertised": meta_adv, "page_sha256": mpage.sha256}
    if meta_adv is None:
        meta["error"] = "metadata file not advertised"
    elif not a.only:
        try:
            meta["download"] = download.download(meta_adv["https_url"], release_dir / meta_adv["name"],
                                                 expected_md5=meta_adv["advertised_md5"])
            meta["local_path"] = (release_dir / meta_adv["name"]).relative_to(config.data_dir()).as_posix()
            if meta_adv["advertised_last_modified"] != dates[-1]:
                meta["warning"] = "metadata Last Modified differs from release parts"
        except Exception as e:
            meta["error"] = f"{type(e).__name__}: {e}"

    manifest = {
        "generated_at": net.utc_now(),
        "release_page": {"url": page.url, "sha256": page.sha256, "retrieved_at": page.retrieved_at,
                         "local_path": Path(page.path).relative_to(config.data_dir()).as_posix()},
        "zip_metadata": meta,
        "advertised_last_modified_values": dates,
        "release_dir": release_dir.relative_to(config.data_dir()).as_posix(),
        "parts": [{**p, "local_path": (release_dir / p["name"]).relative_to(config.data_dir()).as_posix(),
                   **({"download": results[p["name"]]["record"], "error": results[p["name"]]["error"]}
                      if p["name"] in results else {"skipped": True})} for p in parts],
    }
    write_json(a.out, manifest)
    failed = [n for n, r in results.items() if r["error"]] + (["zip_metadata"] if meta.get("error") else [])
    print(json.dumps({"parts": len(parts), "fetched": len(results), "failed": failed}), file=sys.stderr)
    return 1 if failed else 0


def verify_offline(manifest_path: Path, out: Path) -> int:
    """Reproducibility mode: every recorded file must exist and match its recorded SHA-256."""
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    bad = []
    items = [p for p in m["parts"]] + ([m["zip_metadata"]] if m.get("zip_metadata", {}).get("local_path") else [])
    for p in items:
        path = config.data_dir() / p["local_path"]
        want = (p.get("download") or {}).get("sha256")
        sha, md5, n = download.hash_file(path) if path.exists() else (None, None, 0)
        ok = sha is not None and sha == want
        p.setdefault("offline_verification", {})
        p["offline_verification"] = {"verified_at": net.utc_now(), "sha256_matches_record": ok, "bytes": n}
        if not ok:
            bad.append(p.get("name") or p["local_path"])
        print(path.name, "OK" if ok else "MISMATCH/MISSING", file=sys.stderr)
    write_json(out, m)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
