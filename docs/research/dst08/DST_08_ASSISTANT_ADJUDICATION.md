# DST-08 independent adjudication — AI review, not human sign-off

**Date:** 2026-10-25  
**Branch:** `research/dst-08-source-ndc`  
**Status:** Advisory review only. The original `final_human_worksheet.csv` is unchanged; no human verdict, reviewer identity, or review date has been entered.

## Executive decision

**Recommended disposition remains NARROW, but the formal human gate is still OPEN.** This pass reviewed the committed label-derived evidence bundle, version-check summaries, registration audit, and the 52 worksheet questions. It is a second-pass AI adjudication, not a human audit. I could not freshly open the raw XML archive in `$FINEPRINT_DATA` from this session; the report therefore evaluates the extracted fields and recorded hashes/locations, not a fresh byte-level inspection of each raw label.

- **30 random links:** 30/30 are supportable *on the recorded current-label evidence*. This is not an official 30/30 human result. Seventeen of the 30 current source-label versions post-date the citing label, so the sample does not prove that each current site was named at the historical citing date.
- **Eight v2 acceptances:** all eight are supportable under the stated date-aware rule on the recorded historical-version fields; one (levocetirizine) retains a meaningful physical-description caveat because the current source imprint differs from the historical imprint.
- **Policy:** exclude all medical gases from SOURCE_LINKED; separately flag the product named Oxygen whose active ingredient is nitrous oxide; keep a repackager's own MANUFACTURE assertion separate from its source link.
- **Ten DIRECT review cases:** the evidence shows 26 label MANUFACTURE edges conflicting with the available registration operations, across 21 products. Preserve the frozen baseline in DST-08, but do not present these as registration-verified manufacturing without an explicit conflict status and a separate DIRECT-policy decision.

## Scope and interpretation

The source-linked relationship is upstream provenance evidence: a citing label points to a source NDC, and the cited source product's own current label lists one or more product-scoped MANUFACTURE sites. It does **not** identify which site made the lots received by the repackager. A safe UI phrase is:

> The cited source product's current label lists N registered MANUFACTURE site(s). The source-NDC reference does not identify the site used for the repackaged lots.

Avoid wording such as “this product was made at one of N sites” unless the product/lot-specific relationship is independently established.

## A. Random precision sample — 30 items

All 30 recorded checks show a unique canonical source product in another set, matching form and active ingredient/strength, a product-scoped source MANUFACTURE statement, a current DIRECT site edge, and no failed mechanical checks. The provisional dispositions below are therefore supportable against the evidence bundle. “Source label later” is a temporal limitation, not by itself a false-link finding under the current-source-label interpretation.

| Worksheet item | Citing product (NDC) | Source NDC | Current source sites | Source label later than citing? | AI second-pass disposition |
|---|---|---|---:|---|---|
| P-R9-01 | Meclizine Hydrochloride (60760-661) | 16571-661 | 1 | No | Supportable on recorded evidence |
| P-R9-02 | Pindolol (82804-940) | 69367-422 | 1 | No | Supportable on recorded evidence |
| P-R9-03 | Oseltamivir phosphate (68788-8123) | 27241-139 | 1 | Yes | Supportable with temporal caveat |
| P-R9-04 | Levetiracetam (68788-7592) | 65862-246 | 2 | Yes | Supportable with temporal caveat |
| P-R9-05 | Lorazepam (33358-221) | 63304-774 | 1 | Yes | Supportable with temporal caveat |
| P-R9-06 | Lidocaine (80425-0248) | 16714-878 | 1 | Yes | Supportable with temporal caveat |
| P-R9-07 | Desvenlafaxine (63629-7525) | 51991-311 | 1 | No | Supportable on recorded evidence |
| P-R9-08 | hydrocodone bitartrate and acetaminophen (63629-1183) | 71930-044 | 1 | No | Supportable on recorded evidence |
| P-R9-09 | Hydroxychloroquine Sulfate (67046-1523) | 83980-001 | 3 | No | Supportable on recorded evidence |
| P-R9-10 | Pravastatin Sodium (70934-832) | 68462-197 | 3 | Yes | Supportable with temporal caveat |
| P-R9-11 | AZITHROMYCIN (50090-6296) | 42806-149 | 1 | No | Supportable on recorded evidence |
| P-R9-12 | Amlodipine Besylate and Benazepril Hydrochloride (70518-4388) | 55111-587 | 1 | No | Supportable on recorded evidence |
| P-R9-13 | Phenobarbital Sodium (72162-1329) | 42494-415 | 1 | Yes | Supportable with temporal caveat |
| P-R9-14 | LOSARTAN POTASSIUM25 mg (71205-675) | 64380-933 | 1 | Yes | Supportable with temporal caveat |
| P-R9-15 | DIAZEPAM (68071-3682) | 59651-653 | 1 | No | Supportable on recorded evidence |
| P-R9-16 | temazepam (63629-8604) | 67877-149 | 1 | Yes | Supportable with temporal caveat |
| P-R9-17 | Imipramine Hydrochloride (72789-244) | 69584-427 | 1 | No | Supportable on recorded evidence |
| P-R9-18 | Cephalexin (68071-3532) | 65862-019 | 1 | Yes | Supportable with temporal caveat |
| P-R9-19 | Quetiapine fumarate (64725-0148) | 16729-148 | 2 | Yes | Supportable with temporal caveat |
| P-R9-20 | PANTOPRAZOLE SODIUM D/R (61919-700) | 13668-429 | 2 | Yes | Supportable with temporal caveat |
| P-R9-21 | Nifedipine (72162-2536) | 59651-297 | 1 | No | Supportable on recorded evidence |
| P-R9-22 | Ondansetron Hydrochloride (33261-417) | 65862-187 | 1 | Yes | Supportable with temporal caveat |
| P-R9-23 | Budesonide (50090-6586) | 47335-632 | 1 | Yes | Supportable with temporal caveat |
| P-R9-24 | Allopurinol (60760-710) | 69315-291 | 1 | No | Supportable on recorded evidence |
| P-R9-25 | Venlafaxine Hydrochloride (51655-849) | 65862-528 | 1 | No | Supportable on recorded evidence |
| P-R9-26 | Indomethacin (71205-822) | 31722-565 | 1 | Yes | Supportable with temporal caveat |
| P-R9-27 | Celecoxib (45865-943) | 62332-142 | 2 | Yes | Supportable with temporal caveat |
| P-R9-28 | AMOXICILLIN AND CLAVULANATE POTASSIUM (72162-2435) | 42571-160 | 1 | Yes | Supportable with temporal caveat |
| P-R9-29 | Ondansetron (85534-0025) | 65862-390 | 1 | No | Supportable on recorded evidence |
| P-R9-30 | Sumatriptan (68071-3802) | 16714-797 | 1 | Yes | Supportable with temporal caveat |

**Sample finding:** The 30 recorded rows support the source-link semantics, but they do not establish historical site continuity for the 17 cases whose current source label post-dates the citing label. That limitation must remain visible and must not be converted into historical or lot-specific site attribution.

## B. Eight v2 version-check acceptances

| Worksheet item | Citing product / source NDC | Applicable source version | Recorded comparison | Sites named at applicable version and still current | AI second-pass disposition |
|---|---|---|---|---|---|
| V-MULTIPLE_VALID_PRESENTATIONS_sites_conti-1 | Carbamazepine chewable 100 mg / 13668-271 | v7 (2013-05-09) | imprint=SAME; color=SAME; shape=SAME; size=SAME; score=SAME; flavor=ONE_OF_SEVERAL | 916488547 | Supportable under v2; original labels still need human sign-off. |
| V-MULTIPLE_VALID_PRESENTATIONS_sites_conti-2 | Oseltamivir 75 mg capsule / 31722-632 | v1 (2018-03-09) | imprint=SAME; color=ONE_OF_SEVERAL; shape=SAME; size=SAME; score=SAME | 676162024 | Supportable under v2; original labels still need human sign-off. |
| V-NOTATION_ONLY_sites_continue-1 | Clindamycin 150 mg capsule / 63304-692 | v14 (2022-07-06) | imprint=SAME; color=SAME; shape=SAME; size=SAME; score=SAME | 051565745, 725959238 | Supportable under v2; original labels still need human sign-off. |
| V-NOTATION_ONLY_sites_continue-2 | Clindamycin 300 mg capsule / 63304-693 | v14 (2022-07-06) | imprint=SAME; color=SAME; shape=SAME; size=SAME; score=SAME | 051565745, 725959238 | Supportable under v2; original labels still need human sign-off. |
| V-NOTATION_ONLY_sites_continue-3 | Clomipramine 25 mg capsule / 51672-4011 | v7 (2019-10-29) | imprint=SAME; color=SAME; shape=SAME; size=SAME; score=SAME | 600072078 | Supportable under v2; original labels still need human sign-off. |
| V-VERSION_DRIFT_RESOLVED_sites_continue-1 | Hydroxyzine 25 mg tablet / 42806-160 | v9 (2019-04-23) | imprint=SAME; color=SAME; shape=SAME; size=SAME; score=SAME | 827915443 | Supportable under v2; original labels still need human sign-off. |
| V-VERSION_DRIFT_RESOLVED_sites_continue-2 | Levocetirizine 5 mg tablet / 33342-200 | v8 (2019-04-16) | imprint=SAME; color=SAME; shape=SAME; size=SAME; score=SAME | 676369519 | Supportable for the relevant date; retain caveat that current imprint differs from historical ML17. |
| V-VERSION_DRIFT_RESOLVED_sites_continue-3 | Oxycodone/acetaminophen 10/325 mg tablet / 71930-047 | v5 (2022-12-13) | imprint=SAME; color=SAME; shape=SAME; size=SAME; score=SAME | 078706898 | Supportable under v2; original labels still need human sign-off. |

### Version-check interpretation

- The two multiple-presentation cases are supported because the applicable source version records two valid values and the citing value is one of them; only sites actually named in that applicable version are retained.
- The three notation cases preserve the same imprint marks despite a different textual representation (for example, a repeated imprint on both sides); the named sites continue in the current source label and current registration records.
- Hydroxyzine: the citing imprint `E160` matches applicable source v9, while the current source version says `160`; the named site continues.
- Levocetirizine: the citing imprint `ML17` matches applicable source v8, while the current source version says `M;17`. The record supports the link at the relevant date and site continuity, but label history alone does not tell us whether the tablet changed or the description was corrected. Do not describe the historical and current physical descriptions as identical.
- Oxycodone/acetaminophen: the citing `WES203` matches applicable source v5; the current label adds strength notation, and the named site continues.

## C. Four policy cases

| Worksheet item | AI second-pass disposition | Reason / handling |
|---|---|---|
| W-R1-07 — refrigerated liquid oxygen; source lists 180+ Airgas sites | **Exclude from SOURCE_LINKED** | Medical gases are exempt from source-NDC requirements; the source's many sites add little useful product-specific provenance. The citing product remains in its existing DIRECT tier as a filling-site claim; do not reinterpret it as the gas producer. |
| M-5_or_more_DIRECT_source_sites-1 — Oxygen 99%; 29 Air Products sites | **Exclude from SOURCE_LINKED** | Same policy for medical gases. Do not present the source NDC as evidence that the repackaged lots came from any specific one of the 29 sites. |
| M-5_or_more_DIRECT_source_sites-2 — product named “Oxygen”, active ingredient nitrous oxide | **Exclude and flag data-quality conflict** | The ingredient/form match the cited nitrous oxide product, but the product name contradicts the active ingredient. Do not let source matching silently resolve or normalize this contradiction. |
| W-R1-09 — naproxen; citing establishment also claims MANUFACTURE | **Keep source link separate; flag own MANUFACTURE claim** | The recorded source match is supported, but the source link does not validate the citing establishment's own manufacturing claim. Display the claims as separate evidence types. |

## D. Ten DIRECT registration-conflict cases

These are existing label assertions, not DST-08 source-linked additions. The registration audit reports 26 conflicting edges across 21 products; the ten worksheet rows are establishment-level review representatives. Recommendation: do not silently alter the frozen DIRECT baseline inside DST-08, but do not represent these edges as registration-verified. Preserve the label claim and attach a visible `REGISTRATION_CONFLICT`/equivalent status pending a separate DIRECT-policy decision. If the explorer cannot distinguish that status, do not show these as unqualified verified manufacturing.

| Worksheet item | Establishment | Conflicting edges in audit | Label assertion vs. registration | AI second-pass disposition |
|---|---|---:|---|---|
| DIRECT-26308 | Meridian Medical Technologies (049504624) | 8 | Label operation(s) C25391;C43360;C84382;C84731;C84732; registered operation(s): ANALYSIS; LABEL; PACK (LABEL/PACK only) | Preserve frozen assertion with visible registration-conflict flag; do not call independently verified. |
| DIRECT-10839 | Solara Active Pharma Sciences (915786829) | 6 | Label operation(s) C43360; registered operation(s): ANALYSIS; API MANUFACTURE (API MANUFACTURE only) | Preserve frozen assertion with visible registration-conflict flag; do not call independently verified. |
| DIRECT-11955 | Dynamit Nobel (313113144) | 1 | Label operation(s) C43360;C82401; registered operation(s): ANALYSIS; API MANUFACTURE (API MANUFACTURE only) | Preserve frozen assertion with visible registration-conflict flag; do not call independently verified. |
| DIRECT-13674 | Granules (918457644) | 3 | Label operation(s) C43360; registered operation(s): ANALYSIS; API MANUFACTURE; LABEL; PACK (API MANUFACTURE plus label/pack) | Preserve frozen assertion with visible registration-conflict flag; do not call independently verified. |
| DIRECT-14021 | Lacsa (636596397) | 1 | Label operation(s) C43360; registered operation(s): API MANUFACTURE (API MANUFACTURE only) | Preserve frozen assertion with visible registration-conflict flag; do not call independently verified. |
| DIRECT-21953 | Patheon Austria (300398976) | 1 | Label operation(s) C43360; registered operation(s): ANALYSIS; API MANUFACTURE (API MANUFACTURE only) | Preserve frozen assertion with visible registration-conflict flag; do not call independently verified. |
| DIRECT-8736 | Apotex (243805095) | 1 | Label operation(s) C43360; registered operation(s): PACK (LABEL/PACK only) | Preserve frozen assertion with visible registration-conflict flag; do not call independently verified. |
| DIRECT-10838 | Actavis (017665256) | 2 | Label operation(s) C43360; registered operation(s): LABEL; PACK (LABEL/PACK only) | Preserve frozen assertion with visible registration-conflict flag; do not call independently verified. |
| DIRECT-13769 | Focus Health Group (826939949) | 2 | Label operation(s) C43360; registered operation(s): LABEL (LABEL/PACK only) | Preserve frozen assertion with visible registration-conflict flag; do not call independently verified. |
| DIRECT-18338 | Blessings International (064965742) | 1 | Label operation(s) C43360; registered operation(s): RELABEL; REPACK (REPACK/RELABEL only) | Preserve frozen assertion with visible registration-conflict flag; do not call independently verified. |

### Why not silently remove them here?

The audit is establishment-level and covers four snapshots beginning 2024-12-23; it is strong contrary evidence but not a complete historical or product/lot adjudication. Removing the 26 edges would change the released DIRECT graph and is outside this source-link tier's scope. A separate decision should define whether DIRECT means a label's explicit MANUFACTURE assertion or a registration-validated manufacturing site. Until that is decided, a conflict status is more truthful than either silently deleting the label claim or presenting it as verified.

## Final recommendation and gate status

1. Keep `dst08-lineage-v2` only; exclude all medical gases; keep SOURCE_LINKED distinct from DIRECT and out of the 2023 historical evaluation.
2. Use wording that explicitly says the current source label lists the site(s), without implying lot-level or historical site attribution.
3. Keep the original 52-item worksheet's human columns blank. This report is not a substitute for a human reading/sign-off of the cited source XML and registration evidence.
4. **Do not mark DST-08 as human-gate passed yet.** The evidence bundle looks supportable under the proposed narrow policy, but the formal 29/30 and 8/8 criteria require a person to verify the original labels and enter the actual human verdicts.
5. If the person reviewing the raw labels fails either numeric criterion, reject the SOURCE_LINKED addition rather than expanding the rule set.

## Source files reviewed

- [Final validation report](DST_08_FINAL_VALIDATION.md)
- [Human worksheet — left unchanged](final_human_worksheet.csv)
- [Version-aware rule design](SOURCE_NDC_V2_DESIGN.md)
- [Re-derived case evidence](final_cases_evidence.json)
- [AI validation table](final_ai_validation.csv)
- [Frozen random-sample checks](sample_checks.json)
- [Random-sample AI reading](sample_ai_review.csv)
- [Registration operations audit](registration_operations_audit.csv)
