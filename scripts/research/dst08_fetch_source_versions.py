"""DST-08 rule v2 inputs: the DailyMed version history and archived label versions behind every conflicting reference.

  python -I scripts/research/dst08_fetch_source_versions.py --db fineprint_dst08

Scope, fixed in docs/research/dst08/SOURCE_NDC_V2_DESIGN.md (section 3) before this script first ran: for every
reference that is ELIGIBLE under rule v1 and whose citing and current source labels state a conflicting physical
characteristic (lineage.physical_check.conflict),

  - the citing set's history and the source set's history (DailyMed SPL history service);
  - every source version the history lists, from 1 to the release's canonical version (DailyMed version archive).

Every response is cached with its provenance by fineprint.historical.Fetcher (generic User-Agent, a pause between
requests) under $FINEPRINT_DATA/research/dst08/history/. An archived version is recorded with a status and is never
used unless it is a ZIP with exactly one XML file whose set id and version are the ones requested.

Output: docs/research/dst08/source_history_manifest.json, which freezes what was retrieved (version lists with dates;
each archived version's status, hashes, document id and effective time). This script decides nothing;
lineage.validate_v2 reads the manifest and the cache.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from fineprint import config, dailymed, db, historical, lineage, net, spl  # noqa: E402

OUT = REPO / "docs" / "research" / "dst08" / "source_history_manifest.json"
CACHE = config.data_dir() / "research" / "dst08" / "history"

TARGETS_SQL = """
SELECT lower(cd.set_id), cd.version, lower(x.source_set_id), x.source_version
FROM lineage.source_resolution x
JOIN lineage.source_reference r USING (reference_pk)
JOIN lineage.physical_check p USING (reference_pk)
JOIN national.spl_document cd ON cd.document_pk = r.document_pk
WHERE x.status = 'ELIGIBLE' AND p.conflict
ORDER BY r.reference_pk"""


def history(f: historical.Fetcher, set_id: str) -> dict:
    start = len(f.log)
    versions = historical.history(f, set_id)
    pages = [{"url": e["url"], "sha256": e["sha256"], "retrieved_at": e["retrieved_at"], "missing": e["missing"]}
             for e in f.log[start:]]
    return {"status": "ok" if versions else "unavailable", "versions": versions or [], "pages": pages}


def archived(f: historical.Fetcher, set_id: str, version: int) -> dict:
    url = dailymed.GETFILE_VERSION.format(setid=set_id, version=version)
    rel = f"spl/{set_id}_v{version}.zip"
    path, prov = f.get(url, rel, role="historical", missing_ok=True)
    rec = {"set_id": set_id, "version": version, "url": url, "retrieved_at": prov.get("retrieved_at"),
           "http_status": prov.get("status")}
    if path is None:
        return {**rec, "status": f"http_{prov.get('status')}"}
    data = path.read_bytes()
    rec.update(zip_path=rel, zip_sha256=hashlib.sha256(data).hexdigest())
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            xmls = [i.filename for i in z.infolist() if i.filename.lower().endswith(".xml")]
            if len(xmls) != 1:
                return {**rec, "status": f"xml_members_{len(xmls)}"}
            xml = z.read(xmls[0])
    except zipfile.BadZipFile:
        return {**rec, "status": "not_a_zip"}
    rec.update(xml_member=xmls[0], xml_sha256=hashlib.sha256(xml).hexdigest())
    try:
        doc = spl.parse_spl(io.BytesIO(xml))
    except Exception as e:  # recorded per version, never fatal
        return {**rec, "status": f"unparseable:{type(e).__name__}"}
    rec.update(document_id=(doc["document_id"] or "").lower(), effective_time=doc["effective_time"],
               served_set_id=(doc["set_id"] or "").lower(), served_version=doc["version"])
    ok = rec["served_set_id"] == set_id and str(rec["served_version"]) == str(version)
    return {**rec, "status": "ok" if ok else "served_other_document"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint_dst08")
    a = ap.parse_args()
    with db.connect(a.db) as c:
        targets = c.execute(TARGETS_SQL).fetchall()
        build = c.execute("SELECT build_id, rule_version, code_commit, code_dirty FROM lineage.build "
                          "WHERE status = 'completed' ORDER BY build_id DESC LIMIT 1").fetchone()
        release = c.execute("SELECT release_label FROM national.source_file WHERE kind = 'dailymed_human_rx_full_part' "
                            "ORDER BY 1 DESC LIMIT 1").fetchone()[0]
    f = historical.Fetcher(CACHE)
    citing = sorted({t[0] for t in targets})
    source_now = {}
    for _, _, s, v in targets:
        source_now[s] = max(v, source_now.get(s, 0))
    hist: dict[str, dict] = {}
    for n, s in enumerate(sorted(set(citing) | set(source_now)), 1):
        hist[s] = history(f, s)
        hist[s]["roles"] = [r for r, members in (("citing", citing), ("source", source_now)) if s in members]
        if n % 50 == 0:
            print(f"history: {n} sets", flush=True)
    docs = []
    for n, (s, now) in enumerate(sorted(source_now.items()), 1):
        for v in hist[s]["versions"]:
            if v["version"] <= now:
                docs.append(archived(f, s, v["version"]))
        if n % 25 == 0:
            print(f"archived: {n}/{len(source_now)} source sets, {len(docs)} versions", flush=True)
    out = {
        "generated_at": net.utc_now(), "user_agent": net.USER_AGENT, "release_label": release,
        "lineage_build": {"build_id": build[0], "rule_version": build[1], "code_commit": build[2], "code_dirty": build[3]},
        "rule": lineage.V2_RULE_VERSION,
        "scope": "every v1-eligible reference with a current physical conflict: citing and source set histories, and "
                 "every source version from 1 to the release's canonical version",
        "cache_root": "FINEPRINT_DATA/research/dst08/history",
        "targets": len(targets), "citing_sets": len(citing), "source_sets": len(source_now),
        "history_status": dict(Counter(h["status"] for h in hist.values())),
        "document_status": dict(Counter(d["status"] for d in docs)),
        "history": hist, "documents": docs,
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("targets", "citing_sets", "source_sets", "history_status", "document_status")}))


if __name__ == "__main__":
    sys.exit(main())
