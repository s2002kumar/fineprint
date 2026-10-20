# Rocky Mount historical evaluation (DST-04B)

**Question.** Using only records published by **2023-07-18**, can explicit SPL `MANUFACTURE` links to
Hospira Rocky Mount (DUNS `093132819`) shrink the Hospira `00409` package list while still
recovering the package NDCs Pfizer flagged after the **2023-07-19** tornado?

**What this tests.** List overlap and candidate reduction. It does **not** test shortage prediction,
inventory, exclusivity or causality. Pfizer's appendix is a post-event *low-inventory warning list*, and the
warehouse was also damaged, so it is not a list of products made at Rocky Mount. Unlisted packages are never
treated as negatives.

## Headline (measured)
> Using labels published before July 19, 2023, fineprint flagged **480** eligible package NDCs with
> Rocky Mount manufacturing links and recovered **63 of Pfizer's 65** warnings. Flagging all Hospira
> `00409` products required **890** candidates (**46% shorter list, same recall**). On the independent
> May 2023 directory cohort: **235 vs 469** candidates, again **63/65**.

| Cohort | Method | N flagged | X ∩ P | Recall (of 65) | Panel-conditional recall | Reduction vs B1 | Overlap density X/N |
|---|---|---|---|---|---|---|---|
| E (expanded, 890) | B1 all Hospira `00409` | 890 | 63 | 0.969 | 1.000 | — | 0.071 |
| E | B2 injectables | 886 | 62 | 0.954 | 0.984 | 0.4% | 0.070 |
| E | **Graph: DIRECT Rocky Mount MANUFACTURE** | **480** | **63** | **0.969** | **1.000** | **46.1%** | **0.131** |
| M (May 2023 directory, 469) | B1 | 469 | 63 | 0.969 | 1.000 | — | 0.134 |
| M | B2 | 467 | 62 | 0.954 | 0.984 | 0.4% | 0.133 |
| M | **Graph** | **235** | **63** | **0.969** | **1.000** | **49.9%** | **0.268** |
| both | B3 already-short | — | — | **NOT EVALUABLE** | | | |

- **Matching the graph's recall:** B1 needs its full list (890 / 469). B2 cannot reach it at any size, because it excludes oral/inhalation acetylcysteine `00409-3308-03`.
- **B2 adds almost nothing:** 886 of 890 Hospira `00409` packages are injectable.
- **Overlap density is not precision.** Any of the 417 flagged-but-unlisted packages (E; 172 in M) may still be made at Rocky Mount.

## Protocol and no-leakage controls
Each step was committed before the next; full text is in [historical_panel_plan.md](historical_panel_plan.md).

1. **Method pre-registered** (§1–§8) before any frame discovery, while the outcome stayed sealed.
2. **Amendments A1–A4.2** (frame reconciliation and recovery) committed *before each run*.
3. **A5** (cohorts, deduplication, classification precedence, baselines, audit design, normalization,
   metrics) committed **before** the freeze was computed.
4. **Freeze** committed and tagged `dst04b-freeze`.
   - `FREEZE_MANIFEST.json` SHA-256 `361e21bae2bc4fb31e68dfe2f9cf33d03dc8dfb7130c638b1f5012c8596593e3`.
   - The 6 frozen files: `cohort_E` `7e89afed…`, `cohort_M` `ee425813…`, `documents` `af7ba3bc…`,
     `identity` `880d1fa4…`, `audit_sample` `c976dfc6…`, `freeze_summary` `32ec7001…`.
   - The freeze re-derives **byte-identically** from the cached sources.
5. **Link audit** completed and committed before unsealing.
6. **Unsealing** runs only if every frozen file equals its tagged blob. Afterwards, two
   **text-extraction-only** fixes (A5.1, A5.2) repaired the PDF text layer: `00409 - 3308 - 03` and
   `00409-114 1-02`. P was validated against the appendix's 65 `00409` rows (65 tokens, 65 distinct,
   0 unparsed). No cohort, classification, baseline or metric changed after unsealing.

**Inputs.** Every cutoff document has a DailyMed history publication date ≤ 2023-07-18 and an
XML `effectiveTime` ≤ 2023-07-18, and each one is re-hashed before use. The freeze reported **0 leakage
violations**, an allow-listed historical source domain, and no database driver loaded (no current-release
data path).
- **Discovery source A** is today's DailyMed labeler search: it supplies set IDs only, and all content comes from pre-cutoff versions.
- **Discovery source D** is FDA's NDC Directory, generated 2023-05-05 and archived 2023-05-07.

**Disclosed contamination.**
- The researcher and assistant had seen Pfizer positives before this work, and the five DST-00 probes were chosen with that knowledge. They are not in any rule.
- No blinding is claimed.

## Cohorts
| | Count |
|---|---|
| Universe sets (A ∪ D) | 247 |
| Admissible cutoff documents | 235: getFile 189, by document ID 37, monthly-archive range recovery 9 |
| Sets with no retrievable cutoff version | 1 (`99a0571d` v14; none of its packages is a positive) |
| Sets first published after the cutoff | 11 |
| Candidate package rows → distinct 11-digit NDCs (E) | 896 → **890** (5 within-document repeats, 1 NDC in two sets) |
| …listed in May 2023 (M) / not listed | **469** / 421 |
| May 2023 listed packages: in cutoff docs / marketing ended / no admissible doc | 475 / 6 / 2 (of 477) |
| E classification | DIRECT 480 · OTHER_SITE 253 · UNKNOWN_NO_ESTABLISHMENT 109 · UNKNOWN_NO_MANUFACTURE_OP 40 · RM_SECONDARY_ONLY 8 |

**Rocky Mount identity.** DUNS `093132819` ↔ FEI `1021343` ↔ Highway 301 North, from the 2013/2015 SPL
facility filing and the 2022-10-13 FDA registration record. No other DUNS shares that FEI. This is
identity only: 2023 registration status is not established (A2).

## Link audit (pre-unsealing, seeded sample)
**40/40 VERIFIED:** 20 DIRECT, 10 OTHER_SITE and 10 controls.
- An independent ElementTree extraction from the hash-verified raw XML agreed with every frozen
  classification, and each quoted `<performance>` element was read.
- DIRECT-link precision on the sample is **20/20** (Clopper–Pearson 95% lower bound 0.83); all 40 combined give a lower bound of 0.91.
- **Auditor: the AI assistant, not a human.** The worksheet with every excerpt is in
  `evidence/historical/frozen/audit_worksheet.md` for human spot-checks.

## Failure analysis
- **Uncovered positives (2/65).** `00409-5816-11` and `-31` are "Sterile Empty Vial". DailyMed has no drug SPL for that
  product code (checked 2026-10-20), so this is a scope limit of an SPL drug-label method, not a missed link.
- **In-cohort positives not flagged: 0.** All 63 in-cohort positives are DIRECT. No positive fell in an UNKNOWN
  class (149/890 = 16.7% of E is UNKNOWN), so missing evidence cost no recall here. It still bounds what
  the method could detect in general.
- **Unrecovered evidence versus incorrect classification.**
  - *Unrecovered:* the 2 empty vials (no SPL), 1 unretrievable set (no positives), 197 packages without an NDC in their label, and an unproven frame (no DailyMed date-archive export).
  - *Incorrect classification:* none detected. That rests on 0 non-DIRECT positives in the cohorts plus 40/40 audited links. A wrongly *flagged* package cannot be detected with this outcome list.
- **Archival recovery mattered.** 6 of the 63 recovered positives come from retired sets that today's DailyMed
  search cannot see: 5 via FDA SPL-by-document-ID retrieval and 1 via the 2023 monthly-archive range recovery.

## Exploratory, post-hoc, not pre-registered
Among the 480 flagged packages, those whose label lists Rocky Mount as the **sole** manufacturer were on the
warning list at 57/306 (18.6%). Those with Rocky Mount **plus other sites** were at 6/174 (3.4%). This is a
hypothesis for a future pre-registered test only; it is used in no metric above.

## Reproduce
Run `scripts/hist_dst04b_freeze.py --out-dir <tmp>`, which re-derives the freeze for comparison, then
`scripts/hist_dst04b_unseal_and_score.py`, which verifies the seal and scores. Both run on the cached
pre-cutoff sources described in [REPRODUCIBILITY.md](REPRODUCIBILITY.md). Results are in
`evidence/historical/evaluation_results.json`.
