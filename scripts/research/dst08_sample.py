"""DST-08 frozen stratified sample of source-NDC references, drawn BEFORE any reference is inspected.

Input: $FINEPRINT_DATA/research/dst08/references.csv from dst08_source_inventory.py (its SHA-256 is recorded in
docs/research/dst08/source_inventory.json and checked here). Every reference is assigned to exactly one stratum by
the first rule that matches, in this order:

  R1 REPACKAGER_CLAIMS_MANUFACTURE  the citing product carries a same-establishment MANUFACTURE beside REPACK/RELABEL
  R2 KIT_OR_PART                     the reference sits on a kit part, or the citing product's dosage form is a kit
  R3 PACKAGE_CODE                    the source code is a package code (three segments), not a product code
  R4 OTHER_INVALID                   any other departure from the Implementation Guide form (equivalence code, code
                                     system, malformed code, self reference, several sources on one product)
  R5 CHAIN_OR_CONFLICT               a multi-hop chain, a cycle, a chain ending unresolved, or a resolved source whose
                                     dosage form or active ingredients differ from the citing product's
  R6 MULTIPLE_CANDIDATES             the code matches several canonical products in other sets
  R7 NO_MATCHING_SOURCE              no canonical top-level product in another set has the code
  R8 MULTIPLE_VERSIONS               resolved single hop, but the citing or the source set has several versions in the
                                     release, or the code also appears in a non-canonical version
  R9 RESOLVED_DIRECT                 resolved single hop to a DIRECT source product, consistent, single versions
  R10 RESOLVED_NOT_DIRECT            resolved single hop to a source product that is not DIRECT

Within each stratum the sample is random.Random(SEED).sample over references ordered by ref_id. The manifest records
the seed, the input hash, the graph build and table fingerprints, the rules, every stratum's size, and each sampled
reference's full row (release part, member and XML SHA-256, element location), so the checks can be reproduced.

  python -I scripts/research/dst08_sample.py --db fineprint
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "research"))
import verify_audit_sample as raw  # noqa: E402
from fineprint import db  # noqa: E402

SEED = "fineprint-dst08-source-ndc-2026-10-25"
# The coverage claim (R9) gets the largest share; R1 is small enough to take whole; R5 and R8 are the strata most
# likely to hide a wrong join. Sizes were set from the stratum counts alone, before any reference was inspected.
SIZES = {"R1 REPACKAGER_CLAIMS_MANUFACTURE": 10, "R5 CHAIN_OR_CONFLICT": 10, "R8 MULTIPLE_VERSIONS": 10,
         "R9 RESOLVED_DIRECT": 30}
DEFAULT_SIZE = 6
INVENTORY = REPO / "docs" / "research" / "dst08" / "source_inventory.json"
REFERENCES = raw.DATA / "research" / "dst08" / "references.csv"
MANIFEST = REPO / "docs" / "research" / "dst08" / "sample_manifest.json"
FREEZE = REPO / "docs" / "research" / "dst08" / "sample_FREEZE.json"
INVALID = {"NOT_EQUIV_CLASS", "NOT_SAME_EQUIVALENCE", "NOT_NDC_CODE_SYSTEM", "MALFORMED_OR_MISSING_CODE",
           "SELF_REFERENCE", "MULTIPLE_SOURCES_FOR_PRODUCT"}


def stratum(r: dict) -> str:
    if r["repack_mfg"] == "True":
        return "R1 REPACKAGER_CLAIMS_MANUFACTURE"
    if r["product_kind"] == "kit_part" or "KIT" in (r["form"] or "").upper():
        return "R2 KIT_OR_PART"
    if r["validity"] == "PACKAGE_CODE_NOT_PRODUCT_CODE":
        return "R3 PACKAGE_CODE"
    if r["validity"] in INVALID:
        return "R4 OTHER_INVALID"
    resolved = r["resolution"] == "RESOLVED"
    if r["chain"] in ("MULTI_HOP", "CYCLE", "TOO_DEEP") or (r["chain"] == "ENDS_UNRESOLVED" and int(r["chain_depth"]) > 1) \
            or (resolved and (r["form_match"] != "True" or r["active_match"] != "True")):
        return "R5 CHAIN_OR_CONFLICT"
    if r["resolution"] == "MULTIPLE_CANDIDATES":
        return "R6 MULTIPLE_CANDIDATES"
    if not resolved:
        return "R7 NO_MATCHING_SOURCE"
    if int(r["repack_set_versions"]) > 1 or any(int(x) > 1 for x in r["source_set_versions"].split(";") if x) \
            or int(r["noncanonical_matches"]) > 0:
        return "R8 MULTIPLE_VERSIONS"
    if r["candidate_statuses"] == "DIRECT":
        return "R9 RESOLVED_DIRECT"
    return "R10 RESOLVED_NOT_DIRECT"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint")
    a = ap.parse_args()
    if FREEZE.exists():
        sys.exit(f"{FREEZE} exists: the sample is frozen and is never redrawn")
    data = REFERENCES.read_bytes()
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    if hashlib.sha256(data).hexdigest() != inventory["references_csv_sha256"]:
        sys.exit("references.csv does not match the hash recorded in source_inventory.json")
    rows = list(csv.DictReader(data.decode("utf-8").splitlines()))
    strata = defaultdict(list)
    for r in sorted(rows, key=lambda r: r["ref_id"]):
        strata[stratum(r)].append(r)
    rng = random.Random(SEED)
    sample = []
    for name in sorted(strata, key=lambda s: int(s.split()[0][1:])):
        members = strata[name]
        k = min(SIZES.get(name, DEFAULT_SIZE), len(members))
        for i, r in enumerate(rng.sample(members, k), 1):
            sample.append({"sample_id": f"{name.split()[0]}-{i:02d}", "stratum": name, **r})
    with db.connect(a.db) as c:
        fingerprint = db.fingerprint(c)
        build = c.execute("SELECT build_id FROM national.graph_build WHERE status = 'completed' ORDER BY build_id DESC LIMIT 1").fetchone()[0]
    manifest = {
        "frozen_at": raw.utc_now(), "seed": SEED, "graph_build": build, "table_fingerprints": fingerprint,
        "references_csv_sha256": inventory["references_csv_sha256"], "inventory_generated_at": inventory["generated_at"],
        "rules": stratum.__doc__ or __doc__.split("Within each stratum")[0].strip(),
        "stratum_sizes": {k: len(v) for k, v in sorted(strata.items(), key=lambda kv: int(kv[0].split()[0][1:]))},
        "sample_sizes": {k: min(SIZES.get(k, DEFAULT_SIZE), len(v)) for k, v in sorted(strata.items(), key=lambda kv: int(kv[0].split()[0][1:]))},
        "sample": sample,
    }
    text = json.dumps(manifest, indent=1, default=str) + "\n"
    MANIFEST.write_text(text, encoding="utf-8", newline="\n")
    FREEZE.write_text(json.dumps({"manifest": MANIFEST.name, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                                  "frozen_at": manifest["frozen_at"], "seed": SEED, "n": len(sample)}, indent=1) + "\n",
                      encoding="utf-8", newline="\n")
    print(json.dumps({k: manifest[k] for k in ("stratum_sizes", "sample_sizes")}, indent=1), f"\nsampled {len(sample)}")


if __name__ == "__main__":
    sys.exit(main())
