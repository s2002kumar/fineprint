"""DST-08: the evidence chain of a product's source references, re-read from the release XML.

  python -I scripts/research/dst08_evidence_chain.py --db fineprint_dst08 60760-661
  python -I scripts/research/dst08_evidence_chain.py --db fineprint_dst08 --representative

Each step keeps both endpoints: the citing SPL (set, version, document, hashes) with its asEquivalentEntity element
verbatim, the resolved source SPL, the source's own DIRECT MANUFACTURE element verbatim and the FDA registration line.
An excluded reference is returned with its reasons and no manufacturing step. ``--representative`` writes the chains
of a fixed list of products (one per kind of outcome) to docs/research/dst08/evidence_chains.json;
``--representative-v2`` writes one product per rule v2 outcome, with its version check, to evidence_chains_v2.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from fineprint import db, lineage  # noqa: E402

OUT = REPO / "docs" / "research" / "dst08" / "evidence_chains.json"
REPRESENTATIVE = {
    "60760-661": "eligible: single hop to a source with one DIRECT site (sample R9-01)",
    "63629-1183": "eligible: two active ingredients, both equal to the source's (sample R9-08)",
    "67046-1523": "eligible: the source lists three DIRECT sites; the chain names all three, not one (sample R9-09)",
    "0404-9762": "eligible only after exact-decimal strength comparison ('1' against '1.0') (sample R5-10)",
    "76204-018": "citing product is itself DIRECT; its own MANUFACTURE site is the source's site (sample R1-06)",
    "72258-020": "medical gas: citing transfiller is DIRECT, source lists many sites (sample R1-07)",
    "55154-3551": "excluded: two-hop chain through a relabeler (sample R5-01)",
    "53149-4913": "excluded: two candidate source sets naming different sites (sample R1-10)",
    "54868-5183": "excluded: a package code whose prefix would match one source (sample R3-06)",
    "68788-4100": "excluded: dosage form differs from the source's (sample R5-02)",
    "63187-911": "excluded: kit; the source has no DIRECT evidence (sample R2-03)",
}
# Rule v2 (final validation): one product per outcome of the version check, plus a v1-basis link; written to
# evidence_chains_v2.json so the v1 record above stays as committed.
REPRESENTATIVE_V2 = {
    "60760-661": "v2 eligible on the v1 basis: no physical conflict (sample R9-01)",
    "53002-3202": "v2 eligible after the version check: drift resolved (E160 in the 2019 source label, 160 now), site continues",
    "50090-7007": "v2 eligible after the version check: notation only (RX692 against RX692;RX692), sites continue",
    "53808-0858": "v2 eligible after the version check: one of two flavours the source lists; one of two sites continues",
    "54868-4102": "v2 excluded: drift resolved (GG931 then, NL4 now) but the source label then named no product-scoped site",
    "21695-630": "v2 excluded: confirmed conflict, a different tablet (IG;209 against D;74 at the relevant date)",
    "42254-121": "v2 excluded: confirmed conflict, the citing label carries the source's other-strength imprint",
    "53808-0311": "v2 excluded: unresolved, the source set was first published after the citing label",
    "21695-494": "v2 excluded: missing evidence, the archive returns 404 for every version of the source set",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="fineprint_dst08")
    ap.add_argument("--representative", action="store_true")
    ap.add_argument("--representative-v2", action="store_true")
    ap.add_argument("ndc", nargs="*")
    a = ap.parse_args()
    targets = (REPRESENTATIVE if a.representative else REPRESENTATIVE_V2 if a.representative_v2
               else {n: "" for n in a.ndc})
    with db.connect(a.db) as c:
        out = {n: {"why_chosen": why, "chain": lineage.evidence_chain(c, n)} for n, why in targets.items()}
        build = c.execute("SELECT build_id, rule_version, graph_build_id, code_commit, finished_at FROM lineage.build "
                          "ORDER BY build_id DESC LIMIT 1").fetchone()
    doc = {"lineage_build": {"build_id": build[0], "rule_version": build[1], "graph_build": build[2], "code_commit": build[3],
                             "finished_at": build[4]}, "products": out}
    text = json.dumps(doc, indent=1, default=str) + "\n"
    out_path = OUT if a.representative else OUT.with_name("evidence_chains_v2.json") if a.representative_v2 else None
    if out_path:
        out_path.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {out_path}" if out_path else text)


if __name__ == "__main__":
    sys.exit(main())
