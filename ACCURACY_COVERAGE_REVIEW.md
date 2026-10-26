# Accuracy and coverage review gate

Research branch `research/accuracy-coverage-2026-10`, 2026-10-22, on top of v1.2.0 (`1b61045`). Nothing in the
production graph, `site/data/`, the frozen Rocky Mount files or `docs/human_audit_verdicts.csv` was changed. No release
was made and Baxter North Cove was not started. Full detail: `docs/research/AUDIT_ACCURACY_REPORT.md` (workstream B)
and `docs/research/COVERAGE_DIAGNOSIS.md` (workstream C). All verification below is AI-assisted; no human audit has
been performed.

## 1. What was independently checked, and what remains unverifiable

Checked by a separate code path (`scripts/research/verify_audit_sample.py`, no `fineprint` imports) against original
sources: all 33 human-audit worksheet cases. For the 20 current links: release bytes located by set ID and re-hashed,
FDA's SPL-by-document-ID copy fetched live (byte-identical in 20/20), the cited element re-resolved two ways, product
scope and NDC normalisation, DUNS→FEI against the dated FDA files on disk (generation dates read from the files), FEI
history across five snapshots, version selection from the release contents plus official metadata, and the documented
confidence rule re-applied. For the 11 historical packages: cached pre-cutoff documents against fetch provenance and
the frozen hashes, publication dates from the cached and the live DailyMed history (10/10 agree), A5 classification
re-derived, warning-list membership from the appendix PDF's text layer (65 distinct tokens, matching P = 65). For the
identity cases: the 2022 archive re-fetched from web.archive.org (identical bytes) and the dated current file.

Result: 33 VERIFIED, 0 FAILED, 0 CANNOT_TELL; 620/620 checks. Today's live registration file (2026-10-21) shows no
drift for the 16 sampled DUNS.

Unverifiable by this method: whether the documented rules are the right rules (the verifier encodes the same spec);
whether a submission is true (FDA and DailyMed copies corroborate integrity, not truth); anything a person would see
on the DailyMed HTML or the DECRS web search, which were not exercised; and the sample itself, which the project's
own seeded script drew.

## 2. Does the graph contain confirmed errors?

No confirmed errors. No parser bug: no operation element the parser cannot see, 0 operation codes that match no
product in the whole database, 0 dead letters. The confidence rule reproduced every sampled status, including the
three TENTATIVE and three UNKNOWN cases for the stated reasons. Two assertion-quality patterns were found that the
rules cannot judge and a person should: a labeler listing itself as manufacturer while its text says "manufactured
for" it, and a repackager asserting MANUFACTURE beside REPACK/RELABEL (139 products, 19 DIRECT edges database-wide).
The C19/C20 controls were confirmed weak at product level and replaced by 23 frozen, independently checked negative
controls (`docs/research/AUDIT_CONTROLS_V2.md`) with synthetic regression tests.

## 3. Why products lack manufacturing evidence

The published denominators reproduce exactly from graph build 8. From 120 frozen, raw-inspected labels and an exact
scan of all 52,747 canonical labels:

- **OTHER_OPERATIONS_ONLY (28,123)** is the repackager stratum: 98% of these labels cite the originator product
  through a structured source NDC that the parser does not store; their only operations are REPACK/RELABEL.
- **NO_ESTABLISHMENT_BLOCK (18,453)**: the establishment data lives in FDA listing submissions, not in the label;
  27% are repackager labels with a source NDC; about half print a maker's company name in free text.
- **ONLY_UNSCOPED_OPERATIONS (7,762)**: 4,317 have an unscoped MANUFACTURE, mostly allergenic-extract and medical-gas
  labels whose establishment is unregistered; 47% are repackager labels with a source NDC.
- **ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT (119)**: multi-strength labels where the listing scopes MANUFACTURE to
  siblings; the text often names the same company or contradicts the listing; human judgment.
- **UNKNOWN_SITE and TENTATIVE**: unregistered, closed or stale establishments, as designed.

No case was "manufacturing information in structured XML missed by the parser".

## 4. How much extra verified coverage is realistically recoverable

Through the structured source-NDC cross-reference: 36,259 no-evidence products cite a source NDC and **20,396 of them
point at a product that is DIRECT in the current graph**. If those two-hop links survive review, products with a
verified, product-scoped manufacturing statement reachable from the explorer rise from 30.6% to 55.9%, with no new
inference about sites. From free text: about 25,000 labels name a maker and about 10,000 names exact-match a
registered firm, but 0 links are verifiable without name-based inference, which the rules forbid. About 4,000
unscoped-and-unregistered products plus the 1,437 UNKNOWN_SITE/TENTATIVE products need registration data, not labels.

## 5. Does LLM extraction add value over deterministic methods?

At the text step, yes but marginally: on 120 labels (56 with a maker) the constrained LLM got 55/56 companies and
54/54 locations with 0 false assertions and every quote verbatim, against the rule baseline's 47/56, 35/48 and 5
false assertions. The whole gap is three rule fixes. At the step that limits coverage, no: only 9–10 of the 56 named
makers resolve to a single registered facility even deterministically, and only by company name. Cost would be about
4k tokens and 2–3 s per label. **NO-GO** for an LLM extraction feature; **GO** for the structured cross-reference.

## 6. Safe changes for a future release

1. Store `asEquivalentEntity` source NDCs at ingest (additive migration) and expose a `VIA_SOURCE_PRODUCT` tier that
   is never DIRECT and cites the originator's evidence id. Design and a seeded human review of about 30 links first.
2. Keep `tests/test_negative_controls.py` and the v2 controls as the negative half of the human audit.
3. Worksheet wording: "publication date not in the official metadata" instead of "published None"; note that
   pre-2009 labels keep the product under an unclassified section. Disclose the 837 sets without a publication date.
4. No change to confidence rules, no inference from single-product unscoped MANUFACTURE, no name or address
   matching, no LLM extraction in production.

## 7. Remaining human-review requirements

- The human audit of the 33 original cases and the 23 v2 controls (still not performed; nothing here substitutes).
- The 139 repackager-MANUFACTURE products (19 DIRECT) and the labeler-as-manufacturer contradictions.
- The source-NDC design: equivalence semantics, codes matching several current products, explorer wording, and a
  reviewed sample of links before anything is built.
- The three gold corrections in the extraction experiment and the adjudication CSV, all AI-made.

## 8. Recommendation: NARROW

Stop here for the gate. Do not change the production graph or publish. If the user agrees, the next implementation
is the structured source-NDC cross-reference only, preceded by a design note and a human-reviewed link sample; the
LLM extraction line is closed as a negative result.

Test suite on the branch: 98 tests, all passing (PostgreSQL-backed). Commits: `4065e0e` (freeze and verification),
plus the diagnosis, experiment and review commits on the branch.
