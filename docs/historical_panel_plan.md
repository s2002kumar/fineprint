# Pre-registered historical candidate frame — Hospira `00409`, cutoff 2023-07-18

**Status:** PRE-REGISTERED METHOD (DST-00). Written and committed *before* any frame
discovery run and before any outcome document is retrieved. Changes after this commit
must be logged in the "Amendments" section with date and reason; they may not use
outcome information.

## 1. Unit, cutoff, scope
- **Unit:** package NDC, normalized to 11-digit `5-4-2` **only** via
  `fineprint.ndc.to_11_digit` (explicit hyphen-segment rule; unhyphenated or unknown
  patterns are excluded and counted, never padded by guess).
- **Labeler scope:** packages whose raw SPL first segment is `0409` (11-digit `00409`).
  Other Hospira/Pfizer labeler codes are investigated separately and are not in the panel.
- **Cutoff:** an SPL version is admissible iff its DailyMed history-service
  `published_date` is ≤ **2023-07-18**. XML `effectiveTime` is recorded, never substituted.
- **Version rule:** for each set ID, use only the **latest admissible** version, fetched
  from `getFile.cfm?type=zip&setid=…&version=…`; served XML `setId`/`versionNumber`
  must equal the request or the set is a recorded failure. Current/2026 bulk files and
  post-cutoff versions are never used.
- **Document type:** LOINC `34391-3` (human prescription drug label), by code only.

## 2. Frame sources (independent of any outcome list)
| ID | Source | Role |
|---|---|---|
| A | DailyMed v2 `spls.json?labeler=Hospira` (all pages, at run time) → per-set history → latest admissible version | **Primary discovery** |
| B | DailyMed customer-support "all labels for a date" export for 2023-07-18 (to be requested by the researcher) | **Gold standard if received**; supersedes A as frame, A-vs-B diff reported |
| D | FDA NDC Directory snapshot captured before cutoff (Internet Archive capture of `accessdata.fda.gov/cder/ndcxls.zip`, FDA member timestamps 2023-05-05) | **Cross-check only**: package NDCs listed for `0409`; never adds a package without an admissible SPL |
| C | DailyMed monthly update archives Jun/Jul 2023 (still hosted) | Optional check that near-cutoff versions match the history service |

Known survivorship risk: A only sees set IDs DailyMed still serves in 2026. Packages
in D but not A (D-only) are reported as **uncovered**, not silently added or dropped.

## 3. Package eligibility (applied in this order; every exclusion counted by reason)
1. Package element has an NDC code (else `excluded:no_package_code`).
2. Package raw NDC normalizes via `to_11_digit` (else `excluded:ambiguous_ndc_format`).
3. Labeler segment `00409` (else out of scope).
4. Package/product `marketingAct` `effectiveTime/high` ≤ 20230718 → `excluded:marketing_ended_pre_cutoff`.
   Missing marketing data → included, flagged `marketing_unknown`.
5. Same 11-digit package in >1 set ID → one panel row, all provenance kept, conflict flagged.
Being in the frame does **not** mean marketed, stocked or shipped on 2023-07-18.

## 4. Graph classification (per package, using only its own admissible SPL version)
Product = the product element containing the package (must satisfy
`package_belongs_to_product` on raw segments). Operation keyed by **code** (`C43360` =
MANUFACTURE as observed); display-name case/whitespace variants ignored.
- **DIRECT (flagged):** product has `C43360` at DUNS `093132819`, and pre-event Rocky
  Mount identity evidence exists (SPL facility filing v5/v7 2013/2015; DECRS capture
  2022-10-14) — see `evidence/dst00/`.
- `RM_SECONDARY_ONLY`: only non-MANUFACTURE operations (ANALYSIS/PACK/LABEL/…) at
  `093132819` → not flagged.
- `OTHER_SITE`: `C43360` only at other DUNS → not flagged.
- `KIT_PART_ONLY`: `C43360` at Rocky Mount only for a kit part code → reported, not in N.
- `UNKNOWN_NO_ESTABLISHMENT` / `UNKNOWN_NO_MANUFACTURE_OP` / `UNKNOWN_UNSCOPED_OPERATION`
  → not flagged; reported as unknown (unknown ≠ absence).

## 5. Baselines on the identical frame
- **B1:** all frame packages.
- **B2 injectables:** product dosage form contains `INJECT` (case-insensitive), or any route
  display name in {INTRAVENOUS, INTRAMUSCULAR, SUBCUTANEOUS, INTRADERMAL, INTRATHECAL,
  EPIDURAL, INTRA-ARTERIAL, INTRA-ARTICULAR, INTRACARDIAC, INTRACAVERNOUS, INTRAOSSEOUS,
  INTRAPERITONEAL, INTRAVENTRICULAR, INTRAVITREAL, INTRALESIONAL, INFILTRATION, PERINEURAL,
  INTRACAMERAL, INTRASPINAL}. No form and no route → `UNCLASSIFIED` (not in B2, counted).
  Observed route/form vocabularies are reported in full.
- **B3:** NOT EVALUABLE by default. Becomes evaluable only if, *before unsealing*, a
  dated pre-cutoff shortage source with package-level (or exactly mappable) granularity
  is identified and documented here as an amendment.

## 6. Outcome seal and freeze
- The Pfizer July 21, 2023 appendix (`https://www.fda.gov/media/170647/download`) is
  **sealed**: no fineprint script fetches it until the **frame-freeze commit** exists,
  containing: set IDs, versions, ZIP SHA-256s, the package list, exclusions and all
  classifications, plus a SHA-256 of that manifest in the commit message.
- After unsealing: validate actual count P and dedup; normalize with the same function;
  report P, |P ∩ frame|, uncovered positives, and the metrics in
  `docs/spec/02_EVALUATION_AND_KILL_TEST.md`.

## 7. Disclosed contamination
Pfizer-list positives and examples were seen before this plan; the five DST-00 target
set IDs were chosen with that knowledge and are acquisition probes only. Nothing in
§1–§5 references outcome content. No researcher blinding is claimed.

## 8. DST-00 pilot permitted under this plan
Enumerate source A (set IDs + histories only) and count `0409` packages in source D.
No package-level frame is frozen in DST-00.

## Amendments
**A1 (2026-10-19, at reviewer request, committed before the run).** Investigate the
source-A (189 admissible set IDs) vs source-D (213 SPL document IDs) discrepancy:
1. For every set ID returned by source A, take the latest version with history
   `published_date` ≤ **2023-05-05** (the FDA generation date of the D snapshot), fetch that
   exact version, and record its document ID and its `0409` product/package NDCs.
2. Match each D document ID (`PRODUCTID` suffix) to those A document IDs. Each unmatched D document is then classified:
   - **(a) product-NDC present in A at a different version.** For these, the next admissible version is also fetched once.
   - **(b) product NDC absent from every A set.** Each such product NDC is looked up once in the DailyMed
     `spls.json?ndc=` search, and the set ID(s) it returns today are recorded.
3. A set IDs with no D document are reported by reason: no `0409` NDC, first published after the
   snapshot, or listed under another document.
This is a coverage diagnosis only. It freezes no frame, adds no package to any panel, and uses no outcome data.

**A2 (2026-10-19). Identity ≠ registration status.** The 2022-10-13 DECRS snapshot (archived
2022-10-14) establishes the DUNS ↔ FEI ↔ address identity of Rocky Mount and McPherson *as of
that record*. It does **not** establish that either establishment held a current registration
in 2023: the listed registrations expire 12/31/2022, and no pre-event 2023 registration record
has been found. Historical outputs must say "identity per the 2022 registration record", never
"registered in 2023".

**A4 (2026-10-20, DST-04A preparation; committed before the run).** Build a **draft, unfrozen**
candidate universe and measure its coverage. Nothing here classifies Rocky Mount links or
touches outcomes.
1. **Universe U** = source-A set IDs ∪ set IDs of the 213 source-D documents. Each D document is
   fetched **by document ID** from FDA's SPL repository
   (`accessdata.fda.gov/spl/data/<docid>/<docid>.xml`). That endpoint was verified byte-identical
   to DailyMed's version ZIP for DST-00 control acetylcysteine v19, SHA-256 `257d81d5…`.
2. **Cutoff version per set** = the latest version with DailyMed history `published_date`
   ≤ 2023-07-18, fetched via `getFile`; the served set/version must match. If a set has no
   DailyMed history, its D document stands as the latest evidence dated by the snapshot
   (≤ 2023-05-05), flagged `cutoff_version_unverified`.
3. **Packages.**
   - Every `0409` package in each cutoff document is listed with its 11-digit form (`to_11_digit` only)
     and its product (raw segment rule).
   - Exclusions are counted by reason: no package code, ambiguous format, marketing ended on or before the cutoff.
   - Each D package is checked for presence in its set's cutoff document; absences are reported as **unresolved mappings**.
4. **Coverage** is reported by source (A only / D only / both), cutoff versions retrieved / unverified / missing,
   D packages covered, and products whose cutoff document has any `MANUFACTURE` assertion (any site; no site
   classification).
5. Every fetched source goes into `evidence/historical/historical_source_manifest.json`.

The output is marked **DRAFT — NOT FROZEN**. The freeze (plan §6) happens only in DST-04B.

**A4.1 (2026-10-20, before the re-run).** The first A4 run stopped because `getFile` returned
HTTP 404 for a cutoff version that the history service lists. Such a set is now recorded as
`cutoff_version_not_retrievable`. The one exception: a document already retrieved by document ID
with the **identical set ID and version** is used, labelled `cutoff_version_by_document_id`. An older
or different version is never substituted.

**A3 (2026-10-19). B3 unavailable.** B3 ("already-short stays short") stays **NOT EVALUABLE**
until a dated, pre-cutoff shortage-state source with package-level (or exactly mappable)
granularity is identified and recorded here before unsealing. No substitute baseline will be used.
