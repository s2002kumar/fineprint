"""DST-00 step 2: DUNS <-> FEI <-> physical-address evidence for the two named sites.

Sources (each kept in its own role; none is substituted for another):
  * FDA DECRS drls_reg.zip, CURRENT (identity_current: never 2023 evidence)
  * FDA DECRS drls_reg.zip, Internet Archive capture before the cutoff (identity_historical)
  * FDA 2018 BLA 125545 chemistry review PDF (identity_historical, text layer only)
Establishment-registration SPL XML evidence is produced by dst00_historical.py.

Only firm/site fields are copied out of DECRS; contact names and emails are dropped.

Usage:
  python -I scripts/dst00_identity.py --config config/dst00_targets.json \
      --data-dir <raw data dir> --out evidence/dst00/identity_evidence.json
"""

import argparse
import base64
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # works under python -I
from fineprint import net, pdftext, safezip  # noqa: E402
from fineprint.manifest import source_record, write_json  # noqa: E402

DECRS_URL = "https://www.accessdata.fda.gov/cder/drls_reg.zip"
DECRS_DOC = "https://www.fda.gov/drugs/drug-approvals-and-databases/drug-establishments-current-registration-site-decrs"
CDX = ("https://web.archive.org/cdx/search/cdx?url=accessdata.fda.gov/cder/drls_reg.zip"
       "&from=2022&to={year}&output=json&fl=timestamp,original,statuscode,digest,length")
WAYBACK_RAW = "https://web.archive.org/web/{ts}id_/{original}"
FDA_2018_PDF = "https://www.accessdata.fda.gov/drugsatfda_docs/nda/2018/125545Orig1s000ChemR.pdf"

SAFE_FIELDS = ("FEI_NUMBER", "DUNS_NUMBER", "FIRM_NAME", "ADDRESS", "EXPIRATION_DATE", "OPERATIONS",
               "REGISTRANT_NAME", "REGISTRANT_DUNS", "EXCLUSION_FLAG")


def read_decrs(zip_path):
    with zipfile.ZipFile(zip_path) as zf:
        scan = safezip.scan_directory(zf)
        txt = [i for i in zf.infolist() if i.filename.lower().endswith(".txt")]
        if len(txt) != 1 or scan["flagged"]:
            raise RuntimeError(f"unexpected DECRS archive layout: {scan}")
        info = txt[0]
        raw = safezip.read_member(zf, info, 64 << 20)
    lines = raw.decode("latin-1").splitlines()
    hdr = [h.strip() for h in lines[0].split("\t")]
    rows = [dict(zip(hdr, (f.strip() for f in ln.split("\t")))) for ln in lines[1:] if ln.strip()]
    member = {"name": info.filename, "bytes": info.file_size, "zip_mtime": "%04d-%02d-%02dT%02d:%02d:%02d" % info.date_time,
              "sha256": hashlib.sha256(raw).hexdigest()}
    return rows, member, hdr


def decrs_stats(rows):
    by_duns, by_fei = {}, {}
    for r in rows:
        if r.get("DUNS_NUMBER"):
            by_duns.setdefault(r["DUNS_NUMBER"], set()).add(r.get("FEI_NUMBER"))
        if r.get("FEI_NUMBER"):
            by_fei.setdefault(r["FEI_NUMBER"], set()).add(r.get("DUNS_NUMBER"))
    return {
        "rows": len(rows),
        "rows_missing_duns": sum(1 for r in rows if not r.get("DUNS_NUMBER")),
        "rows_missing_fei": sum(1 for r in rows if not r.get("FEI_NUMBER")),
        "distinct_duns": len(by_duns),
        "distinct_fei": len(by_fei),
        "duns_with_multiple_fei": sum(1 for v in by_duns.values() if len(v) > 1),
        "fei_with_multiple_duns": sum(1 for v in by_fei.values() if len(v) > 1),
    }


def site_rows(rows, sites):
    out = {}
    for name, ids in sites.items():
        hits = [r for r in rows if r.get("DUNS_NUMBER") == ids["duns"] or r.get("FEI_NUMBER") == ids["fei"]]
        out[name] = {
            "expected": ids,
            "rows": [{k: r.get(k) for k in SAFE_FIELDS} for r in hits],
            "exact_pair_present": any(r.get("DUNS_NUMBER") == ids["duns"] and r.get("FEI_NUMBER") == ids["fei"]
                                      for r in hits),
        }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    cfg = json.loads(a.config.read_text(encoding="utf-8"))
    sites, cutoff = cfg["sites"], cfg["cutoff"]
    sources, result = [], {"run": {"started_at": net.utc_now(), "cutoff": cutoff}}

    # 1. Current DECRS (identity_current) + national index for later coverage checks.
    r = net.fetch(DECRS_URL, a.data_dir / "decrs_current" / "drls_reg.zip")
    rows, member, hdr = read_decrs(r.path)
    sources.append(source_record(r, kind="fda_decrs_drls_reg_zip", role="identity_current", data_dir=a.data_dir,
                                 published_at=None, published_at_basis="not stated; see member zip_mtime",
                                 member=member, documentation_url=DECRS_DOC))
    result["decrs_current"] = {"sha256": r.sha256, "retrieved_at": r.retrieved_at, "member": member,
                               "columns": hdr, "stats": decrs_stats(rows), "sites": site_rows(rows, sites)}
    index = {}
    for row in rows:
        if row.get("DUNS_NUMBER"):
            index.setdefault(row["DUNS_NUMBER"], []).append(
                {k: row.get(k) for k in ("FEI_NUMBER", "FIRM_NAME", "ADDRESS", "EXPIRATION_DATE", "OPERATIONS")})
    idx_path = a.data_dir / "decrs_current" / "duns_index.json"
    idx_path.write_text(json.dumps(index), encoding="utf-8")
    result["decrs_current"]["duns_index_path_in_data_dir"] = "decrs_current/duns_index.json"

    # 2. Pre-cutoff DECRS capture from the Internet Archive (identity_historical).
    year = cutoff[:4]
    cr = net.fetch(CDX.format(year=year))
    caps = json.loads(cr.body.decode("utf-8"))
    caps = [dict(zip(caps[0], c)) for c in caps[1:]] if caps else []
    sources.append(source_record(cr, kind="internet_archive_cdx_listing", role="documentation"))
    ok = [c for c in caps if c["statuscode"] == "200" and c["timestamp"][:8] <= cutoff.replace("-", "")]
    result["decrs_archive_captures_listed"] = caps
    if ok:
        cap = ok[-1]
        ts = cap["timestamp"]
        captured = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}T{ts[8:10]}:{ts[10:12]}:{ts[12:14]}Z"
        wr = net.fetch(WAYBACK_RAW.format(ts=ts, original=cap["original"]),
                       a.data_dir / "decrs_archived" / f"drls_reg_{ts}.zip")
        sha1_b32 = base64.b32encode(hashlib.sha1(Path(wr.path).read_bytes()).digest()).decode()
        hrows, hmember, hhdr = read_decrs(wr.path)
        sources.append(source_record(wr, kind="fda_decrs_drls_reg_zip_archived_copy", role="identity_historical",
                                     data_dir=a.data_dir, captured_at=captured,
                                     published_at=None, published_at_basis="not stated; FDA member zip_mtime recorded",
                                     member=hmember, archive_cdx_digest_sha1_b32=cap["digest"],
                                     archive_digest_matches=sha1_b32 == cap["digest"], original_url=cap["original"]))
        result["decrs_archived"] = {
            "captured_at": captured, "original_url": cap["original"], "sha256": wr.sha256,
            "archive_digest_matches": sha1_b32 == cap["digest"], "member": hmember,
            "pre_cutoff": captured[:10] <= cutoff, "stats": decrs_stats(hrows), "sites": site_rows(hrows, sites),
            "caveat": "Third-party archival copy of an FDA file; registrations listed expire 12/31 of the snapshot year.",
        }
    else:
        result["decrs_archived"] = {"failure": "no HTTP-200 pre-cutoff capture listed"}

    # 3. FDA 2018 PDF text layer (FEI <-> address); DUNS searched but not assumed.
    pr = net.fetch(FDA_2018_PDF, a.data_dir / "fda_pdf" / "125545Orig1s000ChemR.pdf")
    needles = [f"(FEI={sites['mcpherson']['fei']})", sites["mcpherson"]["duns"], sites["rocky_mount"]["duns"],
               sites["rocky_mount"]["fei"], "Establishment Information"]
    found = pdftext.find(Path(pr.path).read_bytes(), needles, before=110, after=0)
    sources.append(source_record(pr, kind="fda_bla_review_pdf", role="identity_historical", data_dir=a.data_dir,
                                 published_at=None,
                                 published_at_basis="not stated in metadata; HTTP Last-Modified recorded"))
    result["fda_2018_pdf"] = {"url": FDA_2018_PDF, "sha256": pr.sha256, "last_modified": pr.headers.get("last-modified"),
                              "pages": found["pages"],
                              "hits": {k: [{"page": h["page"], "excerpt": h["excerpt"] if k.startswith("(FEI") else None}
                                           for h in v] for k, v in found["hits"].items()}}
    result["run"]["finished_at"] = net.utc_now()
    result["sources"] = sources
    write_json(a.out, result)

    print("DECRS current", result["decrs_current"]["stats"])
    for s, v in result["decrs_current"]["sites"].items():
        print("  current", s, v["exact_pair_present"], [(x["FEI_NUMBER"], x["DUNS_NUMBER"], x["ADDRESS"]) for x in v["rows"]])
    da = result["decrs_archived"]
    print("DECRS archived", da.get("captured_at"), "digest ok", da.get("archive_digest_matches"), da.get("stats"))
    for s, v in da.get("sites", {}).items():
        print("  archived", s, v["exact_pair_present"], [(x["FEI_NUMBER"], x["DUNS_NUMBER"], x["ADDRESS"], x["EXPIRATION_DATE"]) for x in v["rows"]])
    print("PDF", result["fda_2018_pdf"]["pages"], {k: [h["page"] for h in v] for k, v in result["fda_2018_pdf"]["hits"].items()})


if __name__ == "__main__":
    main()
