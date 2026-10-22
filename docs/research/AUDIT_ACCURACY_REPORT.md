# Manufacturing graph accuracy audit (research workstream B)

**Status: AI-assisted verification, not a human audit.** The AI assistant that built fineprint wrote and ran a
separate verification path over the 33 records in `docs/HUMAN_AUDIT_WORKSHEET.md` (seed
`fineprint-human-audit-2026-10-20`, worksheet SHA-256 `9ba457a6…`). `docs/human_audit_verdicts.csv` is untouched and
unsigned. This report says what was checked, what agreed, what could not be made independent, and what to change.

Deliverables in this directory:

| File | What it is |
|---|---|
| `audit_results.json` | machine-readable result: every check for every case, with source URLs, file hashes, observations |
| `audit_evidence_table.md` | one row per case: verdict, basis, source checked, source version, observation |
| `audit_controls_v2.json`, `AUDIT_CONTROLS_V2.md` | 23 frozen replacement negative controls (B2) |
| `scripts/research/verify_audit_sample.py` | the verifier (imports nothing from `fineprint`) |
| `scripts/research/make_audit_controls.py` | draws and checks the controls |
| `tests/test_negative_controls.py` | synthetic regression tests for every control type (11 tests) |

Reproduce: `python -I scripts/research/verify_audit_sample.py` (about 20 s with cached downloads; add `--offline` to
skip the network) and `python -I scripts/research/make_audit_controls.py --db fineprint`.

## 1. Method: a separate path from the classifier

The verifier reads the claims from the worksheet markdown and re-derives each one from original sources with its own
code: its own XML walk (sibling-indexed locations, enclosing-organization DUNS, author-tree depth), its own DECRS
parser, its own implementation of the documented confidence and historical precedence rules, and its own PDF
text scan. For each current case it

1. locates the label in the DailyMed release parts by set ID from the zip directories (not from the database),
   re-hashes the nested XML and reads set ID, version and document ID from the bytes;
2. fetches FDA's SPL-by-document-ID copy live (generic User-Agent) and compares its SHA-256;
3. resolves the cited XPath both by its own walk and by ElementTree positional predicates, then checks the operation
   code, display name, product code, enclosing DUNS, establishment depth, and that the product code is a product
   of the label (with its normalised 5-4 form and name);
4. resolves the DUNS against the dated FDA files on disk (current registration generated 2026-10-19 03:00:34,
   excluded list, three archived snapshots dated 2026-08-21, 2025-12-05 and 2024-12-23; all hashed, generation date
   read from the zip member timestamp), including the FEI history across snapshots, expiry, and for stale cases
   that no newer snapshot lists the DUNS;
5. re-derives version selection from the versions actually present in the release plus the official zip-metadata
   file, and the publication date from that metadata;
6. applies the documented rule to the independently observed facts and compares confidence and reasons.

For the historical cases it verifies the cached pre-cutoff zip against both its fetch provenance and the frozen
`documents.json` hash, the XML hash, set/version, effective time, the publication date from the cached DailyMed
history and from a live re-fetch, the package under the product, the A5 classification by precedence, the Rocky
Mount locations, and warning-list membership by a whitespace-insensitive search of the appendix PDF's text layer.
For I01 it hashes the cached 2022 archive and re-fetches it from web.archive.org.

Verdicts: VERIFIED only when every assertion check passes; FAILED on any factual mismatch; CANNOT_TELL only for an
inaccessible source. Corroboration checks (live copies, display names) are recorded but never decide a verdict.

## 2. Results

| Part | Cases | VERIFIED | FAILED | CANNOT_TELL |
|---|---|---|---|---|
| Current graph links C01–C20 | 20 | 20 | 0 | 0 |
| Historical replay packages H01–H11 | 11 | 11 | 0 | 0 |
| Facility identity I01–I02 | 2 | 2 | 0 | 0 |
| **Total** | **33** | **33** | **0** | **0** |

620 individual checks ran; 620 passed. Corroboration that goes beyond the worksheet:

- FDA's SPL-by-document-ID copy was byte-identical to the release XML for all 20 current cases.
- The live DailyMed version history agreed with the cached, frozen publication date for all 10 historical labels.
- web.archive.org still serves the 2022 registration file with the frozen SHA-256 `ee642893…`; its DUNS 093132819 row
  gives FEI 1021343 and the Rocky Mount address, and no other DUNS shares that FEI in the file.
- The appendix PDF's text layer contains exactly 65 distinct `00409-xxxx-xx` package tokens, matching P = 65; every
  worksheet membership claim (yes for H01, H02, H11; no for H03–H10) matched.
- DailyMed lists no SPL for `00409-5816-11` today (H11), consistent with the "no drug label exists" claim.
- Today's live DECRS file (generated 2026-10-21) still gives the same status and FEI for all 16 sampled DUNS
  (informational; verdicts used the dated 2026-10-19 file only).

**Confidence classification.** Re-implementing the rules from `docs/ARCHITECTURE.md` on the independently observed
facts reproduced every status and reason: 14 DIRECT (C01–C12 plus the C19/C20 operation rows), 3 TENTATIVE (C13
`version_selection:ambiguous`: the metadata names version 10 while the release holds only version 9; C14 and C15
`identity:STALE_REGISTERED`: listed only in the 2024-12-23 and 2025-12-05 archives respectively, absent from the
current and excluded files and from every newer archive), 3 UNKNOWN (C16 `scope:no_product_scope`: the
performance element has no product; C17 and C18 `identity:NOT_FOUND`: absent as establishment DUNS from all five
files, and not listed as a registrant DUNS either). The 10 historical classifications reproduced under the A5
precedence from the raw elements (H09's 2006 label has no establishment block at all).

## 3. Parser and graph bugs found

**None in the sample, and none in the database-wide checks run alongside it:**

- no `performance` element outside the author tree and none at a depth other than the establishment level, in any
  sampled label (the ingest's anomaly log agrees: 0 such anomalies in 55,064 documents);
- 0 operation assertions with `product_scope = 'unmatched_code'` in the whole database, so no operation cites a
  product code the label does not define (format mismatches were a suspected defect; there are none);
- 0 dead letters; the only anomaly kinds recorded are `product_outside_product_data_section` (602 products in 305
  canonical labels, almost all pre-2009), `duplicate_product_code_in_document` (9) and
  `duplicate_operation_product_code` (2).

One false alarm is worth recording: the verifier's first draft rejected H09 because it looked for products only under
section `48780-1`; the 2006 label stores its product under an unclassified section. fineprint's model stores such
products with an anomaly flag and the graph was right. The verifier now accepts any section and records the code.

## 4. Source disagreements and inaccessible material

- No source was inaccessible. Every live fetch (20 FDA XML copies, 10 DailyMed histories, 1 NDC lookup, the 2022
  archive, today's DECRS) returned HTTP 200 on 2026-10-22.
- C13 is a genuine source disagreement, correctly classified: the official zip metadata (file `84e7cc7e…`) lists
  version 10 (upload 2026-01-12) for set `81e639d7…`, but the release parts contain only version 9. The graph keeps
  version 9, marks the selection ambiguous, and reports no publication date. Across the release this affects 107
  sets (`SINGLE_VERSION_METADATA_LISTS_OTHER`); a further 730 sets are absent from the metadata altogether, so 837
  canonical sets (1,204 products) have no publication date. The worksheet prints this as "published None"; it
  should say "publication date not in the official metadata".
- The worksheet's human instructions point at the DailyMed HTML page and the FDA DECRS web search; the verifier used
  the XML and the dated files instead, which is stricter but means the human-facing instructions themselves were not
  exercised.

## 5. Limits of this verification

- **Same author.** The classifier, the worksheet generator and the verifier were all written by the AI assistant.
  The verifier is a different code path with no shared imports, but it encodes the same documented rules, so it
  cannot detect a rule that is wrong by design; it can only detect a graph that disagrees with its own rules or with
  the sources.
- **Same sample.** The 33 cases were drawn by the project's seeded script, not by an outside party.
- **Corroboration is not independent origin.** FDA's by-document-ID copy and DailyMed's history describe the same
  submissions the release came from; agreement shows the release was not altered, not that the submission is true.
- **Claims were parsed from the worksheet by regex.** A worksheet rendering bug would be invisible if it affected
  both the claim and the check in the same way.
- **DECRS web search and DailyMed HTML were not used**; a human following the worksheet would exercise those.

## 6. Control design (B2)

C19 and C20 are weak product-level negatives: both labels also assert MANUFACTURE by DUNS 093132819 for the same
product (edges 113220 and 121361), so the product-level answer is right whether or not an operation is
mis-mapped. They are retained as operation-level checks (`is_manufacture = false` on edges 113224 and 121363, both
confirmed). `AUDIT_CONTROLS_V2.md` freezes 23 new controls drawn with seed `fineprint-audit-controls-v2-2026-10-22`
(one per label set per type): PACK (3), LABEL (3) and ANALYSIS (3) without MANUFACTURE; API MANUFACTURE only (3);
API site versus finished-dose site (3); MANUFACTURE with no product scope in a single-product label (3); MANUFACTURE
by an unresolved DUNS (3) and by a stale DUNS (2). For every control the premise holds in the raw XML by the
independent walk and the expectation holds in the graph tables (23/23). `tests/test_negative_controls.py` encodes
each type on a synthetic release so a regression in the rules fails the suite.

## 7. Corrective actions

Safe now (research branch; no production data changed):

1. Adopt the v2 controls as the negative half of the human audit and keep C19/C20 as operation checks. Done, frozen.
2. Keep `tests/test_negative_controls.py` in the suite (11 tests pass; the full suite is 98 tests).
3. Change the worksheet wording for an absent publication date and add a note that pre-2009 labels keep the product
   under an unclassified section (generator change in `scripts/make_human_audit_worksheet.py`; cosmetic, no data
   change). Proposed, not applied, because regenerating the worksheet would alter a published document.

Needing a person:

4. Perform the human audit on the original 33 cases plus the 23 controls using the public links; record verdicts in
   a new CSV for the controls and in `docs/human_audit_verdicts.csv` for the originals.
5. Review two assertion patterns that the rules cannot judge and the coverage sample surfaced (see
   `COVERAGE_DIAGNOSIS.md`): a labeler that lists itself as manufacturer while its own text says "manufactured for"
   it, and a repackager that asserts MANUFACTURE alongside REPACK/RELABEL. Database-wide, 139 products carry the
   second pattern and 19 of their edges are DIRECT; that is a short, reviewable list.
6. Decide whether the 837 sets without an official publication date should be surfaced more prominently in the
   explorer.
