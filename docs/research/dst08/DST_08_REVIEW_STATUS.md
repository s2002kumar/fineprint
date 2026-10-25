# DST-08 review status

**As of:** 2026-10-25  
**Branch:** `research/dst-08-source-ndc`  
**Disposition:** **NARROW — research evidence is supportable; formal human gate remains OPEN.**  
**Release state:** not merged, deployed, or tagged. Production data and the historical Rocky Mount evaluation remain untouched.

## Executive result

The source-NDC pilot has a reproducible evidence bundle, a version-aware rule, an item-by-item AI-assisted adjudication, direct links to the exact cited label versions, and automated tests for the review artifacts. The CI run for commit `abb3fae84d8ce1296e9e6fe552a82e4b10cbc408` passed on Python 3.11, Python 3.14, and PostgreSQL 18 (workflow run 25).

This is **not** a claim that the formal human acceptance criteria have passed. The original human worksheet remains intentionally blank, and this branch must not be merged or used in production until a person completes that gate.

## What the evidence bundle currently supports

| Check | Recorded result | Interpretation |
|---|---:|---|
| Frozen R9 random sample | 30/30 mechanically eligible; 0 failed checks | Every row has one canonical source candidate, matching form and active ingredient/strength, a product-scoped MANUFACTURE statement, and recorded current DIRECT evidence. |
| AI second-pass reading of R9 | 30/30 `LINK_SUPPORTED` | Supported by the committed extracted evidence; **not** the official human 29/30 result. |
| Source label later than citing label | 17/30 R9 cases | Preserve the temporal caveat. A current source label does not prove which site was listed when the citing label was published or which site made a particular lot. |
| Version-aware acceptances | 8/8 reproduced in the committed evidence | 3 `VERSION_DRIFT_RESOLVED`, 3 `NOTATION_ONLY`, 2 `MULTIPLE_VALID_PRESENTATIONS`; all have a recorded continuing site. This is not the official human 8/8 result. |
| Policy cases | 4 dispositions documented | Exclude medical gases from SOURCE_LINKED; separately flag the “Oxygen”/nitrous-oxide name/ingredient conflict; keep a repackager's own MANUFACTURE claim distinct from its source-NDC relationship. |
| DIRECT registration conflicts | 10 establishment-level cases | The audit identifies 26 label MANUFACTURE edges conflicting with available registration operations across 21 products. DST-08 does not silently rewrite the frozen DIRECT baseline; the conflicts must not be presented as registration-verified. |

## Acceptance gate — still required

The frozen validation report requires a person to review the original source evidence and enter the real verdicts:

- **At least 29/30** random R9 cases.
- **All 8/8** version-aware acceptance cases.
- Explicit decisions on the 4 policy cases and 10 DIRECT registration-conflict representatives.

Do not populate reviewer names, review dates, or human verdict fields on behalf of someone else. The automated artifact test verifies that the worksheet has 52 unique items and that all human fields remain blank; it also checks the frozen R9 cases against the sample manifest and re-derived evidence, and checks the eight accepted version cases for reproduced site continuity.

If the human threshold fails, the pre-registered decision is **REJECT** for the SOURCE_LINKED addition, not a relaxed rule. If it passes, review the display semantics and conflicts before any release. No production graph, explorer, benchmark, migration, or tag is changed by this research branch.

## Review materials

- [Final validation and decision](../../../DST_08_FINAL_VALIDATION.md)
- [First source-NDC review gate](../../../DST_08_SOURCE_NDC_REVIEW.md)
- [AI-assisted independent adjudication (not human sign-off)](DST_08_ASSISTANT_ADJUDICATION.md)
- [Human review runbook with exact-version source links](DST_08_HUMAN_REVIEW_RUNBOOK.md)
- [Original 52-item human worksheet (blank until actual review)](final_human_worksheet.csv)
- [Frozen random-sample manifest](sample_manifest.json)
- [Re-derived mechanical sample checks](sample_checks.json)
- [Random-sample AI readings](sample_ai_review.csv)
- [Re-derived version/policy/DIRECT case evidence](final_cases_evidence.json)
- [Registration operations audit](registration_operations_audit.csv)

## Interpretation boundary

A SOURCE_LINKED relationship is upstream evidence: the citing label names a source product, and that source product's label lists registered manufacturing site(s). It does not identify the facility used for any particular repackaged lot. Keep SOURCE_LINKED separate from DIRECT, do not include it in the historical 2023 evaluation, and exclude medical gases from this tier.
