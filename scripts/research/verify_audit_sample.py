"""Independent verification of the 33 sampled records in docs/HUMAN_AUDIT_WORKSHEET.md (research workstream B1).

This script imports nothing from the fineprint package. It has its own XML walk, its own DECRS parser, its own
implementation of the documented confidence rules and its own PDF text scan, so it is a separate code path from
the ingest/graph classifier. It reads the claims from the worksheet markdown and checks each one against original
sources:

  * the DailyMed release parts on disk: the member is located by set ID from the zip directories (not from the
    database), the nested XML is re-hashed, and its set ID / version / document ID are read from the bytes;
  * FDA's SPL-by-document-ID copy, fetched live with a generic User-Agent, hashed and compared;
  * the dated FDA DECRS files on disk, hashed, with the generation date read from the zip member timestamp; the
    2022 archived file is also re-fetched from web.archive.org; today's live DECRS file is fetched only to report
    drift, never to decide a verdict;
  * the cached pre-cutoff documents and DailyMed version histories for the historical cases, with a live re-fetch
    of each history and a live DailyMed NDC lookup for the uncovered case;
  * the Pfizer appendix PDF, scanned with a whitespace-insensitive search of its text layer.

Verdicts are VERIFIED, FAILED or CANNOT_TELL. A CANNOT_TELL verdict is always tagged as either
"source_inaccessible" or "ambiguous"; it is never used for a mismatch, which is FAILED.

AI-assisted: the AI assistant wrote and ran this. It is not a human audit, and it does not sign
docs/human_audit_verdicts.csv.

  python -I scripts/research/verify_audit_sample.py [--offline] [--out docs/research/audit_results.json]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("FINEPRINT_DATA", Path.home() / "fineprint-data")).resolve()
DL = DATA / "research" / "b1_downloads"          # new directory for live downloads (untrusted data, outside the repo)
NS = "{urn:hl7-org:v3}"
DUNS_ROOT = "1.3.6.1.4.1.519.1"
FEI_ROOT = "2.16.840.1.113883.4.82"
PRODUCT_SECTION = "48780-1"
MANUFACTURE = "C43360"
ROCKY_MOUNT = "093132819"
CUTOFF = "2023-07-18"
UA = "fineprint/0.1 (research prototype; stdlib urllib)"   # generic: no personal identifiers
PAUSE = 0.5
DM_HISTORY = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{setid}/history.json?pagesize=100&page=1"
DM_NDC = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?ndc={ndc}"
FDA_DECRS_LIVE = "https://www.accessdata.fda.gov/cder/drls_reg.zip"
OP_CODES = {"MANUFACTURE": "C43360", "ANALYSIS": "C25391", "PACK": "C84731", "LABEL": "C84732"}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ----------------------------------------------------------------------------------------------- worksheet claims
def parse_worksheet(md: str) -> dict:
    cases = {"current": [], "historical": [], "identity": []}
    blocks = re.split(r"\n(?=### )", md)
    for b in blocks:
        m = re.match(r"### (C\d\d|H\d\d|I\d\d) · (.+)", b)
        if not m:
            continue
        cid, stratum = m.group(1), m.group(2).strip()
        if cid.startswith("C"):
            s = re.search(r"label set `([0-9a-f-]+)` version (\d+) \(published (\S+)\) asserts \*\*([A-Z ]+)\*\* "
                          r"\(`(C\d+)`\) by DUNS `(\d+)` for (?:`([0-9-]+)` (.+?) \(([^)]*)\)|no product \(operation not "
                          r"tied to one\))\. Status \*\*(\w+)\*\*(?:; reasons: (.+?))?\.", b)
            ident = re.search(r"\*\*Identity in fineprint:\*\* (\w+)(?:, FEI (\d+), (.+?))?\.\n", b)
            xml = re.search(r"\(https://www\.accessdata\.fda\.gov/spl/data/([0-9a-f-]+)/\1\.xml\) \(expected SHA-256 "
                            r"`([0-9a-f]{64})`\)\. At `([^`]+)` .*?inside the establishment whose `id` has extension "
                            r"`(\d+)`(?:, naming product code `([0-9-]+)`|, with no product code)", b, flags=re.S)
            cases["current"].append({
                "id": cid, "stratum": stratum, "set_id": s.group(1), "version": int(s.group(2)),
                "published": None if s.group(3) == "None" else s.group(3), "operation": s.group(4).strip(),
                "operation_code": s.group(5), "duns": s.group(6), "product_ndc_5_4": s.group(7),
                "product_name": s.group(8), "status": s.group(10),
                "reasons": [r.strip() for r in s.group(11).split(",")] if s.group(11) else [],
                "identity_status": ident.group(1), "fei": ident.group(2),
                "identity_text": ident.group(3), "document_id": xml.group(1), "xml_sha256": xml.group(2),
                "loc": xml.group(3), "loc_duns": xml.group(4), "operation_product_code": xml.group(5)})
        elif cid.startswith("H"):
            s = re.search(r"package `([0-9-]+)` is \*\*(\w+)\*\*; flagged: (yes|no); on Pfizer's July 21, 2023 list: "
                          r"(yes|no)\.(?: Note: (.+?)\.)?", b)
            prov = re.search(r"\*\*Pre-cutoff label:\*\* set `([0-9a-f-]+)` version (\d+), published (\S+) \((\w+)\): "
                             r"\[([^\]]+)\]\(\5\) \(XML SHA-256 `([0-9a-f]{64})`\)", b)
            exp_yes = re.search(r"Expect `C43360` \(MANUFACTURE\) by DUNS `093132819` for product `([0-9-]+)` at "
                                r"`(.+?)`\.", b)
            exp_no = re.search(r"Expect \*\*no\*\* MANUFACTURE by DUNS `093132819` for product `([0-9-]+)`\. "
                               r"Manufacturing DUNS fineprint read: (.+?)\.", b)
            c = {"id": cid, "stratum": stratum, "package_ndc_11": s.group(1), "classification": s.group(2),
                 "flagged": s.group(3) == "yes", "on_warning_list": s.group(4) == "yes", "note": s.group(5)}
            if prov:
                c.update(set_id=prov.group(1), version=int(prov.group(2)), published=prov.group(3),
                         document_kind=prov.group(4), document_url=prov.group(5), xml_sha256=prov.group(6))
            if exp_yes:
                c.update(product_ndc_raw=exp_yes.group(1),
                         rocky_mount_manufacture_locs=[x.strip() for x in exp_yes.group(2).split("`, `")])
            elif exp_no:
                mf = exp_no.group(2).strip()
                c.update(product_ndc_raw=exp_no.group(1), rocky_mount_manufacture_locs=[],
                         manufacture_duns=[] if mf == "none" else [x.strip() for x in mf.split(",")])
            cases["historical"].append(c)
        else:
            if cid == "I01":
                s = re.search(r"DUNS `(\d+)` ↔ FEI `(\d+)` ↔ (.+?), from FDA's registration file generated (\S+)\.", b)
                u = re.search(r"download the archived file \[([^\]]+)\]\(\1\) \(expected SHA-256 `([0-9a-f]{64})`\)", b)
                cases["identity"].append({"id": cid, "stratum": stratum, "duns": s.group(1), "fei": s.group(2),
                                          "address": s.group(3), "fda_generated": s.group(4), "url": u.group(1),
                                          "sha256": u.group(2)})
            else:
                s = re.search(r"DUNS `(\d+)` ↔ FEI `(\d+)` ↔ (.+?)\.\n", b)
                cases["identity"].append({"id": cid, "stratum": stratum, "duns": s.group(1), "fei": s.group(2),
                                          "address": s.group(3)})
    return cases


# ------------------------------------------------------------------------------------------------------- network
def fetch(url: str, dest: Path, *, offline: bool, timeout: int = 120) -> dict:
    """GET to a file under DL; returns {status, sha256, bytes, path, error}. Never raises."""
    if dest.exists():
        b = dest.read_bytes()
        return {"url": url, "status": 200, "sha256": sha256(b), "bytes": len(b), "path": dest.relative_to(DATA).as_posix(),
                "cached": True}
    if offline:
        return {"url": url, "status": None, "error": "offline", "accessible": False}
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout)
        b = r.read()
        status = r.status
    except urllib.error.HTTPError as e:
        time.sleep(PAUSE)
        return {"url": url, "status": e.code, "error": f"http_{e.code}", "accessible": False,
                "retrieved_at": utc_now()}
    except Exception as e:  # network errors are recorded, never fatal
        time.sleep(PAUSE)
        return {"url": url, "status": None, "error": f"{type(e).__name__}: {e}", "accessible": False,
                "retrieved_at": utc_now()}
    dest.write_bytes(b)
    time.sleep(PAUSE)
    return {"url": url, "status": status, "sha256": sha256(b), "bytes": len(b), "path": dest.relative_to(DATA).as_posix(),
            "retrieved_at": utc_now(), "accessible": True,
            "last_modified": r.headers.get("Last-Modified"), "etag": r.headers.get("ETag")}


# ------------------------------------------------------------------------------------------------- XML inspection
def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_xml(b: bytes) -> ET.Element:
    if b"<!DOCTYPE" in b[:65536] or b"<!ENTITY" in b[:65536]:
        raise ValueError("refusing XML with DTD/entity declarations")
    return ET.fromstring(b)


def header(root: ET.Element) -> dict:
    g = lambda t, a: (root.find(NS + t).get(a) if root.find(NS + t) is not None else None)  # noqa: E731
    return {"root_tag": local(root.tag), "document_id": g("id", "root"), "set_id": g("setId", "root"),
            "version": g("versionNumber", "value"), "effective_time": g("effectiveTime", "value")}


def performances(root: ET.Element) -> list[dict]:
    """Every <performance> in the document with a sibling-indexed location and its enclosing organization.

    Location convention (matches the worksheet): every step is indexed except representedOrganization /
    assignedOrganization, which are single children in the author tree.
    """
    out = []

    def rec(elem, loc, ancestors):
        counts = {}
        for child in elem:
            t = local(child.tag)
            counts[t] = counts.get(t, 0) + 1
            step = t if t in ("representedOrganization", "assignedOrganization") else f"{t}[{counts[t]}]"
            cloc = f"{loc}/{step}"
            if t == "performance":
                ent = elem  # the assignedEntity holding this performance
                org = None
                for o in ent:
                    if local(o.tag) in ("assignedOrganization", "representedOrganization"):
                        org = o
                        break
                ids = [(i.get("root"), i.get("extension")) for i in (org.findall(NS + "id") if org is not None else [])]
                act = child.find(NS + "actDefinition")
                code = act.find(NS + "code") if act is not None else None
                prods = []
                if act is not None:
                    for p in act.iter(NS + "manufacturedMaterialKind"):
                        c = p.find(NS + "code")
                        if c is not None:
                            prods.append(c.get("code"))
                name = org.find(NS + "name") if org is not None else None
                out.append({"loc": cloc, "entity_loc": loc, "depth": sum(1 for a in ancestors if a == "assignedEntity"),
                            "in_author": "author" in ancestors, "code": code.get("code") if code is not None else None,
                            "display_name": code.get("displayName") if code is not None else None,
                            "product_codes": prods,
                            "duns": [e for r, e in ids if r == DUNS_ROOT and e],
                            "fei": [e for r, e in ids if r == FEI_ROOT and e],
                            "org_name": " ".join("".join(name.itertext()).split()) if name is not None else None})
            rec(child, cloc, ancestors + [t])

    rec(root, "/document", [])
    return out


def establishment_count(perfs: list[dict], root: ET.Element) -> int:
    """Establishments = organizations at assignedEntity depth 3 inside the author tree (with or without operations)."""
    n = 0

    def rec(elem, depth):
        nonlocal n
        for child in elem:
            t = local(child.tag)
            d = depth + 1 if t == "assignedEntity" else depth
            if t == "assignedEntity" and d == 3:
                n += 1
            rec(child, d)

    for a in root.findall(NS + "author"):
        rec(a, 0)
    return n


def products(root: ET.Element) -> list[dict]:
    """Products under any section: code, name, package codes (all levels), kit-part codes, source NDCs.

    The section code is recorded; pre-2009 labels put the product under an unclassified section rather than
    48780-1 (fineprint stores those with a 'product_outside_product_data_section' anomaly)."""
    out = []
    for sec in root.iter(NS + "section"):
        c = sec.find(NS + "code")
        sec_code = c.get("code") if c is not None else None
        for subj in sec.findall(NS + "subject"):
            outer = subj.find(NS + "manufacturedProduct")
            if outer is None:
                continue
            inner = outer.find(NS + "manufacturedProduct")
            if inner is None:
                inner = outer.find(NS + "manufacturedMedicine")
            if inner is None:
                continue
            code = inner.find(NS + "code")
            name = inner.find(NS + "name")
            pk = [k.get("code") for tag in ("containerPackagedProduct", "containerPackagedMedicine")
                  for cp in inner.iter(NS + tag) for k in [cp.find(NS + "code")] if k is not None]
            parts = [k.get("code") for tag in ("partProduct", "partMedicine")
                     for pp in inner.iter(NS + tag) for k in [pp.find(NS + "code")] if k is not None]
            # repackager / relabeler labels cite the source product here (asEquivalentEntity/definingMaterialKind)
            sources = [k.get("code") for eq in inner.findall(NS + "asEquivalentEntity")
                       for dm in eq.findall(NS + "definingMaterialKind") for k in [dm.find(NS + "code")] if k is not None]
            out.append({"code": code.get("code") if code is not None else None,
                        "name": " ".join("".join(name.itertext()).split()) if name is not None else None,
                        "section": sec_code, "packages": pk, "parts": parts, "source_ndcs": sources})
    return out


def to_5_4(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.split("-")
    if len(s) != 2 or not all(x.isdigit() for x in s):
        return None
    if (len(s[0]), len(s[1])) == (4, 4):
        return f"0{s[0]}-{s[1]}"
    if (len(s[0]), len(s[1])) == (5, 3):
        return f"{s[0]}-0{s[1]}"
    if (len(s[0]), len(s[1])) == (5, 4):
        return raw
    return None


def to_11(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.split("-")
    if len(s) != 3 or not all(x.isdigit() for x in s):
        return None
    p = tuple(len(x) for x in s)
    if p == (4, 4, 2):
        return f"0{s[0]}-{s[1]}-{s[2]}"
    if p == (5, 3, 2):
        return f"{s[0]}-0{s[1]}-{s[2]}"
    if p == (5, 4, 1):
        return f"{s[0]}-{s[1]}-0{s[2]}"
    if p == (5, 4, 2):
        return raw
    return None


def et_resolve(root: ET.Element, loc: str) -> ET.Element | None:
    """Cross-check: resolve the worksheet location with ElementTree positional predicates."""
    steps = loc.strip("/").split("/")[1:]
    try:
        return root.find("./" + "/".join(NS + s for s in steps))
    except SyntaxError:
        return None


# ------------------------------------------------------------------------------------------------ release parts
class Release:
    def __init__(self):
        self.parts = sorted((DATA / "raw" / "dailymed" / "human_rx_full").glob("*/dm_spl_release_human_rx_part*.zip"))
        self.index: dict[str, list[tuple[Path, str]]] = {}
        self.part_sha: dict[str, str | None] = {}
        for p in self.parts:
            rec = Path(str(p) + ".json")
            self.part_sha[p.name] = json.loads(rec.read_text("utf-8")).get("sha256") if rec.exists() else None
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():
                    m = re.match(r"^[^/]+/\d{8}_([0-9a-fA-F-]{36})\.zip$", n)
                    if m:
                        self.index.setdefault(m.group(1).lower(), []).append((p, n))
        meta = next((DATA / "raw" / "dailymed").glob("zip_meta_*/dm_spl_zip_files_meta_data.zip"))
        self.meta_path = meta
        self.meta_sha = sha256(meta.read_bytes())
        self.meta: dict[str, dict] = {}      # zip basename -> row
        self.meta_by_set: dict[str, list] = {}
        with zipfile.ZipFile(meta) as z:
            txt = [i for i in z.infolist() if i.filename.lower().endswith(".txt")][0]
            lines = z.read(txt).decode("utf-8", "replace").splitlines()
        assert lines[0].strip() == "SETID|ZIP_FILE_NAME|UPLOAD_DATE|SPL_VERSION|TITLE", lines[0]
        for ln in lines[1:]:
            f = ln.rstrip("\r\n").split("|", 4)
            if len(f) != 5:
                continue
            row = {"set_id": f[0].strip().lower(), "zip": f[1].strip(), "upload_date": f[2].strip(),
                   "version": int(f[3]) if f[3].strip().isdigit() else None}
            self.meta[row["zip"]] = row
            self.meta_by_set.setdefault(row["set_id"], []).append(row)

    def members(self, set_id: str) -> list[dict]:
        out = []
        for p, n in self.index.get(set_id.lower(), []):
            with zipfile.ZipFile(p) as z:
                data = z.read(n)
            with zipfile.ZipFile(io.BytesIO(data)) as inner:
                xmls = [i for i in inner.infolist() if i.filename.lower().endswith(".xml")]
                xml = inner.read(xmls[0]) if len(xmls) == 1 else None
            h = header(parse_xml(xml)) if xml else {}
            out.append({"part": p.name, "part_sha256": self.part_sha[p.name], "member": n, "member_sha256": sha256(data),
                        "xml_member": xmls[0].filename if len(xmls) == 1 else None,
                        "xml_sha256": sha256(xml) if xml else None, "xml": xml, **h})
        return out

    def upload_date(self, member: str, set_id: str, version: int) -> tuple[str | None, str]:
        base = member.rsplit("/", 1)[-1]
        row = self.meta.get(base)
        if row and row["set_id"] == set_id.lower() and row["version"] == version:
            d = dt.datetime.strptime(row["upload_date"], "%m/%d/%Y").date().isoformat()
            return d, "zip_metadata_row_matches_member_set_and_version"
        if row:
            return None, f"zip_metadata_row_for_member_names_version_{row['version']}"
        return None, "member_not_listed_in_zip_metadata"


# ------------------------------------------------------------------------------------------------------- DECRS
def parse_decrs(path: Path) -> dict:
    b = path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        info = [i for i in z.infolist() if i.filename.lower().endswith(".txt")][0]
        raw = z.read(info)
    lines = raw.decode("latin-1").splitlines()
    hdr = [h.strip() for h in lines[0].split("\t")]
    by_duns: dict[str, list] = {}
    by_fei: dict[str, list] = {}
    registrant_duns: set[str] = set()
    for n, ln in enumerate(lines[1:], start=2):
        if not ln.strip():
            continue
        f = dict(zip(hdr, (x.strip() for x in ln.split("\t"))))
        row = {"line": n, "fei": f.get("FEI_NUMBER") or None, "duns": f.get("DUNS_NUMBER") or None,
               "firm": f.get("FIRM_NAME") or None, "address": f.get("ADDRESS") or None,
               "expiration": f.get("EXPIRATION_DATE") or None, "operations": f.get("OPERATIONS") or None,
               "exclusion": f.get("EXCLUSION_FLAG") or None}
        if row["duns"]:
            by_duns.setdefault(row["duns"], []).append(row)
        if row["fei"]:
            by_fei.setdefault(row["fei"], []).append(row)
        if f.get("REGISTRANT_DUNS"):
            registrant_duns.add(f["REGISTRANT_DUNS"].strip())
    return {"path": path.relative_to(DATA).as_posix() if path.is_relative_to(DATA) else path.as_posix(), "sha256": sha256(b),
            "member": info.filename, "generated": "%04d-%02d-%02dT%02d:%02d:%02d" % info.date_time,
            "generated_date": "%04d-%02d-%02d" % info.date_time[:3], "rows": len(lines) - 1,
            "by_duns": by_duns, "by_fei": by_fei, "registrant_duns": registrant_duns}


def load_decrs() -> dict:
    cur_dir = sorted((DATA / "raw" / "fda" / "decrs").glob("20*"))[-1]
    files = {"current": parse_decrs(cur_dir / "drls_reg.zip"), "excluded": parse_decrs(cur_dir / "drls_excluded.zip"),
             "archived": sorted((parse_decrs(p) for p in (DATA / "raw" / "fda" / "decrs" / "archived").glob("*.zip")),
                                key=lambda d: d["generated"], reverse=True)}
    return files


def mdy(s: str | None):
    try:
        return dt.datetime.strptime(s, "%m/%d/%Y").date() if s else None
    except ValueError:
        return None


def resolve_identity(duns: str, decrs: dict) -> dict:
    """Documented rule: CURRENT_REGISTERED > CURRENT_REGISTERED_NO_FEI > CURRENT_EXCLUDED > STALE_REGISTERED > NOT_FOUND."""
    cur = decrs["current"]
    snapshots = [("fda_decrs_registration", cur), ("fda_decrs_excluded", decrs["excluded"])] + \
                [("fda_decrs_registration_archived", a) for a in decrs["archived"]]
    feis = {r["fei"] for _, s in snapshots for r in s["by_duns"].get(duns, []) if r["fei"]}
    history = [{"as_of": s["generated_date"], "kind": k, "fei": r["fei"], "address": r["address"]}
               for k, s in sorted(snapshots, key=lambda x: x[1]["generated"]) for r in s["by_duns"].get(duns, [])]
    out = {"duns": duns, "fei_changed": len(feis) > 1, "fei_history": history, "row": None, "file": None,
           "registrant_only_in_current": duns in cur["registrant_duns"] and duns not in cur["by_duns"]}
    rows = cur["by_duns"].get(duns)
    if rows:
        if len({r["fei"] for r in rows if r["fei"]}) > 1:
            out.update(status="AMBIGUOUS_MULTIPLE_FEI", row=rows[0], file=cur)
        else:
            out.update(status="CURRENT_REGISTERED" if rows[0]["fei"] else "CURRENT_REGISTERED_NO_FEI", row=rows[0],
                       file=cur)
        return out
    rows = decrs["excluded"]["by_duns"].get(duns)
    if rows:
        out.update(status="CURRENT_EXCLUDED", row=rows[0], file=decrs["excluded"])
        return out
    for a in decrs["archived"]:
        rows = a["by_duns"].get(duns)
        if rows:
            out.update(status="STALE_REGISTERED", row=rows[0], file=a)
            return out
    out.update(status="NOT_FOUND")
    return out


def confidence(*, duns, status, expired, fei_changed, scoped, selection_ambiguous) -> tuple[str, list[str]]:
    if duns is None:
        return "UNKNOWN", ["spl:no_duns"]
    if not scoped:
        return "UNKNOWN", ["scope:no_product_scope"]
    if status == "NOT_FOUND":
        return "UNKNOWN", ["identity:NOT_FOUND"]
    reasons = []
    if status != "CURRENT_REGISTERED":
        reasons.append(f"identity:{status}")
    if expired:
        reasons.append("identity:registration_expired")
    if fei_changed:
        reasons.append("identity:fei_changed_across_snapshots")
    if selection_ambiguous:
        reasons.append("version_selection:ambiguous")
    return ("TENTATIVE", reasons) if reasons else ("DIRECT", [])


def select_version(versions: list[int], metadata_version: int | None) -> tuple[int, str, bool]:
    vs = sorted(set(versions))
    if metadata_version is not None and metadata_version in vs:
        return metadata_version, ("SINGLE_VERSION_METADATA_CONFIRMED" if len(vs) == 1
                                  else "MULTI_VERSION_METADATA_SELECTED"), False
    if len(vs) == 1:
        return vs[0], ("SINGLE_VERSION_NOT_IN_METADATA" if metadata_version is None
                       else "SINGLE_VERSION_METADATA_LISTS_OTHER"), metadata_version is not None
    return vs[-1], ("MULTI_VERSION_HIGHEST_NO_METADATA" if metadata_version is None
                    else "MULTI_VERSION_HIGHEST_METADATA_LISTS_OTHER"), True


# ---------------------------------------------------------------------------------------------- PDF text layer
def pdf_text_no_whitespace(pdf: bytes) -> str:
    """Literal strings from every (Flate or raw) stream, concatenated, whitespace removed.

    Independent of fineprint.pdftext: no page model, no object streams; just enough to test membership of an NDC
    string in the text layer irrespective of how the PDF split it into glyph runs."""
    esc = {b"n": b"\n", b"r": b"", b"t": b" ", b"b": b"", b"f": b"", b"(": b"(", b")": b")", b"\\": b"\\"}
    out = []
    import zlib
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", pdf, flags=re.S):
        raw = m.group(1)
        try:
            data = zlib.decompress(raw)
        except Exception:
            data = raw
        for seg in re.findall(rb"BT(.*?)ET", data, flags=re.S):
            for s in re.finditer(rb"\((?:\\.|[^\\)])*\)", seg, flags=re.S):
                t = s.group(0)[1:-1]
                t = re.sub(rb"\\([0-7]{1,3})", lambda x: bytes([int(x.group(1), 8) & 255]), t)
                t = re.sub(rb"\\([nrtbf()\\])", lambda x: esc[x.group(1)], t)
                out.append(t)
    return re.sub(r"\s+", "", b"".join(out).decode("latin-1"))


# ------------------------------------------------------------------------------------------------- verification
class Checks:
    def __init__(self):
        self.items: list[dict] = []
        self.inaccessible: list[str] = []

    def add(self, name, ok, observed=None, expected=None, note=None, kind="assertion"):
        self.items.append({"check": name, "ok": bool(ok), "observed": observed, "expected": expected, "note": note,
                           "kind": kind})
        return ok

    def source_missing(self, what):
        self.inaccessible.append(what)
        self.items.append({"check": what, "ok": False, "kind": "source_access", "note": "source inaccessible"})

    def verdict(self) -> tuple[str, str | None]:
        failed = [c for c in self.items if c["kind"] == "assertion" and not c["ok"]]
        if failed:
            return "FAILED", "incorrect_assertion"
        if self.inaccessible:
            return "CANNOT_TELL", "source_inaccessible"
        return "VERIFIED", None


def verify_current(c: dict, rel: Release, decrs: dict, *, offline: bool) -> dict:
    ck = Checks()
    res = {"id": c["id"], "stratum": c["stratum"], "claim": {k: v for k, v in c.items() if k not in ("id", "stratum")},
           "sources": {}}
    # 1. original bytes from the release part, located by set ID in the zip directories
    members = rel.members(c["set_id"])
    match = [m for m in members if m["xml_sha256"] == c["xml_sha256"]]
    res["sources"]["release_members_for_set"] = [{k: v for k, v in m.items() if k != "xml"} for m in members]
    if not match:
        ck.source_missing("release_member_with_expected_xml_sha256")
        xml = None
    else:
        m = match[0]
        xml = m["xml"]
        ck.add("release_member_xml_sha256_matches_worksheet", True, m["xml_sha256"], c["xml_sha256"],
               note=f"{m['part']}#{m['member']}")
        ck.add("xml_set_id_matches", (m["set_id"] or "").lower() == c["set_id"], m["set_id"], c["set_id"])
        ck.add("xml_version_matches", str(m["version"]) == str(c["version"]), m["version"], c["version"])
        ck.add("xml_document_id_matches", (m["document_id"] or "").lower() == c["document_id"], m["document_id"],
               c["document_id"])
        pub, how = rel.upload_date(m["member"], c["set_id"], c["version"])
        ck.add("published_date_from_official_zip_metadata", pub == c["published"], pub, c["published"], note=how)
    # 2. FDA SPL by document ID (live): same bytes?
    url = f"https://www.accessdata.fda.gov/spl/data/{c['document_id']}/{c['document_id']}.xml"
    f = fetch(url, DL / "fda_spl" / f"{c['document_id']}.xml", offline=offline)
    res["sources"]["fda_spl_by_document_id"] = f
    if f.get("sha256"):
        ck.add("fda_spl_by_document_id_sha256_matches_worksheet", f["sha256"] == c["xml_sha256"], f["sha256"],
               c["xml_sha256"], kind="corroboration")
        if xml is None:
            xml = (DL / "fda_spl" / f"{c['document_id']}.xml").read_bytes()
            if sha256(xml) != c["xml_sha256"]:
                xml = None
    else:
        ck.add("fda_spl_by_document_id_accessible", False, f.get("error"), "HTTP 200", kind="corroboration")
    if xml is None:
        v, why = ck.verdict()
        res.update(checks=ck.items, verdict=v, verdict_basis=why)
        return res
    # 3. independent inspection of the cited element
    root = parse_xml(xml)
    perfs = performances(root)
    prods = products(root)
    hit = [p for p in perfs if p["loc"] == c["loc"]]
    ck.add("performance_exists_at_cited_location", bool(hit), [p["loc"] for p in perfs][:3] if not hit else c["loc"],
           c["loc"])
    et_el = et_resolve(root, c["loc"])
    ck.add("elementtree_positional_resolution_agrees", et_el is not None and local(et_el.tag) == "performance",
           local(et_el.tag) if et_el is not None else None, "performance", kind="corroboration")
    if hit:
        p = hit[0]
        ck.add("operation_code_at_location", p["code"] == c["operation_code"], p["code"], c["operation_code"])
        ck.add("operation_display_name", (p["display_name"] or "").strip().upper() == c["operation"], p["display_name"],
               c["operation"], kind="corroboration")
        ck.add("establishment_duns_at_location", c["loc_duns"] in p["duns"] and c["duns"] in p["duns"], p["duns"],
               c["duns"])
        ck.add("operation_is_at_establishment_level_depth3_in_author", p["depth"] == 3 and p["in_author"],
               {"depth": p["depth"], "in_author": p["in_author"]}, {"depth": 3, "in_author": True})
        if c["operation_product_code"]:
            ck.add("operation_names_expected_product_code", c["operation_product_code"] in p["product_codes"],
                   p["product_codes"], c["operation_product_code"])
            in_section = [q for q in prods if q["code"] == c["operation_product_code"]]
            ck.add("product_code_is_a_product_in_the_label", bool(in_section),
                   [q["code"] for q in prods], c["operation_product_code"],
                   note=None if not in_section or in_section[0]["section"] == PRODUCT_SECTION
                   else f"product sits under section {in_section[0]['section']}, not {PRODUCT_SECTION}")
            ck.add("product_ndc_5_4_normalization", to_5_4(c["operation_product_code"]) == c["product_ndc_5_4"],
                   to_5_4(c["operation_product_code"]), c["product_ndc_5_4"])
            if in_section:
                ck.add("product_name_matches", (in_section[0]["name"] or "").lower() == (c["product_name"] or "").lower(),
                       in_section[0]["name"], c["product_name"], kind="corroboration")
        else:
            ck.add("operation_has_no_product_code", not p["product_codes"], p["product_codes"], [])
        res["observed_element"] = {k: p[k] for k in ("loc", "code", "display_name", "product_codes", "duns", "org_name",
                                                     "depth")}
    res["observed_document"] = {
        "establishments_depth3": establishment_count(perfs, root),
        "performances_total": len(perfs), "performances_outside_author": sum(1 for p in perfs if not p["in_author"]),
        "performances_not_depth3": sum(1 for p in perfs if p["depth"] != 3),
        "all_operations_for_this_product": sorted({(p["code"], p["display_name"], d) for p in perfs
                                                   for d in (p["duns"] or [None])
                                                   if c["operation_product_code"] and
                                                   c["operation_product_code"] in p["product_codes"]}),
        "manufacture_duns_for_this_product": sorted({d for p in perfs for d in p["duns"] if p["code"] == MANUFACTURE
                                                     and c["operation_product_code"] and
                                                     c["operation_product_code"] in p["product_codes"]}),
        "products_in_section": [q["code"] for q in prods]}
    # 4. identity against the dated DECRS files
    ident = resolve_identity(c["duns"], decrs)
    res["observed_identity"] = {k: ident[k] for k in ("status", "fei_changed", "fei_history", "registrant_only_in_current")}
    if ident["row"]:
        res["observed_identity"].update(fei=ident["row"]["fei"], firm=ident["row"]["firm"], address=ident["row"]["address"],
                                        expiration=ident["row"]["expiration"], line=ident["row"]["line"],
                                        file=ident["file"]["path"], file_sha256=ident["file"]["sha256"],
                                        file_generated=ident["file"]["generated"])
    ck.add("identity_status_per_dated_decrs", ident["status"] == c["identity_status"], ident["status"], c["identity_status"])
    if c["fei"]:
        ck.add("fei_per_dated_decrs", ident["row"] is not None and ident["row"]["fei"] == c["fei"],
               ident["row"]["fei"] if ident["row"] else None, c["fei"])
        if ident["row"]:
            txt = f"{ident['row']['firm']}, {ident['row']['address']}"
            ck.add("firm_and_address_per_dated_decrs", txt == c["identity_text"], txt, c["identity_text"])
    if ident["status"] == "STALE_REGISTERED":
        newer = [a["generated_date"] for a in decrs["archived"] if a["generated"] > ident["file"]["generated"]
                 and c["duns"] in a["by_duns"]]
        ck.add("stale_snapshot_is_newest_listing", not newer and c["duns"] not in decrs["current"]["by_duns"]
               and c["duns"] not in decrs["excluded"]["by_duns"], {"newer_listings": newer},
               {"newer_listings": []})
    if ident["status"] == "NOT_FOUND":
        files = ["current", "excluded"] + [a["generated_date"] for a in decrs["archived"]]
        ck.add("duns_absent_from_all_loaded_registration_files", True, files, files,
               note="also_listed_as_registrant_duns" if ident["registrant_only_in_current"] else None)
    expired = bool(ident["row"] and mdy(ident["row"]["expiration"]) and
                   mdy(ident["row"]["expiration"]) < dt.date.fromisoformat(ident["file"]["generated_date"]))
    # 5. version selection from the release's own contents + official metadata
    versions = [int(m["version"]) for m in members if m.get("version") and str(m["version"]).isdigit()]
    meta_rows = rel.meta_by_set.get(c["set_id"].lower(), [])
    mv = meta_rows[0]["version"] if meta_rows else None
    sel, status, ambiguous = select_version(versions, mv)
    res["observed_selection"] = {"versions_in_release": sorted(set(versions)), "metadata_version": mv,
                                 "selected": sel, "status": status, "ambiguous": ambiguous,
                                 "metadata_rows": meta_rows}
    ck.add("selected_version_is_worksheet_version", sel == c["version"], sel, c["version"])
    # 6. documented confidence rule applied to the independently observed facts
    conf, reasons = confidence(duns=c["duns"], status=ident["status"], expired=expired,
                               fei_changed=ident["fei_changed"], scoped=bool(c["operation_product_code"]),
                               selection_ambiguous=ambiguous)
    ck.add("confidence_per_documented_rules", conf == c["status"] and sorted(reasons) == sorted(c["reasons"]),
           {"confidence": conf, "reasons": reasons}, {"confidence": c["status"], "reasons": c["reasons"]})
    is_control = c["stratum"].startswith("Control")
    ck.add("worksheet_stratum_consistent_with_operation",
           (c["operation"] != "MANUFACTURE") if is_control else (c["operation"] == "MANUFACTURE"),
           c["operation"], c["stratum"], kind="corroboration")
    v, why = ck.verdict()
    res.update(checks=ck.items, verdict=v, verdict_basis=why)
    return res


def classify_hist(ev: dict) -> str:
    if ROCKY_MOUNT in ev["mfg_duns"]:
        return "DIRECT"
    if ev["rm_part_mfg"]:
        return "KIT_PART_ONLY"
    if ev["mfg_duns"]:
        return "OTHER_SITE"
    if ev["rm_ops"]:
        return "RM_SECONDARY_ONLY"
    if ev["mfg_without_duns"]:
        return "UNKNOWN_MANUFACTURE_WITHOUT_DUNS"
    if not ev["has_establishment_block"]:
        return "UNKNOWN_NO_ESTABLISHMENT"
    if ev["unscoped"]:
        return "UNKNOWN_UNSCOPED_OPERATION"
    return "UNKNOWN_NO_MANUFACTURE_OP"


def verify_historical(c: dict, frozen_docs: dict, pdf_text: str, *, offline: bool) -> dict:
    ck = Checks()
    res = {"id": c["id"], "stratum": c["stratum"], "claim": {k: v for k, v in c.items() if k not in ("id", "stratum")},
           "sources": {}}
    # warning-list membership from the PDF text layer (whitespace-insensitive)
    on_list = c["package_ndc_11"] in pdf_text
    ck.add("warning_list_membership_per_pdf_text_layer", on_list == c["on_warning_list"], on_list, c["on_warning_list"])
    if "set_id" not in c:  # H11: uncovered warning-list NDC
        f = fetch(DM_NDC.format(ndc=c["package_ndc_11"]), DL / "dailymed" / f"ndc_{c['package_ndc_11']}.json",
                  offline=offline)
        res["sources"]["dailymed_ndc_lookup"] = f
        if f.get("sha256"):
            d = json.loads((DL / "dailymed" / f"ndc_{c['package_ndc_11']}.json").read_text("utf-8"))
            spls = (d.get("data") or [])
            ck.add("dailymed_has_no_spl_for_this_ndc_today", len(spls) == 0, {"spls": len(spls),
                   "total_elements": (d.get("metadata") or {}).get("total_elements")}, {"spls": 0}, kind="corroboration",
                   note="today's DailyMed, not a 2023 state")
        else:
            ck.add("dailymed_ndc_lookup_accessible", False, f.get("error"), "HTTP 200", kind="corroboration")
        ck.add("not_in_cohort_means_no_graph_flag", c["flagged"] is False and c["classification"] == "NOT_IN_COHORT",
               {"flagged": c["flagged"], "classification": c["classification"]}, {"flagged": False})
        v, why = ck.verdict()
        res.update(checks=ck.items, verdict=v, verdict_basis=why)
        return res
    # cached pre-cutoff document
    zp = DATA / "raw" / "historical" / "frame_reconcile" / "spl" / f"{c['set_id']}_v{c['version']}.zip"
    prov = Path(str(zp) + ".prov.json")
    if not zp.exists() or not prov.exists():
        ck.source_missing("cached_pre_cutoff_zip")
        v, why = ck.verdict()
        res.update(checks=ck.items, verdict=v, verdict_basis=why)
        return res
    zb = zp.read_bytes()
    pv = json.loads(prov.read_text("utf-8"))
    fz = frozen_docs.get(c["set_id"], {})
    res["sources"]["cached_zip"] = {"path": zp.relative_to(DATA).as_posix(), "sha256": sha256(zb), "url": pv.get("url"),
                                    "retrieved_at": pv.get("retrieved_at"), "frozen_sha256": fz.get("sha256")}
    ck.add("cached_zip_sha256_equals_fetch_provenance", sha256(zb) == pv.get("sha256"), sha256(zb), pv.get("sha256"))
    ck.add("cached_zip_sha256_equals_frozen_documents_json", sha256(zb) == fz.get("sha256"), sha256(zb), fz.get("sha256"))
    ck.add("worksheet_url_equals_provenance_url", c["document_url"] == pv.get("url"), pv.get("url"), c["document_url"])
    with zipfile.ZipFile(io.BytesIO(zb)) as inner:
        xmls = [i for i in inner.infolist() if i.filename.lower().endswith(".xml")]
        xml = inner.read(xmls[0]) if len(xmls) == 1 else None
    if xml is None:
        ck.source_missing("single_xml_member_in_cached_zip")
        v, why = ck.verdict()
        res.update(checks=ck.items, verdict=v, verdict_basis=why)
        return res
    ck.add("xml_sha256_matches_worksheet", sha256(xml) == c["xml_sha256"], sha256(xml), c["xml_sha256"])
    root = parse_xml(xml)
    h = header(root)
    ck.add("xml_set_id_matches", (h["set_id"] or "").lower() == c["set_id"], h["set_id"], c["set_id"])
    ck.add("xml_version_matches", str(h["version"]) == str(c["version"]), h["version"], c["version"])
    ck.add("xml_effective_time_on_or_before_cutoff", (h["effective_time"] or "")[:8] <= CUTOFF.replace("-", ""),
           h["effective_time"], f"<= {CUTOFF}")
    # publication date: cached history, then a live re-fetch
    hp = DATA / "raw" / "historical" / "frame_reconcile" / "history" / f"{c['set_id']}.p1.json"
    pub_cached = None
    if hp.exists():
        hist = json.loads(hp.read_text("utf-8"))
        for row in (hist.get("data") or {}).get("history") or []:
            if int(row["spl_version"]) == c["version"]:
                pub_cached = dt.datetime.strptime(row["published_date"], "%b %d, %Y").date().isoformat()
        ck.add("published_date_per_cached_dailymed_history", pub_cached == c["published"], pub_cached, c["published"])
        ck.add("published_on_or_before_cutoff", pub_cached is not None and pub_cached <= CUTOFF, pub_cached, f"<= {CUTOFF}")
    else:
        ck.source_missing("cached_dailymed_history")
    f = fetch(DM_HISTORY.format(setid=c["set_id"]), DL / "dailymed" / f"history_{c['set_id']}.json", offline=offline)
    res["sources"]["dailymed_history_live"] = f
    if f.get("sha256"):
        hist = json.loads((DL / "dailymed" / f"history_{c['set_id']}.json").read_text("utf-8"))
        live = None
        for row in (hist.get("data") or {}).get("history") or []:
            if int(row["spl_version"]) == c["version"]:
                live = dt.datetime.strptime(row["published_date"], "%b %d, %Y").date().isoformat()
        ck.add("published_date_per_live_dailymed_history", live == c["published"], live, c["published"],
               kind="corroboration")
    else:
        ck.add("live_dailymed_history_accessible", False, f.get("error"), "HTTP 200", kind="corroboration")
    # package and product in the document
    prods = products(root)
    prod = [p for p in prods if p["code"] == c["product_ndc_raw"]]
    ck.add("product_code_in_the_label", bool(prod), [p["code"] for p in prods], c["product_ndc_raw"],
           note=None if not prod or prod[0]["section"] == PRODUCT_SECTION
           else f"product sits under section {prod[0]['section']}, not {PRODUCT_SECTION}")
    pk_raw = {k for p in prod for k in p["packages"] if k}
    ck.add("package_ndc_under_that_product", c["package_ndc_11"] in {to_11(k) for k in pk_raw}, sorted(pk_raw),
           c["package_ndc_11"])
    # independent classification (A5 precedence)
    perfs = performances(root)
    part_codes = {k for p in prod for k in p["parts"]}
    ev = {"mfg_duns": set(), "mfg_without_duns": False, "rm_ops": set(), "rm_mfg_locs": [], "rm_part_mfg": False,
          "has_establishment_block": establishment_count(perfs, root) > 0,
          "unscoped": any(not p["product_codes"] for p in perfs if p["in_author"])}
    for p in perfs:
        if not p["in_author"]:
            continue
        if c["product_ndc_raw"] in p["product_codes"]:
            if p["code"] == MANUFACTURE:
                if p["duns"]:
                    ev["mfg_duns"] |= set(p["duns"])
                else:
                    ev["mfg_without_duns"] = True
            if ROCKY_MOUNT in p["duns"]:
                ev["rm_ops"].add(p["code"])
                if p["code"] == MANUFACTURE:
                    ev["rm_mfg_locs"].append(p["loc"])
        elif part_codes & set(p["product_codes"]) and ROCKY_MOUNT in p["duns"] and p["code"] == MANUFACTURE:
            ev["rm_part_mfg"] = True
    cls = classify_hist(ev)
    res["observed"] = {"classification": cls, "manufacture_duns": sorted(ev["mfg_duns"]),
                       "rocky_mount_operations": sorted(ev["rm_ops"]), "rocky_mount_manufacture_locs": ev["rm_mfg_locs"],
                       "has_establishment_block": ev["has_establishment_block"],
                       "document_has_unscoped_operation": ev["unscoped"], "effective_time": h["effective_time"],
                       "all_operations_for_product": sorted({(p["code"], d) for p in perfs for d in (p["duns"] or [None])
                                                             if c["product_ndc_raw"] in p["product_codes"]})}
    ck.add("classification_per_a5_precedence", cls == c["classification"], cls, c["classification"])
    ck.add("rocky_mount_manufacture_locations", ev["rm_mfg_locs"] == c["rocky_mount_manufacture_locs"], ev["rm_mfg_locs"],
           c["rocky_mount_manufacture_locs"])
    if "manufacture_duns" in c:
        ck.add("manufacture_duns_read", sorted(ev["mfg_duns"]) == sorted(c["manufacture_duns"]), sorted(ev["mfg_duns"]),
               sorted(c["manufacture_duns"]))
    ck.add("graph_flag_equals_direct", c["flagged"] == (cls == "DIRECT"), c["flagged"], cls == "DIRECT")
    for loc in c["rocky_mount_manufacture_locs"]:
        el = et_resolve(root, loc)
        ck.add(f"elementtree_resolves_{loc.rsplit('/', 1)[-1]}", el is not None and local(el.tag) == "performance",
               local(el.tag) if el is not None else None, "performance", kind="corroboration")
    v, why = ck.verdict()
    res.update(checks=ck.items, verdict=v, verdict_basis=why)
    return res


def verify_identity(c: dict, decrs: dict, *, offline: bool) -> dict:
    ck = Checks()
    res = {"id": c["id"], "stratum": c["stratum"], "claim": {k: v for k, v in c.items() if k not in ("id", "stratum")},
           "sources": {}}
    if c["id"] == "I01":
        cached = DATA / "raw" / "historical" / "frame_reconcile" / "decrs" / "drls_reg_20221014123457.zip"
        if not cached.exists():
            ck.source_missing("cached_2022_decrs_archive")
        else:
            d = parse_decrs(cached)
            res["sources"]["cached_archive"] = {k: d[k] for k in ("path", "sha256", "member", "generated", "rows")}
            ck.add("cached_file_sha256_matches_worksheet", d["sha256"] == c["sha256"], d["sha256"], c["sha256"])
            ck.add("fda_generation_timestamp", d["generated"] == c["fda_generated"], d["generated"], c["fda_generated"])
            rows = d["by_duns"].get(c["duns"], [])
            ck.add("duns_row_present", bool(rows), len(rows), ">=1")
            if rows:
                ck.add("fei_matches", rows[0]["fei"] == c["fei"], rows[0]["fei"], c["fei"])
                ck.add("address_matches", rows[0]["address"] == c["address"], rows[0]["address"], c["address"])
                ck.add("no_other_duns_shares_fei", {r["duns"] for r in d["by_fei"].get(c["fei"], [])} == {c["duns"]},
                       sorted({r["duns"] for r in d["by_fei"].get(c["fei"], [])}), [c["duns"]])
                res["observed"] = rows[0]
        f = fetch(c["url"], DL / "archive" / "drls_reg_20221014123457.zip", offline=offline, timeout=300)
        res["sources"]["web_archive_live"] = f
        if f.get("sha256"):
            ck.add("web_archive_still_serves_identical_bytes", f["sha256"] == c["sha256"], f["sha256"], c["sha256"],
                   kind="corroboration")
        else:
            ck.add("web_archive_accessible", False, f.get("error"), "HTTP 200", kind="corroboration")
    else:
        cur = decrs["current"]
        rows = cur["by_fei"].get(c["fei"], [])
        res["sources"]["current_decrs"] = {k: cur[k] for k in ("path", "sha256", "member", "generated", "rows")}
        ck.add("fei_row_present_in_dated_current_file", bool(rows), len(rows), ">=1")
        if rows:
            ck.add("duns_matches", any(r["duns"] == c["duns"] for r in rows), [r["duns"] for r in rows], c["duns"])
            ck.add("address_matches", any((r["address"] or "").startswith(c["address"].split(",")[0]) and
                                          "McPherson" in (r["address"] or "") for r in rows),
                   [r["address"] for r in rows], c["address"])
            res["observed"] = rows[0]
    v, why = ck.verdict()
    res.update(checks=ck.items, verdict=v, verdict_basis=why)
    return res


def drift_report(ids: list[str], decrs: dict, *, offline: bool) -> dict:
    """Informational only: does today's live DECRS still say the same for the sampled DUNS? Never affects verdicts."""
    f = fetch(FDA_DECRS_LIVE, DL / "decrs_live" / f"drls_reg_{dt.date.today().isoformat()}.zip", offline=offline,
              timeout=300)
    out = {"fetch": f, "basis": "today's live file versus the dated file the graph used; informational"}
    if not f.get("sha256"):
        return out
    live = parse_decrs(DL / "decrs_live" / f"drls_reg_{dt.date.today().isoformat()}.zip")
    out.update(live_generated=live["generated"], live_sha256=live["sha256"], live_rows=live["rows"], duns={})
    for d in sorted(set(ids)):
        then = resolve_identity(d, decrs)
        now = live["by_duns"].get(d, [])
        out["duns"][d] = {"dated_status": then["status"], "dated_fei": then["row"]["fei"] if then["row"] else None,
                          "live_present": bool(now), "live_fei": now[0]["fei"] if now else None,
                          "live_address": now[0]["address"] if now else None,
                          "changed": (bool(now) != (then["status"] in ("CURRENT_REGISTERED", "CURRENT_REGISTERED_NO_FEI")))
                          or (bool(now) and then["row"] is not None and now[0]["fei"] != then["row"]["fei"])}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="skip every live fetch (cached downloads are still used)")
    ap.add_argument("--out", default=str(REPO / "docs" / "research" / "audit_results.json"))
    ap.add_argument("--table", default=str(REPO / "docs" / "research" / "audit_evidence_table.md"))
    a = ap.parse_args()
    t0 = time.time()
    md = (REPO / "docs" / "HUMAN_AUDIT_WORKSHEET.md").read_text(encoding="utf-8")
    claims = parse_worksheet(md)
    print(f"claims: {len(claims['current'])} current, {len(claims['historical'])} historical, "
          f"{len(claims['identity'])} identity", file=sys.stderr)
    rel = Release()
    print(f"release index: {sum(len(v) for v in rel.index.values())} members in {len(rel.parts)} parts; "
          f"metadata rows {len(rel.meta)}", file=sys.stderr)
    decrs = load_decrs()
    frozen = json.loads((REPO / "evidence" / "historical" / "frozen" / "documents.json").read_text("utf-8"))["documents"]
    pdf_path = DATA / "raw" / "historical" / "outcome" / "fda_media_170647.pdf"
    pdf_bytes = pdf_path.read_bytes()
    pdf_text = pdf_text_no_whitespace(pdf_bytes)
    pdf_tokens = sorted(set(re.findall(r"00409-\d{4}-\d{2}", pdf_text)))
    results = []
    for c in claims["current"]:
        r = verify_current(c, rel, decrs, offline=a.offline)
        results.append(r)
        print(f"{c['id']} {r['verdict']}", file=sys.stderr)
    for c in claims["historical"]:
        r = verify_historical(c, frozen, pdf_text, offline=a.offline)
        results.append(r)
        print(f"{c['id']} {r['verdict']}", file=sys.stderr)
    for c in claims["identity"]:
        r = verify_identity(c, decrs, offline=a.offline)
        results.append(r)
        print(f"{c['id']} {r['verdict']}", file=sys.stderr)
    drift = drift_report([c["duns"] for c in claims["current"]] + [c["duns"] for c in claims["identity"]], decrs,
                         offline=a.offline)
    tally = {}
    for r in results:
        tally.setdefault(r["id"][0], {}).setdefault(r["verdict"], 0)
        tally[r["id"][0]][r["verdict"]] += 1
    out = {
        "generated_at": utc_now(), "worksheet": "docs/HUMAN_AUDIT_WORKSHEET.md",
        "worksheet_sha256": sha256((REPO / "docs" / "HUMAN_AUDIT_WORKSHEET.md").read_bytes()),
        "auditor": "AI assistant (Claude) running scripts/research/verify_audit_sample.py; NOT a human audit",
        "method": __doc__.strip().split("\n\n")[1:3],
        "offline": a.offline, "seconds": round(time.time() - t0, 1),
        "sources": {
            "release_parts": [{"name": p.name, "sha256_from_download_record": rel.part_sha[p.name]} for p in rel.parts],
            "zip_metadata": {"path": rel.meta_path.relative_to(DATA).as_posix(), "sha256": rel.meta_sha},
            "decrs_current": {k: decrs["current"][k] for k in ("path", "sha256", "member", "generated", "rows")},
            "decrs_excluded": {k: decrs["excluded"][k] for k in ("path", "sha256", "member", "generated", "rows")},
            "decrs_archived": [{k: d[k] for k in ("path", "sha256", "member", "generated", "rows")} for d in decrs["archived"]],
            "outcome_pdf": {"path": pdf_path.relative_to(DATA).as_posix(), "sha256": sha256(pdf_bytes),
                            "distinct_00409_package_tokens_in_text_layer": len(pdf_tokens)},
        },
        "tally": tally, "verdicts": {r["id"]: r["verdict"] for r in results},
        "cases": results, "registration_drift_today": drift,
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8", newline="\n")
    write_table(out, Path(a.table))
    print(json.dumps(tally), file=sys.stderr)


def write_table(out: dict, path: Path):
    lines = ["# Audit evidence table (AI-assisted verification, not a human audit)", "",
             f"Generated {out['generated_at']} by `scripts/research/verify_audit_sample.py` from "
             f"`docs/HUMAN_AUDIT_WORKSHEET.md` (SHA-256 `{out['worksheet_sha256'][:16]}…`). "
             "Machine-readable detail for every check: `docs/research/audit_results.json`.", "",
             "| Case | Stratum | Verdict | Basis | Source checked | Source version | Observation |",
             "|---|---|---|---|---|---|---|"]
    for r in out["cases"]:
        cl = r["claim"]
        failed = [c["check"] for c in r["checks"] if not c["ok"] and c["kind"] == "assertion"]
        corro_fail = [c["check"] for c in r["checks"] if not c["ok"] and c["kind"] != "assertion"]
        n_ok = sum(1 for c in r["checks"] if c["ok"])
        if r["id"].startswith("C"):
            src = (f"release part member + FDA SPL by document ID `{cl['document_id'][:8]}…`; "
                   f"DECRS {out['sources']['decrs_current']['generated'][:10]}")
            ver = f"set `{cl['set_id'][:8]}…` v{cl['version']}, XML `{cl['xml_sha256'][:12]}…`"
            el = r.get("observed_element") or {}
            obs = (f"{el.get('code')} ({el.get('display_name')}) by DUNS {el.get('duns')} for {el.get('product_codes')}; "
                   f"identity {r.get('observed_identity', {}).get('status')}"
                   + (f", FEI {r['observed_identity'].get('fei')}" if r.get("observed_identity", {}).get("fei") else ""))
        elif r["id"].startswith("H"):
            src = ("cached pre-cutoff zip (provenance + frozen hash) + DailyMed history (cached and live) + appendix PDF"
                   if "set_id" in cl else "appendix PDF + live DailyMed NDC lookup")
            ver = f"set `{cl['set_id'][:8]}…` v{cl['version']} published {cl['published']}" if "set_id" in cl else "n/a"
            o = r.get("observed") or {}
            obs = (f"class {o.get('classification')}; MANUFACTURE DUNS {o.get('manufacture_duns')}; RM ops "
                   f"{o.get('rocky_mount_operations')}" if o else "no admissible SPL; list membership checked")
        else:
            src = "archived 2022 DECRS (cached + web.archive.org)" if r["id"] == "I01" else "dated current DECRS"
            ver = cl.get("fda_generated") or out["sources"]["decrs_current"]["generated"]
            o = r.get("observed") or {}
            obs = f"FEI {o.get('fei')}, {o.get('address')}" if o else "row not found"
        basis = r["verdict_basis"] or f"{n_ok}/{len(r['checks'])} checks passed"
        if failed:
            basis += "; failed: " + ", ".join(failed)
        if corro_fail:
            basis += "; corroboration unavailable: " + ", ".join(corro_fail)
        lines.append(f"| {r['id']} | {r['stratum']} | **{r['verdict']}** | {basis} | {src} | {ver} | {obs} |")
    t = out["tally"]
    lines += ["", "## Tally", "", "| Part | VERIFIED | FAILED | CANNOT_TELL |", "|---|---|---|---|"]
    for k, name in (("C", "Current graph links"), ("H", "Historical replay packages"), ("I", "Facility identity")):
        lines.append(f"| {name} | {t.get(k, {}).get('VERIFIED', 0)} | {t.get(k, {}).get('FAILED', 0)} | "
                     f"{t.get(k, {}).get('CANNOT_TELL', 0)} |")
    d = out["registration_drift_today"]
    lines += ["", "## Registration drift (informational, not part of any verdict)", ""]
    if d.get("duns"):
        changed = [k for k, v in d["duns"].items() if v["changed"]]
        lines.append(f"Today's live DECRS (generated {d['live_generated']}) versus the dated file: "
                     f"{len(changed)} of {len(d['duns'])} sampled DUNS changed status or FEI"
                     + (f": {', '.join(changed)}." if changed else "."))
    else:
        lines.append(f"Live DECRS not fetched: {d['fetch'].get('error')}.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    sys.exit(main())
