# Manufacturing coverage diagnosis (research workstream C)

**Status: research only.** Nothing here changed the production graph, `site/data/` or any frozen file. Adjudication
and gold labels were produced by the AI assistant from the raw label text and are marked as such throughout.

Files in this directory:

| File | What it is |
|---|---|
| `coverage_sample_manifest.json`, `coverage_sample_FREEZE.json` | the frozen 120-product sample (seed `fineprint-coverage-diagnosis-2026-10-22`, SHA-256 `560a3fdd…`, frozen at commit `4065e0e` before any inspection) |
| `coverage_cases.json`, `coverage_cases_digest.md` | raw-source inspection of every sampled label: structured scan, free-text statements with section and offset, identity facts, live DailyMed version check |
| `coverage_adjudication.csv` | one row per product: primary explanation A–G, recoverability class, flags, evidence reference, note |
| `coverage_estimates.json` | per-stratum counts with Wilson intervals and population-weighted estimates |
| `population_scan.json` | exact counts over all 52,747 canonical labels for the structured facts the sample surfaced |
| `c4_gold_makers.json`, `c4_results.json` | the rules-versus-LLM extraction experiment (gold, scores, facility matching) |
| `scripts/research/coverage_sample.py`, `coverage_diagnose.py`, `coverage_estimates.py`, `population_scan.py`, `c4_extract_eval.py` | reproduce every number below |

## 1. Denominators reproduced

The `fineprint` database at graph build 8 (DailyMed release 2026-10-16, FDA registration files as of 2026-10-19, no
refresh applied) reproduces the published reference exactly: 80,508 products; 24,614 DIRECT; 435 TENTATIVE;
1,002 UNKNOWN_SITE; 54,457 NO_MANUFACTURE_EVIDENCE split 28,123 / 18,453 / 7,762 / 119 by reason. The graph
fingerprints equal the reference in `docs/REPRODUCIBILITY.md`.

The only later refresh ran in the scratch database `fineprint_refresh` (daily update of 2026-10-19 applied, 207
sets at a newer version, build 10). Its counts differ from the reference by small amounts and are reported
separately, not mixed in:

| Status | reference (build 8) | refreshed scratch DB (build 10) | difference |
|---|---|---|---|
| products | 80,508 | 80,510 | +2 |
| DIRECT | 24,614 | 24,620 | +6 |
| TENTATIVE | 435 | 432 | −3 |
| UNKNOWN_SITE | 1,002 | 1,002 | 0 |
| NO_MANUFACTURE_EVIDENCE | 54,457 | 54,456 | −1 |
| OTHER_OPERATIONS_ONLY / NO_ESTABLISHMENT_BLOCK | 28,123 / 18,453 | 28,125 / 18,450 | +2 / −3 |

## 2. Frozen sample (C1)

120 products in seven strata (25 / 25 / 25 / 15 of the four no-evidence reasons, 15 UNKNOWN_SITE, 10 TENTATIVE,
5 DIRECT positive controls), drawn by `random.Random(seed).sample` over rows ordered by natural key. The manifest
records the build, all table fingerprints, every source-file hash, and each product's release part, archive member,
member and XML SHA-256. Small strata are oversampled on purpose: **raw sample proportions are not prevalence**;
population figures below are weighted by stratum size.

## 3. What the raw labels say (C2)

Every label was re-opened from the release part (hash-verified) and inspected with code that imports nothing from
`fineprint`: every `<performance>` element in the document, the operations naming the product, MANUFACTURE anywhere
in the label, unscoped operations, API MANUFACTURE, kit relations, operation codes that match no product,
`asEquivalentEntity` source NDCs, establishment FEI ids and addresses, and the narrative text for manufacturing-role
statements. Identities were re-resolved against the dated DECRS files, and DailyMed's live history was checked for
version drift.

Primary explanation per sampled product (the AI adjudication; evidence references in the CSV):

| Stratum (population) | n | A absent | B parser missed | C free text only | D unscoped op | E identity | F version | G unresolved | P positive |
|---|---|---|---|---|---|---|---|---|---|
| OTHER_OPERATIONS_ONLY (28,123) | 25 | 13 | 0 | 12 | 0 | 0 | 0 | 0 | – |
| NO_ESTABLISHMENT_BLOCK (18,453) | 25 | 13 | 0 | 12 | 0 | 0 | 0 | 0 | – |
| ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT (7,762) | 25 | 4 | 0 | 8 | 13 | 0 | 0 | 0 | – |
| ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT (119) | 15 | 5 | 0 | 10 | 0 | 0 | 0 | 0 | – |
| UNKNOWN_SITE (1,002) | 15 | 0 | 0 | 0 | 0 | 15 | 0 | 0 | – |
| TENTATIVE (435) | 10 | 0 | 0 | 0 | 0 | 10 | 0 | 0 | – |
| DIRECT (24,614) | 5 | – | – | – | – | – | – | – | 5 |
| **Total** | **120** | **35** | **0** | **42** | **13** | **25** | **0** | **0** | **5** |

F (version or data inconsistency) never explained a missing site; it appears as a secondary note on four labels whose
canonical version has no official publication date (the known 837-set metadata gap) and three whose set has a newer
version on DailyMed today than in the 2026-10-16 release (expected drift). The five DIRECT controls were confirmed in
the raw XML and their text was consistent with the structured site.

What the strata turned out to be:

- **OTHER_OPERATIONS_ONLY is the repackager stratum.** All 25 sampled labels are repackager or relabeler labels whose
  only operations are REPACK/RELABEL, and all 25 cite the originator product through `asEquivalentEntity`
  (structured source NDC). 12 of 25 also print "Manufactured by: <company>, <place>", usually the originator's
  contract maker at a city or head-office address.
- **NO_ESTABLISHMENT_BLOCK** labels name a distributor or "manufactured for" party in 13 of 25 and a maker company in
  12 of 25; 4 of 25 are repackager labels with a source NDC. The establishment data for these products lives in FDA
  listing submissions, not in the human-Rx label release: it is absent from the inspected source, not missed.
- **ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT** splits in two: 13 of 25 have an unscoped MANUFACTURE (eleven are
  allergenic-extract or medical-gas labels whose single establishment is not in any registration file), and 12 of 25
  have only unscoped REPACK/RELABEL plus a source NDC.
- **ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT** is mostly multi-strength labels where the listing scopes MANUFACTURE
  to sibling products; in 7 of 15 the text names the label's own establishment or contradicts it (one product says
  "MADE IN USA" while both listed sites are abroad), so only a person can decide.
- **UNKNOWN_SITE and TENTATIVE** are what the rules say they are: a structured MANUFACTURE whose DUNS is unregistered
  (compounders, medical-gas fillers, firms that have closed: Akorn, Teligent, Mutual) or stale, or whose FEI changed
  across snapshots. In three labels the structured assertion itself is doubtful: a labeler lists itself as
  manufacturer while its text says the product is made for it (S098, S104), and a repackager asserts MANUFACTURE
  beside REPACK/RELABEL (S115).

**Parser defects: none.** No sampled label had a `performance` element the parser cannot see, an operation at the
wrong depth, or an operation code that matches no product (database-wide: 0 `unmatched_code` assertions, 0 dead
letters). Category B is empty. What the parser does not *store* is the `asEquivalentEntity` source NDC, which is a
cross-reference rather than a manufacturing assertion; it is the subject of the main recommendation.

## 4. What is recoverable (C3)

Recoverability class per stratum (one class per product; priority positive control › identity blocker › structured
cross-reference › human judgment › free-text candidate › genuine absence):

| Stratum | n | structured cross-reference | free-text candidate | identity blocker | genuine absence | human judgment |
|---|---|---|---|---|---|---|
| OTHER_OPERATIONS_ONLY | 25 | 25 | 0 | 0 | 0 | 0 |
| NO_ESTABLISHMENT_BLOCK | 25 | 4 | 12 | 0 | 9 | 0 |
| ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT | 25 | 12 | 0 | 13 | 0 | 0 |
| ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT | 15 | 3 | 0 | 0 | 5 | 7 |
| UNKNOWN_SITE | 15 | 0 | 0 | 13 | 0 | 2 |
| TENTATIVE | 10 | 0 | 0 | 9 | 0 | 1 |

Population-weighted estimates for the 54,457 no-evidence products (95% normal-approximation interval; the sum of
per-stratum Wilson intervals is wider and is in `coverage_estimates.json`):

| Quantity | estimate | 95% interval |
|---|---|---|
| label cites a structured source NDC (repackager cross-reference) | 34,825 | 31,771–37,879 |
| label prints a "manufactured by" company (physical text claim) | 25,230 | 18,479–31,966 |
| …of which the company exact-matches a registered firm name (raw candidate) | 10,355 | 4,891–15,818 |
| free-text candidate with no structured cross-reference | 8,857 | 5,246–12,469 |
| identity blocker (unscoped MANUFACTURE by an unregistered DUNS) | 4,036 | 2,519–5,554 |
| genuine absence (nothing in the label names a maker) | 6,683 | 3,221–10,160 |
| needs human judgment | 56 | 20–75 (small-sample; true value could be far higher) |
| **independently verified links from text** | **0** | – |

The sample estimates were then replaced by exact counts for the structured facts, from a scan of every canonical
label (`population_scan.json`, 52,747 documents, 17 minutes):

| Stratum | products | with source NDC | source product is DIRECT in the graph | TENTATIVE | UNKNOWN_SITE | source has no evidence | source NDC not in graph | label says "manufactured by" (strict rule) |
|---|---|---|---|---|---|---|---|---|
| OTHER_OPERATIONS_ONLY | 28,123 | 27,557 (98.0%) | 16,791 | 178 | 128 | 7,228 | 3,232 | 15,687 |
| NO_ESTABLISHMENT_BLOCK | 18,453 | 5,002 (27.1%) | 2,877 | 15 | 16 | 1,638 | 456 | 6,532 |
| ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT | 7,762 | 3,679 (47.4%) | 725 | 13 | 30 | 856 | 2,055 | 2,020 |
| ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT | 119 | 21 | 3 | 0 | 0 | 7 | 11 | 45 |
| **no-evidence total** | **54,457** | **36,259 (66.6%)** | **20,396 (37.5%)** | 206 | 174 | 9,729 | 5,754 | 24,284 (44.6%) |

The sample-weighted estimates (34,825 and 25,230) sit inside these exact counts' neighbourhood, which is the
expected behaviour of a correctly weighted stratified sample. The unscoped stratum holds 4,317 products whose label
has an unscoped MANUFACTURE; 680 of them are single-product labels.

Raw candidates versus verified links: a "manufactured by" company name is a raw candidate. Resolving it to a facility
needs a name or address match against the registration file, which the project's rules forbid for DIRECT because a
company name is not a site. No text-derived link was verified. The structured source NDC is different in kind: it
points at another product whose own label already carries a verified, product-scoped MANUFACTURE assertion.

## 5. Rules versus LLM extraction (C4)

**Justification.** The sample does contain free-text maker statements in bulk (42 of 120 primary C; 56 of 120 labels
name a maker somewhere), so the extraction step was worth measuring. Whether anything *verifiable* follows is the
facility-matching question, measured separately.

**Design.** Evaluation unit: the 120 frozen labels. Both methods saw exactly the same excerpt per label (every
keyword window of ±500 characters, merged, manufacturing windows first, at most 6,000 characters). Gold: the AI
assistant's adjudication of the maker company and printed location per label, frozen in `c4_gold_makers.json`
before scoring; three gold entries were corrected after the LLM surfaced statements the digest rule had missed
(all three corrections went the LLM's way, recorded in the file). Baseline: the deterministic rule in
`coverage_diagnose.py` (capitalised role keyword plus "by/for", first "Manufactured by"/"Manufacturer:" statement,
company = text up to the first comma or period). LLM: a Claude subagent inside this session with a tight prompt
(role vocabulary, explicit exclusions, verbatim quote required, no outside knowledge), 20 labels per call, no API
charge. A first LLM round on badly truncated excerpts was discarded unscored (`research/c4/round1`).

| Metric (120 labels, 56 with a maker in the excerpt) | deterministic baseline | LLM |
|---|---|---|
| maker present / absent decided correctly | 109 / 120 | 120 / 120 |
| maker company correct | 47 / 56 | 55 / 56 (the one miss is a scorer artefact on "Mylan; Apotex per strength") |
| false assertion of a maker where there is none | 5 ("Produced by air liquefaction") | 0 |
| wrong company | 3 (fused name, "Packed by", "Dr") | 0 |
| missed maker | 6 ("Manufactured In <country> By:", "Manufactured for … By:", glued "…-36Manufactured by") | 0 |
| printed location correct | 35 / 48 | 54 / 54 |
| supporting quote verbatim in the text | 55 / 55 | 56 / 56 |
| latency | milliseconds | 34–70 s per 20 labels (1.7–3.5 s per label) |
| cost | none | ≈71–86k tokens per 20 labels (≈4k per label); no API charge in-session; ≈220M tokens to run over the 54,457 no-evidence labels |

**Facility matching, evaluated separately and deterministically** on the 56 gold makers (exact normalised firm-name
match against the dated DECRS file, then the printed city): 33 have at least one exact-name row, 10 resolve to a
single FEI by name alone, 9 by name plus city, 23 match nothing (foreign plants with city-level addresses, fused
names, head-office addresses). Even perfect extraction therefore yields a unique registered facility for about one
maker in six, and that facility is an inference from a company name, which the graph's rules do not admit as DIRECT.

**Reading.** The LLM is better at the extraction step: it fixes every baseline miss, all five false positives and
all location errors, with every quote verbatim. But the increment is 8 labels in 120 and every miss is a three-rule
fix (recognise "Manufactured in X by", "Manufactured for … By:", and keywords glued to a preceding token; drop
"produced by air liquefaction"). Neither method moves a single product to a verified site, because the binding
constraint is identity, not text. A production LLM extractor would spend about 220M tokens to produce company names
that cannot become DIRECT edges.

## 6. Recommended fixes, ranked by engineering impact

1. **Store the structured source NDC and add a cross-reference tier (GO, deterministic).** Parse
   `asEquivalentEntity/definingMaterialKind/code` (and its equivalence code) at ingest; additive migration; a derived
   status such as `VIA_SOURCE_PRODUCT` that is never DIRECT and always shows the source label's own evidence id.
   Exact population: 36,259 no-evidence products cite a source NDC and 20,396 of them point at a product that is
   DIRECT in the current graph. If every one of those two-hop links survives review, the share of products with a
   verified product-scoped manufacturing statement reachable from the explorer rises from 30.6% (24,614 of 80,508)
   to 55.9% (45,010), with no new inference about sites: the site statement is the originator's, already verified by
   the existing rules. What still needs a person: a seeded review of about 30 links to confirm that the cited source
   product is the same product (the equivalence is the repackager's assertion), the handling of source codes that
   match more than one current product, and the wording in the explorer.
2. **Human-review lists from the assertion-quality flags**: 139 products where a repackager asserts MANUFACTURE
   beside REPACK/RELABEL (19 DIRECT edges), and labels whose structured manufacturer is the labeler while the text says
   "manufactured for" it (3 of 120 in the sample; a targeted text scan can list them). No rule change: a person
   decides.
3. **Disclose the publication-date gap**: 837 canonical sets (1,204 products) have no official publication date
   (730 absent from the metadata file, 107 version mismatches). Cosmetic; METRICS and explorer wording.
4. **Research-extractor rule fixes** (only if text hints are ever shown to humans): the three patterns above plus the
   air-liquefaction exclusion. Not a production change.
5. **Do not** infer a product scope from an unscoped MANUFACTURE in a single-product label (680 products), and do not
   match company names or addresses to the registration file. Both would be inference from identity, which the
   project forbids; the 4,036 unscoped-and-unregistered products need registration data, not extraction.

## 7. Realistic coverage improvement and decision

- **Structured, verifiable:** up to 20,396 additional products reachable through their originator's verified DIRECT
  evidence (exact count, pending the review in item 1). A further 206 reach a TENTATIVE originator and 174 an
  UNKNOWN_SITE originator; 9,729 point at an originator that itself lacks evidence.
- **Free text:** about 25,000 labels print a maker's company name; roughly 10,000 of those names exact-match a
  registered firm; none can be verified to a site without name-based inference. Recoverable as human-review hints at
  most; 0 verified links.
- **Identity blockers:** about 4,000 unscoped products plus the 1,002 UNKNOWN_SITE and 435 TENTATIVE products depend
  on registration coverage (FDA DECRS), not on labels.
- **Genuine absence:** roughly 6,700 products whose label names no maker at all, plus the labels that give only a
  country.

**Decision on extraction expansion: NARROW.** GO for the structured source-NDC cross-reference as a new, clearly
labelled tier. NO-GO for an LLM free-text extraction feature: it is more accurate than the rules at the text step,
but the step it improves is not the one that limits coverage, and its output cannot enter DIRECT evidence.

## 8. Limitations

- The adjudication and the extraction gold were produced by the AI assistant, not a person; the LLM arm was a
  Claude subagent in the same session, so the experiment's two sides are not independent. Three gold corrections
  were made after seeing LLM output; all are documented in the gold file.
- The sample is 120 products; per-stratum intervals are wide (shown above), and the 119-product stratum was sampled
  at 15, so its weighted contribution is small but its proportions are rough.
- The population scan counts the structured facts exactly but counts text statements with the strict rule, which
  misses the three patterns above and counts "produced by air liquefaction"; its text columns are indicative only.
- Source-NDC status was looked up by normalised 5-4 product code; a code shared by several current products counts as
  DIRECT if any of them is.
- The live DailyMed checks describe today's state, not the release's.
