"""Follow the explorer's source links for sample evidence rows and check they resolve to the cited record.

  python -I scripts/check_source_links.py --out evidence/explorer/source_links_check.json

For each sampled current-graph edge (first DIRECT and first UNKNOWN MANUFACTURE row of each example facility, as the
explorer sorts them) it requests the DailyMed label page, the version ZIP, the version history and FDA's SPL XML by
document ID, and compares that XML's SHA-256 with the hash the explorer displays. Generic User-Agent; read-only.
"""

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # works under python -I
from fineprint.net import USER_AGENT  # noqa: E402

DAILYMED = "https://dailymed.nlm.nih.gov/dailymed"
DATA = ROOT / "site" / "data"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read()


def sample_rows():
    rank = {"DIRECT": 0, "TENTATIVE": 1, "UNKNOWN": 2}
    for duns in ("093132819", "030606222"):
        b = json.loads((DATA / "current" / "examples" / f"{duns}.json").read_text(encoding="utf-8"))
        edges = [dict(zip(b["edge_columns"], e)) for e in b["edges"]]
        prod = lambda e: (b["products"][str(e["product"])][0] if e["product"] is not None else "~")  # noqa: E731
        edges = [e for e in edges if e["operation"] == "MANUFACTURE"]
        edges.sort(key=lambda e: (rank[e["confidence"]], str(prod(e)), e["set_id"], e["evidence_id"]))
        for conf in ("DIRECT", "UNKNOWN"):
            e = next((x for x in edges if x["confidence"] == conf), None)
            if e:
                d = dict(zip(b["document_columns"], b["documents"][e["set_id"]]))
                yield duns, e, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args()
    results = []
    for duns, e, d in sample_rows():
        sid, v, doc = e["set_id"], d["version"], d["document_id"]
        r = {"duns": duns, "evidence_id": e["evidence_id"], "confidence": e["confidence"], "set_id": sid, "version": v,
             "document_id": doc, "xml_sha256_shown": d["xml_sha256"]}
        st, ct, body = get(f"{DAILYMED}/drugInfo.cfm?setid={sid}")
        r["label_page"] = {"status": st, "mentions_set_id": sid.encode() in body}
        st, ct, body = get(f"{DAILYMED}/getFile.cfm?type=zip&setid={sid}&version={v}")
        r["version_zip"] = {"status": st, "is_zip": body[:2] == b"PK", "bytes": len(body)}
        st, ct, body = get(f"{DAILYMED}/services/v2/spls/{sid}/history.json?pagesize=100")
        versions = [str(x.get("spl_version")) for x in json.loads(body)["data"]["history"]]
        r["history"] = {"status": st, "lists_version": str(v) in versions, "latest_version": versions[0] if versions else None}
        st, ct, body = get(f"https://www.accessdata.fda.gov/spl/data/{doc}/{doc}.xml")
        r["fda_xml"] = {"status": st, "sha256": hashlib.sha256(body).hexdigest()}
        r["fda_xml"]["matches_shown_hash"] = r["fda_xml"]["sha256"] == d["xml_sha256"]
        r["ok"] = (r["label_page"]["status"] == 200 and r["version_zip"]["is_zip"] and r["history"]["lists_version"]
                   and r["fda_xml"]["matches_shown_hash"])
        results.append(r)
    out = {"checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "rows": len(results),
           "ok": all(r["ok"] for r in results), "results": results}
    text = json.dumps(out, indent=1) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    print(text)
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
