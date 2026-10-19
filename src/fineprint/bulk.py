"""Per-member processing and measured tallies for DailyMed bulk release parts.

A bulk part is a ZIP of nested per-SPL ZIPs (``prescription/<YYYYMMDD>_<setid>.zip``).
Each nested ZIP is processed in memory under hard byte caps; nothing is extracted
by name. Every count reported here is an observation over the members actually
processed, never an extrapolation.
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter

from . import ndc, safezip, spl

MEMBER_NAME = re.compile(r"^(?P<dir>[^/]+)/(?P<date>\d{8})_(?P<setid>[0-9a-fA-F-]{36})\.zip$")


def peak_rss_bytes() -> int | None:
    """Peak resident set size of this process (Windows working set or POSIX maxrss)."""
    try:
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            class PMC(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
            pmc = PMC()
            pmc.cb = ctypes.sizeof(PMC)
            k32, psapi = ctypes.windll.kernel32, ctypes.windll.psapi
            k32.GetCurrentProcess.restype = wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
            if not psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
                return None
            return int(pmc.PeakWorkingSetSize)
        import resource
        r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return r if sys.platform == "darwin" else r * 1024
    except Exception:
        return None


def process_nested_zip(member_name: str, data: bytes, limits: safezip.Limits = safezip.DEFAULT_LIMITS) -> dict:
    """Process one nested SPL ZIP; return a compact, JSON-serialisable record."""
    t0 = time.perf_counter()
    rec = {"member": member_name, "member_bytes": len(data), "member_sha256": hashlib.sha256(data).hexdigest(),
           "status": "ok", "failure": None}
    m = MEMBER_NAME.match(member_name)
    rec["name_date"] = m["date"] if m else None
    rec["name_set_id"] = m["setid"].lower() if m else None
    if not m:
        rec["name_problem"] = "unexpected_member_name_pattern"
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as e:
        rec.update(status="failed", failure=f"bad_nested_zip:{e}")
        return rec
    with zf:
        infos = zf.infolist()
        if len(infos) > limits.max_nested_members:
            rec.update(status="failed", failure="too_many_nested_members")
            return rec
        flagged = {i.filename: safezip.member_problems(i, limits) for i in infos}
        flagged = {k: v for k, v in flagged.items() if v}
        rec["nested_members"] = len(infos)
        rec["nested_flagged"] = flagged
        xmls = [i for i in infos if i.filename.lower().endswith(".xml")]
        rec["xml_members"] = len(xmls)
        if len(xmls) != 1:
            rec.update(status="failed", failure=f"xml_member_count_{len(xmls)}")
            return rec
        info = xmls[0]
        if info.filename in flagged:
            rec.update(status="failed", failure=f"unsafe_xml_member:{flagged[info.filename]}")
            return rec
        try:
            with safezip.open_member(zf, info, limits.max_xml_bytes) as fh:
                doc = spl.parse_spl(fh, max_bytes=limits.max_xml_bytes)
        except spl.SplRejected as e:
            rec.update(status="failed", failure=f"rejected:{e}")
            return rec
        except ET.ParseError as e:
            rec.update(status="failed", failure=f"xml_parse_error:{e}")
            return rec
        except (safezip.ZipSafetyError, zipfile.BadZipFile, EOFError, OSError) as e:
            rec.update(status="failed", failure=f"member_read_error:{type(e).__name__}:{e}")
            return rec
    rec.update(summarize_document(doc))
    if rec["name_set_id"] and doc["set_id"] and rec["name_set_id"] != doc["set_id"].lower():
        rec.setdefault("anomalies", []).append({"kind": "member_name_set_id_mismatch"})
    rec["parse_seconds"] = round(time.perf_counter() - t0, 4)
    return rec


def summarize_document(doc: dict) -> dict:
    ests = spl.establishments(doc)
    edges = spl.operation_edges(doc)
    product_codes = [p["product_ndc_raw"] for p in doc["products"]]
    all_packages = [k for p in doc["products"] for k in p["packages"]] + \
                   [k for p in doc["products"] for part in p["parts"] for k in part["packages"]]
    mfg = {e["product_code"] for e in edges if e["operation_code"] == spl.MANUFACTURE_CODE and e["duns"]}
    op_codes = {e["product_code"] for e in edges if e["product_code"]}
    part_codes = {part["code"] for p in doc["products"] for part in p["parts"] if part["code"]}
    return {
        "xml_sha256": doc["xml_sha256"], "xml_bytes": doc["xml_bytes"],
        "set_id": doc["set_id"], "version": doc["version"], "effective_time": doc["effective_time"],
        "document_type_code": doc["document_type_code"], "document_type": doc["document_type"],
        "labeler_duns": sorted({d for o in spl.labelers(doc) for d in o["duns"]}),
        "n_products": len(product_codes),
        "n_products_without_code": sum(1 for c in product_codes if not c),
        "product_ndc_patterns": dict(Counter(ndc.pattern(c) for c in product_codes if c)),
        "n_packages": len(all_packages),
        "n_packages_without_code": sum(1 for k in all_packages if not k["package_ndc_raw"]),
        "n_packages_not_matching_product_segments": sum(
            1 for p in doc["products"] for k in p["packages"]
            if k["package_ndc_raw"] and p["product_ndc_raw"]
            and not ndc.package_belongs_to_product(k["package_ndc_raw"], p["product_ndc_raw"])),
        "n_kit_parts": sum(len(p["parts"]) for p in doc["products"]),
        "n_establishments": len(ests),
        "n_establishments_without_duns": sum(1 for o in ests if not o["duns"]),
        "establishment_duns": sorted({d for o in ests for d in o["duns"]}),
        "establishment_fei_present": sum(1 for o in ests if o["fei"]),
        "establishment_address_present": sum(1 for o in ests if o["address"]),
        "operations": dict(Counter(f'{e["operation_code"]}|{e["operation"]}' for e in edges)),
        "n_operation_edges": len(edges),
        "n_operation_edges_without_product_code": sum(1 for e in edges if not e["product_code"]),
        "products_with_manufacture_duns": sorted(c for c in product_codes if c in mfg),
        "products_without_manufacture_duns": sorted(c for c in product_codes if c and c not in mfg),
        "operation_codes_not_in_products": sorted(op_codes - set(product_codes) - part_codes),
        "operation_codes_matching_kit_parts": sorted((op_codes & part_codes) - set(product_codes)),
        "manufacture_duns": sorted({e["duns"] for e in edges if e["operation_code"] == spl.MANUFACTURE_CODE and e["duns"]}),
        "anomalies": doc["anomalies"],
    }


class Tally:
    """Aggregate measured counts over processed member records."""

    def __init__(self):
        self.c = Counter()
        self.failures = Counter()
        self.doc_types = Counter()
        self.ops = Counter()
        self.op_names_by_code: dict[str, Counter] = {}
        self.anomalies = Counter()
        self.est_duns: set[str] = set()
        self.mfg_duns: set[str] = set()
        self.labeler_duns: set[str] = set()
        self.set_ids = Counter()
        self.product_patterns = Counter()
        self.name_years = Counter()

    def add(self, r: dict) -> None:
        self.c["members"] += 1
        self.c["member_bytes"] += r["member_bytes"]
        if r["status"] != "ok":
            self.c["failed"] += 1
            self.failures[r["failure"].split(":")[0]] += 1
            return
        self.c["ok"] += 1
        self.c["xml_bytes"] += r["xml_bytes"]
        self.set_ids[r["set_id"]] += 1
        self.doc_types[f'{r["document_type_code"]}|{r["document_type"]}'] += 1
        for k in ("n_products", "n_products_without_code", "n_packages", "n_packages_without_code",
                  "n_packages_not_matching_product_segments", "n_kit_parts", "n_establishments",
                  "n_establishments_without_duns", "establishment_fei_present", "establishment_address_present",
                  "n_operation_edges", "n_operation_edges_without_product_code"):
            self.c[k] += r[k]
        self.c["products_with_manufacture_duns"] += len(r["products_with_manufacture_duns"])
        self.c["products_without_manufacture_duns"] += len(r["products_without_manufacture_duns"])
        self.c["operation_codes_not_in_products"] += len(r["operation_codes_not_in_products"])
        self.c["operation_codes_matching_kit_parts"] += len(r["operation_codes_matching_kit_parts"])
        self.c["docs_with_unscoped_operation_edges"] += r["n_operation_edges_without_product_code"] > 0
        self.name_years[(r.get("name_date") or "none")[:4]] += 1
        self.c["docs_with_zero_establishments"] += r["n_establishments"] == 0
        self.c["docs_with_any_manufacture_duns"] += bool(r["manufacture_duns"])
        for k, v in r["operations"].items():
            self.ops[k] += v
            code, _, name = k.partition("|")
            self.op_names_by_code.setdefault(code, Counter())[name] += v
        for a in r["anomalies"]:
            self.anomalies[a["kind"]] += 1
        self.product_patterns.update(r["product_ndc_patterns"])
        self.est_duns.update(r["establishment_duns"])
        self.mfg_duns.update(r["manufacture_duns"])
        self.labeler_duns.update(r["labeler_duns"])

    def to_dict(self, duns_index: dict | None = None) -> dict:
        d = {
            "counts": dict(self.c),
            "failures_by_kind": dict(self.failures),
            "document_types": dict(self.doc_types.most_common()),
            "operation_edges_by_code_and_name": dict(self.ops.most_common()),
            "operation_codes_with_multiple_names": {k: dict(v) for k, v in self.op_names_by_code.items() if len(v) > 1},
            "anomalies": dict(self.anomalies),
            "product_ndc_patterns": dict(self.product_patterns),
            "member_name_date_years": dict(sorted(self.name_years.items())),
            "distinct_set_ids": len(self.set_ids),
            "set_ids_seen_more_than_once": sum(1 for v in self.set_ids.values() if v > 1),
            "distinct_establishment_duns": len(self.est_duns),
            "distinct_manufacture_duns": len(self.mfg_duns),
            "distinct_labeler_duns": len(self.labeler_duns),
            "labeler_duns_also_establishment_duns": len(self.labeler_duns & self.est_duns),
        }
        if duns_index is not None:
            d["current_decrs_resolution"] = {
                "basis": "CURRENT FDA DECRS drls_reg (identity_current); not valid for historical claims",
                "establishment_duns_found": sum(1 for x in self.est_duns if x in duns_index),
                "establishment_duns_total": len(self.est_duns),
                "manufacture_duns_found": sum(1 for x in self.mfg_duns if x in duns_index),
                "manufacture_duns_total": len(self.mfg_duns),
                "manufacture_duns_found_with_fei": sum(1 for x in self.mfg_duns
                                                       if any(r.get("FEI_NUMBER") for r in duns_index.get(x, []))),
            }
        return d
