# DST-08 source-NDC lineage pilot: review gate

Research branch `research/dst-08-source-ndc`, 2026-10-25, stacked on `research/accuracy-coverage-2026-10` (`473ffc2`,
draft PR #2, open and not merged).

Nothing in production changed: the database `fineprint`, the released graph, `site/data/`, the frozen Rocky Mount
benchmark, `dst04b-freeze`, `docs/human_audit_verdicts.csv` and every tag are untouched. The prototype ran only in the
scratch database `fineprint_dst08`, a template copy of `fineprint`: graph build 8, DailyMed release 2026-10-16, FDA
registration files as of 2026-10-19. Nothing was merged, deployed or tagged.

**All sample verification here is AI-assisted. No person has yet adjudicated any source-NDC relationship.**

## 1. Recommendation: NARROW

**GO (research).** A separate `SOURCE_LINKED` tier is supported, built as in this pilot: one validated source-NDC
reference, resolved by exact product code to one canonical source product, consistent in form and active
ingredients, single hop, ending at the source's own DIRECT MANUFACTURE edge, with every step stored and re-readable.
- The rule finds what it should. In the frozen sample, 42 of 42 eligible links were supported by the raw XML (Wilson
  95% interval 91.6–100%), and every exclusion was correct or conservative.
- **It needs one more condition before any use: physical characteristics.** A post-hoc check over all 19,668 eligible
  references found 373 (1.9%) where the citing and source labels state a different imprint, colour, shape, size, score
  or flavour. 131 of them have clearly different imprints, for example `IG;209` against `D;74`, or `GG931` against `NL4`.
  - 352 of the 373 are old repackager labels citing a source label published later. The current source label then
    describes a different physical product, so its manufacturing site may not be where the repackaged lots were made.
  - The sample (0 of 42) was too small to see a problem this rare.
  - Under the brief's stop condition these 373 links are **stopped**: not counted as validated, and not in the usable
    figure below. The Implementation Guide already requires these characteristics to match (3.2.2.4–3.2.2.9). A rule
    `v2` should add the check.
- **Before any release:**
  - a person completes the worksheet (section 10);
  - the explorer labels the tier "upstream evidence about the cited source product" and shows the number of source sites
    next to it;
  - SOURCE_LINKED never enters the DIRECT count.

**NO-GO:**
- calling the combined figure verified site coverage;
- using source links in the historical 2023 evaluation;
- following multi-hop chains;
- truncating package codes;
- choosing among several candidate sources;
- any name, company or address matching;
- release before human review.

| Products (80,508) | Count | Share |
|---|---|---|
| DIRECT (unchanged) | 24,614 | 30.6% |
| SOURCE_LINKED under rule v1, as pre-registered | 19,612 | 24.4% |
| SOURCE_LINKED without the 373 characteristic conflicts (usable figure) | 19,239 | 23.9% |
| DIRECT or SOURCE_LINKED, v1 / without conflicts | 44,226 / 43,853 | 54.9% / 54.5% |

**Neither combined figure is independently verified site coverage, and the earlier 55.9% must not be described as
such.** What a source-linked product carries is this: the product it cites is, in that product's own current label,
made at one of N registered sites. That says nothing about which site made this repackager's lots, or about how the
source was listed when the repackager bought it. For 23.6% of source-linked products N is 2 or more.

## 2. What a source NDC is (Phase 2)

Full note, with sources, retrieval date and SHA-256 hashes: `docs/research/dst08/SOURCE_NDC_DESIGN.md`. It was committed
in `8a2d0fd`, before the sample was drawn.

- **21 CFR 207.53(b).** A repacker or relabeler lists "the NDC assigned to each finished drug received by the registrant
  for repacking or relabeling, with the exception of medical gases", associated with its own NDCs. No manufacturer, lot,
  date or version is named.
- **SPL encoding** (Implementation Guide v1, December 2023, 3.1.2 and 3.2.2). The element is `asEquivalentEntity`, with
  class `EQUIV`, equivalence code C64637 ("Same") and the source NDC *product* code in `definingMaterialKind`. It sits
  under a product or a kit part.
  - At submission FDA checks that the code is another set's product code, not the product's own, and one per product.
  - It also checks that active ingredients and strengths, dosage form, size, shape, colour, imprint, flavour and scoring
    equal the source's.
  - These checks run once. They are not repeated when the source label changes.
- **21 CFR 207.1** defines "manufacture" separately from repack and relabel for listing purposes. It also counts
  contract packers and contract labelers as manufacturers, and section 510 of the Act treats repackaging as
  manufacturing. That is why no repackager MANUFACTURE assertion is called false in section 5.

| Relationship | Stored in | Meaning |
|---|---|---|
| `DIRECT_MANUFACTURE` | `national.operation_edge`, unchanged | the product's own label names a registered MANUFACTURE site for it |
| `SOURCE_NDC_REFERENCE` | `lineage.source_reference` | the repackager states it received the finished drug under that product code |
| `SOURCE_LINKED_MANUFACTURING_EVIDENCE` | `lineage.source_linked_evidence` | an eligible reference composed with the source's own DIRECT edge; both endpoints and every step kept |

## 3. Frozen sample and independent checks (Phase 3)

- **Inventory** (`scripts/research/dst08_source_inventory.py`, its own XML walk with no parser imports):
  - 36,457 `asEquivalentEntity` elements in the 52,747 canonical labels, every one with C64637 in the NCI system;
  - 36,354 on top-level products and 103 on kit parts;
  - one per product, no element outside a product, and no product without a database row.
- **Sample** (`dst08_sample.py`):
  - 96 references in 10 strata, seed `fineprint-dst08-source-ndc-2026-10-25`;
  - drawn from the inventory (SHA-256 `4ca5f526…`) and committed in `43b3c5b` *before* any check ran;
  - sizes set from stratum counts alone.

  | Stratum | References | Sampled |
  |---|---|---|
  | R1 repackager claims MANUFACTURE | 10 | 10 |
  | R2 kit or kit part | 308 | 6 |
  | R3 package code | 109 | 6 |
  | R4 other invalid | 11 | 6 |
  | R5 multi-hop or conflict | 1,239 | 10 |
  | R6 multiple candidates | 347 | 6 |
  | R7 no matching source | 5,595 | 6 |
  | R8 multiple label versions | 3,446 | 10 |
  | R9 resolves to DIRECT | 17,261 | 30 |
  | R10 resolves, not DIRECT | 8,131 | 6 |

- **Checks** (`dst08_check_sample.py` → `sample_checks.json`, `sample_checks_digest.md`). For each sampled reference,
  the script:
  - re-reads the citing XML, hash-verified, and quotes the element verbatim;
  - re-resolves the code over every product row, canonical or not;
  - opens each candidate's XML and compares dosage form and active ingredients;
  - reads the candidate's MANUFACTURE performances scoped to the code, and the graph edges with their registration line;
  - lists every version of the source set in the release, with the sites each version names;
  - records publication dates and the next hop.
- **AI-assisted review** (`sample_ai_review.csv`). It is kept separate from the blank `human_review_worksheet.csv`, and
  every row says it is not a human adjudication.

| Verdict | n | Meaning |
|---|---|---|
| LINK_SUPPORTED | 41 | eligible; the raw XML supports the source identity and the source's MANUFACTURE statement |
| EXCLUDED_BY_DEFECT_FIXED | 1 | excluded in the inventory only by the strength-spelling defect (section 8); eligible and supported in the prototype |
| CORRECTLY_EXCLUDED | 44 | excluded, and the stated reason is confirmed in the raw XML |
| EXCLUDED_PLAUSIBLE_LINK | 10 | excluded by a rule, though the link would probably be right: more specific form on one side (3), candidate sets that agree (3), two-hop chains (3), a package code with one prefix match (1) |
| FALSE or UNSAFE LINK | 0 | none in the sample; see the population check in section 8 |

R9 alone: 30 of 30 supported (95% interval 88.6–100%). For all 42 eligible sample links, every version of the source set
in the release names the same MANUFACTURE sites. In 25 of the 41 supported links, the current source label is newer
than the citing label. Product names agree in every eligible case. Names were read only as a cross-check; no rule uses
them, and no link was inferred from similarity, company names or addresses.

## 4. The prototype (Phase 4)

Code:
- `src/fineprint/lineage.py` (rule `dst08-lineage-v1`);
- the schema, `scripts/research/dst08_lineage.sql`;
- the runner, `scripts/research/dst08_build_lineage.py`;
- the chain query, `scripts/research/dst08_evidence_chain.py`.

It is not wired into ingest, the CLI, the explorer export or the historical evaluation. `lineage.build` refuses any
database not named `fineprint_dst08*` or `*_test`.

- **DIRECT is preserved.** The national ingest fingerprints, every `operation_edge` row and every product status are
  hashed before and after each build: all unchanged. The scratch copy equalled production beforehand.
- **Auditable relationships.** One row per source reference, holding the citing document, the element location, the
  verbatim code and code system, and its validity. Resolution, chain, consistency, status and *every* exclusion reason
  sit beside it.
- **Exact normalisation.** Codes go through `fineprint.ndc` only. A package code stays a package code and is never
  truncated.
  - Strengths compare as exact decimals: `.25` equals `0.25`, but 7.70 mg per 100 mL does not equal 7.7 mg per 1 mL.
- **Limited traversal.** One validated reference, then the source's DIRECT MANUFACTURE edge. Everything else is recorded
  and excluded with its reasons: cycles, multi-hop chains, chains ending at an unresolved reference, several candidates,
  kit parts, an ambiguous source version, and form or strength conflicts.
- **Separate provenance.** The repackager SPL, the source SPL and the FDA registration line each keep their release
  part, member and hashes.
- **No substitution.** The citing and source versions are each the canonical version of the same release, and both are
  recorded. Nothing newer replaces older evidence.
- **Correctness.**
  - Compared reference by reference with the independent inventory, all 36,457 references match on validity,
    resolution, resolved source set and chain. The differences are explained and either conservative or the fixed
    defect:
    - 58 strength-spelling conflicts become consistent;
    - 149 kit or no-ingredient cases become `INCOMPLETE` instead of consistent;
    - 5 eleven-digit codes become malformed instead of package codes, excluded either way.
  - The prototype matches the mechanical checks on 95 of 96 sample rows; the one difference is R5-10, the fixed defect.
- **Reproducibility.** Six builds produced identical fingerprints over all three lineage tables (36,457 / 36,457 /
  26,866 rows). Two ran before the read fix, two on a dirty tree, and the final two from the clean commit `c8ded0f`
  (`lineage_build.json`, `code_dirty: false`).
  - source_reference `6e73b8a6…`, source_resolution `304e344e…`, source_linked_evidence `96e121a6…`.
- **Performance** (laptop, 15 GB RAM, under memory pressure):
  - a build takes 305–383 s, almost all of it reading and hashing 52,747 XML files; the eleven resolution statements
    take about 11 s together;
  - one product's evidence chain takes 5.7 ms in SQL, or 0.23 s with both cited XML elements re-read and hash-verified;
  - the coverage aggregate over 80,508 products takes 0.7 s.
  - The first builds took 62–70 minutes because each document reopened its multi-gigabyte release part; that is fixed.
- **Tests.** `tests/test_source_lineage.py` has 15 tests on a synthetic release with one scenario per rule:
  - consistent DIRECT source; no candidate; several candidates; package code; multi-hop chain; cycle;
  - form conflict; strength conflict; an equal ratio with a different denominator (still a conflict); the same strength
    spelled differently (consistent);
  - repackager claiming MANUFACTURE (stays DIRECT); kit part; source without DIRECT; non-canonical-only match; wrong
    equivalence code; two sources on one product; self reference;
  - the national tables are unchanged, a rebuild is identical, and the SQL rule equals the Python rule on every row;
  - the evidence chain carries both verbatim elements and the registration line, and the production database is
    refused.

  **Full PostgreSQL-backed suite: 113 tests, OK, none skipped** (`python -I -m unittest discover -s tests -t .`).

## 5. Repackager MANUFACTURE audit (Phase 5)

`scripts/research/dst08_repackager_audit.py` writes `repackager_manufacture_audit.json` and `.csv`.

**Population:** every product-scoped MANUFACTURE edge whose establishment also lists REPACK or RELABEL for the same
product in the same label. That is 139 products, 139 edges, 15 establishments and 19 DIRECT edges.

Each assertion was re-read from the release and set against two independent facts:
- FDA's registration record for the DUNS, which lists its registered business operations;
- where the product has one, its source NDC: is the claimed DUNS one of the resolved source's own MANUFACTURE sites?

Label statements ("Manufactured by", "Manufactured for", "Distributed by") were extracted as text for the reviewer.

| Establishment (DUNS) | Products | Edge | Registered operations | Evidence | AI-assisted judgment |
|---|---|---|---|---|---|
| Hetero Labs Unit III (676162024) | 7 | DIRECT | MANUFACTURE | makes 180 other products; text "By: Hetero Labs" | correct |
| Inventia Healthcare (677604412) | 5 | DIRECT | ANALYSIS; LABEL; MANUFACTURE; PACK | makes 57 other products for 14 labelers | correct |
| Appco Pharma (078510186) | 2 | DIRECT | includes MANUFACTURE and REPACK | text "Manufactured By: Appco Pharma" | correct |
| Jerome Stevens (021130638) | 2 | DIRECT | includes MANUFACTURE | text "Manufactured by: Jerome Stevens" | correct |
| The Ritedose Corp. (837769546) | 1 | DIRECT | includes MANUFACTURE | it is the cited source product's own MANUFACTURE site | correct |
| Focus Medical Gases (084462152) | 1 | DIRECT | MANUFACTURE; REPACK | medical oxygen | correct |
| ProCare (025798900) | 1 | DIRECT | TRANSFILL only | oxygen; its source names other sites | **ambiguous, high risk**: the registration says transfiller and the label says manufacture. Transfilling is a manufacturing operation for gases under CGMP, so this is not demonstrably false |
| H.J. Harkins (147681894) | 103 | TENTATIVE | MANUFACTURE; RELABEL; REPACK (archived) | own labels. 102 cite no source NDC although IG 3.2.2.11 requires one. One cites Glenmark's naproxen, whose label names a different site | **potentially erroneous as physical manufacture**; legally ambiguous (contract packer) |
| All Pharma (078572520) | 7 | UNKNOWN | not registered | every product cites another labeler's source NDC | **potentially erroneous** |
| California Pharmaceuticals (021420944) | 5 | UNKNOWN | not registered | compounding-type products; no source cited | ambiguous |
| TMIG (036572986), Snap Medical (036735821) | 1 + 1 | UNKNOWN | not registered | kits of other firms' products | ambiguous (kit assembly can be manufacture) |
| Laboratoire Aguettant (271085545), International Vitamin Corp. (964464114), Teligent (011036910) | 1 + 1 + 1 | UNKNOWN | not in the US registration file | the text names the same firm as maker | ambiguous; probably correct, unverifiable here |

**Mechanical classes, for the record:**
- 119 `REGISTRATION_ONLY`: the registration lists MANUFACTURE, an establishment-level fact;
- 1 `CORROBORATED_BY_SOURCE` (Ritedose);
- 2 `POTENTIALLY_ERRONEOUS` (ProCare and one All Pharma product);
- 17 `AMBIGUOUS`.

Not all repackager MANUFACTURE assertions are false. Of the 19 DIRECT edges, 18 belong to registered manufacturers that
also pack or relabel.

**The three labeler-as-manufacturer contradictions** from the coverage sample:
- **S098 (EPI Health):** the labeler lists itself as the only MANUFACTURE establishment, while the text says
  "Manufactured by: Dr. Reddy's … for EPI Health". Potentially erroneous structured assertion.
- **S104 (Xspire):** the labeler lists itself as the only MANUFACTURE establishment, while the text says "Manufactured
  for: Xspire". Potentially erroneous structured assertion.
  - Both are UNKNOWN_SITE because the DUNS is unregistered, so the DIRECT tier is not affected.
- **S077 (ICU Medical):** no MANUFACTURE edge for the product itself (the Rocky Mount site is scoped to sibling sizes),
  and the text says both "Manufactured by" and "Manufactured for" ICU Medical. Ambiguous; NO_MANUFACTURE_EVIDENCE is the
  right status.

**Defects demonstrated in the graph or parser: none.** Every audited edge is what its label says, classified by the
documented rule, so no graph regression test is warranted. The lineage-side behaviour — a repackager's own MANUFACTURE
stays DIRECT whatever it cites — is covered by `test_a_repackager_claiming_manufacture_stays_direct_and_its_reference_stays_separate`.

**One rule question for a person, not applied anywhere.** 60 of the 30,015 DIRECT MANUFACTURE edges (32 DUNS) come from
establishments whose registration lists operations without MANUFACTURE: TRANSFILL 10, REPACK 8, label- or pack-only,
API-only, PET production. A future DIRECT rule could cross-check registered operations, but that changes the released
graph's rules and needs its own decision.

## 6. Counts (Phase 6)

From `docs/research/dst08/report_counts.json` (`dst08_report_counts.py`), lineage build at `c8ded0f`.

| Measure | Count |
|---|---|
| Source-NDC references (each on a different product or kit part) | 36,457 |
| — on top-level products: NO_MANUFACTURE_EVIDENCE / DIRECT / UNKNOWN_SITE / TENTATIVE | 36,259 / 76 / 15 / 4 |
| — on kit parts (recorded, never coverage) | 103 |
| Valid references resolved to exactly one canonical source product (unique citing–source pairs) | 30,283 |
| — distinct source products | 9,086 |
| Eligible references (rule v1) | 19,668 |
| — on products already DIRECT (DIRECT kept) | 56 |
| — distinct source products | 5,607 |
| Products reaching SOURCE_LINKED | 19,612 (19,607 from NO_MANUFACTURE_EVIDENCE, 3 UNKNOWN_SITE, 2 TENTATIVE) |
| — distinct source products / distinct DIRECT source sites (DUNS) / evidence rows | 5,593 / 787 / 26,133 |
| — with 1 / 2 / 3 / 4 / 5 or more source sites | 14,979 / 3,285 / 1,256 / 81 / 11 (up to 213, medical gases) |
| Eligible references whose source label is newer than the citing label | 10,419 (53.0%); 317 lack a date |
| Eligible references with a characteristic conflict (post-hoc; stopped) | 373 (179 imprint, 190 other with imprint equal, 4 other) |

Excluded references, by first reason (16,789 in all; the full reason lists are in the schema):

| First reason | References |
|---|---|
| source has no DIRECT manufacture | 9,104 |
| unresolved: no candidate in the release | 5,607 |
| two-hop chain | 508 |
| conflict with source: dosage form | 397 |
| unresolved: several candidates | 351 |
| conflict with source: active ingredient or strength | 267 |
| conflict with source: incomplete (no form or no active ingredient on one side) | 143 |
| source version selection ambiguous | 135 |
| package code, not a product code | 105 |
| citing kit part | 103 |
| unresolved: code only on a kit part | 41 |
| malformed or missing code | 16 |
| chain ends at an unresolved reference | 9 |
| unresolved: code only in a non-canonical version | 3 |

Population coverage before and after is in section 1. The DIRECT tier is identical before and after: 24,614 DIRECT,
54,457 NO_MANUFACTURE_EVIDENCE, 435 TENTATIVE, 1,002 UNKNOWN_SITE.

## 7. Evidence chains

`python -I scripts/research/dst08_evidence_chain.py --db fineprint_dst08 <NDC>`. `--representative` writes
`evidence_chains.json` for eleven products, one per outcome. Product 60760-661 (meclizine 25 mg tablet, sample R9-01)
gives:

```
SOURCE_LINKED_MANUFACTURING_EVIDENCE  status ELIGIBLE  RESOLVED  SINGLE_HOP  CONSISTENT
citing   60760-661  set c6b3f4d8-5fcf-2278-e053-2a95a90ab139 v5  doc 54cf1e68-62f3-0d64-e063-6294a90a6a38  published 2026-06-23
         part5 / prescription/20260623_c6b3f4d8-….zip  xml sha256 8af7fda8…
         <asEquivalentEntity classCode="EQUIV"> <code code="C64637" codeSystem="2.16.840.1.113883.3.26.1.1" />
           <definingMaterialKind> <code code="16571-661" codeSystem="2.16.840.1.113883.6.69" /> </definingMaterialKind> </asEquivalentEntity>
source   16571-661  set c9ddc39c-bc6b-42f1-8c5f-5aff2d79c4bd v3  doc 2be27ea6-3d0a-4036-ab42-fea4720daa34  published 2025-06-09
         part3 / prescription/20250608_c9ddc39c-….zip  xml sha256 d8e12e54…
source's own DIRECT MANUFACTURE  DUNS 650381903  FEI 3007373532  CURRENT_REGISTERED
         <performance> <actDefinition> <code code="C43360" … displayName="MANUFACTURE" /> <product> <manufacturedProduct classCode="MANU">
           <manufacturedMaterialKind> <code code="16571-661" … /> … </performance>
registration  drls_reg.zip line 5362  sha256 d225e7b7…  generated 2026-10-19
```

An excluded reference returns only the `SOURCE_NDC_REFERENCE` step with its reasons. For example, 53149-4913 gives
`resolution:MULTIPLE_CANDIDATES`: two canonical sets carry the code, and they name different sites.

## 8. Unsafe joins avoided, and the defects found

- **Package codes:** 105 references cite a package code. Truncating it would match exactly one product in 41 cases
  (sample R3-06 looks right) and none in 64. Never done.
- **Several candidates:** 354 references.
  - In 206, every candidate names the same DIRECT sites.
  - In 90, the candidates name *different* sites, and picking one would be a guess (sample R1-10).
  - In 58, no candidate has DIRECT sites.
  - All 354 are excluded. A rule that accepts agreeing candidates is possible later, with review.
- **Name, company or address joins:** none anywhere.
- **Physical-characteristic conflicts among eligible links** (`dst08_characteristics.py`, post-hoc):
  - Of the 19,668 eligible references: 16,936 have an equal imprint and all other stated characteristics equal; 720
    have no imprint but every other characteristic equal; 1,639 have nothing comparable (mostly liquids and
    injectables); 373 conflict.
  - Of the 179 imprint differences, 48 vanish when compared as token sets, the same mark stated for one side or both
    (`RX692` against `RX692;RX692`). The other 131 are real differences, for example `IG;209` against `D;74`,
    `GG931` against `NL4`, `L005` against `L006`, or `ETO;200;MG` against `ETO;300;MG`.
  - 352 of the 373 have a source label newer than the citing label. The conflict rate is 3.4% when the source label
    is newer and 0.2% otherwise: the drift is temporal.
  - These are the clearest unsafe joins rule v1 admits. They are stopped here, and rule v2 should exclude them.
- **Defect 1 (fixed): strength spelling.** The inventory compared strengths as text, so `.25` against `0.25` and `1`
  against `1.0` counted as conflicts. That was conservative, never unsafe. The prototype compares exact decimals,
  which makes 58 references consistent; it is covered by two regression tests. Each change is reported separately
  (section 4).
- **Defect 2 (fixed): build time.** Reopening the release part for every document; covered by the timing record.
- **Diagnostic defect (fixed before use).** The first characteristics run read `subjectOf` from the inner product
  element and found nothing. SPL attaches characteristics to the `manufacturedProduct` role.

## 9. Limitations

- **Verification is AI-assisted and the sample is small (42 eligible links).** Its 0 errors are consistent with the
  1.9% conflict rate found over the population, where 0.8 conflicts would be expected in 42. The sample check and the
  inventory read the XML in the same way.
- **The rule is current-release only.** A repackager may have bought from a different supplier, or the source may have
  changed formulation, site or imprint since the repackager listed it. The characteristic check catches only drift that
  shows in the stated characteristics.
- **Equal characteristics do not prove the same lots.** Equal form, strength and imprint show the same listed product.
  The tier says only that the source is made at one of its N listed sites.
- **Absence is not evidence.** Sources outside the human-Rx release (OTC, discontinued, bulk) show as `NO_CANDIDATE`,
  which is not evidence that the source does not exist.
- **Registration evidence is coarse.** Operations are establishment-level and current (the 2026-10-19 file).
- **Kits are out of scope.** Kits and kit parts would need part-by-part comparison.

## 10. Human-review worksheet

`docs/research/dst08/human_review_worksheet.csv` has 32 rows, high risk first:
- 22 sample rows;
- 10 eligible population links with a real imprint conflict.

Each row has blank columns for: source identity confirmed, manufacturing statement from the correct source product and
version, verdict, reviewer, date and note. The highest-risk rows:

| Row | Citing → source code | Prototype | Why it needs a person |
|---|---|---|---|
| P-IMPRINT-07 | 21695-630 → 65862-079 | ELIGIBLE v1 | imprint `IG;209` (2011 label) against `D;74` (2024 source label): a different tablet |
| P-IMPRINT-09, -10 | 54868-4102, 68788-9150 → 43386-480 | ELIGIBLE v1 | `GG931` against `NL4` |
| P-IMPRINT-08 | 54868-4135 → 51672-4017 | ELIGIBLE v1 | `ETO;200;MG` against `ETO;300;MG` |
| P-IMPRINT-01…06 | (see CSV) | ELIGIBLE v1 | `A;42` against `A;43`, `L005` against `L006`, `RDY;179` against `R;179`, typing variants |
| R1-03 | 53149-4840 → 0116-2001 | ELIGIBLE | link supported, but the citing repackager (unregistered) also claims MANUFACTURE |
| R1-07 | 72258-020 → 11054-010 | ELIGIBLE (product DIRECT) | medical gas; the source lists 180+ sites; the citing transfiller is DIRECT |
| R1-09 | 52959-193 → 68462-190 | ELIGIBLE | link supported; the repackager's own MANUFACTURE claim conflicts with the source's site |
| R1-10 | 53149-4913 → 65162-918 | EXCLUDED | two candidate sets name different DIRECT sites |
| R3-06 | 54868-5183 → 51672-1302-0 | EXCLUDED | package code whose prefix matches one DIRECT product |
| R5-03 | 72162-1406 → 45802-400 | EXCLUDED | 7.70 mg/100 mL against 7.7 mg/mL: probably a data-entry error in the citing listing |
| R5-10 | 0404-9762 → 0641-6243 | ELIGIBLE | eligible only after the decimal fix (`1` against `1.0`) |
| R5-01, R5-07, R5-09 | | EXCLUDED | two-hop chains through relabelers to DIRECT makers |
| R6-02, R6-03, R6-06 | | EXCLUDED | candidate sets that agree on their sites |

Phase 5 items for the same reviewer:
- the ProCare oxygen DIRECT edge (registered TRANSFILL only);
- H.J. Harkins' 103 MANUFACTURE assertions;
- All Pharma's 7 products;
- S098 and S104;
- whether the 60 DIRECT edges without registered MANUFACTURE need a rule.

## 11. Reproduce

```
CREATE DATABASE fineprint_dst08 TEMPLATE fineprint;      -- with no open connection to fineprint
python -I scripts/research/dst08_source_inventory.py --db fineprint
python -I scripts/research/dst08_check_sample.py --db fineprint        # the sample is frozen and never redrawn
python -I scripts/research/dst08_build_lineage.py --db fineprint_dst08 --production fineprint
python -I scripts/research/dst08_evidence_chain.py --db fineprint_dst08 --representative
python -I scripts/research/dst08_characteristics.py --db fineprint_dst08
python -I scripts/research/dst08_repackager_audit.py --db fineprint
python -I scripts/research/dst08_report_counts.py --db fineprint_dst08
python -I -m unittest discover -s tests -t .
```

The inventory CSV and the per-product extract are written to `$FINEPRINT_DATA/research/dst08/`, outside the repository.
Their hashes are recorded in `source_inventory.json` and the sample manifest. The FDA source documents are in
`$FINEPRINT_DATA/research/dst08/sources/`, with hashes in the design note.

## 12. Stop conditions

- **Exact source identity.** Established for eligible references by an exact product code, a unique canonical source in
  another set, and the same form and active ingredients and strengths read from both labels. Human confirmation is
  pending. Where identity is in doubt, the work stopped:
  - 16,789 references excluded by rule;
  - the 373 eligible references with a characteristic conflict, stopped post-hoc and kept out of the usable figure.
- **Product-level attribution.** The source's DIRECT edge is MANUFACTURE scoped to the source's own product code in its
  own label. Unscoped operations never produce evidence.
- **Historical version correctness.** Not established, so the historical work was not attempted. The tier applies to
  the current release only and is excluded from the 2023 evaluation.
- **No confidence rule was weakened to raise coverage.** The one change made after the freeze, exact-decimal strength
  comparison, corrects a demonstrated defect; its 58 extra consistent references are reported separately. The
  characteristic check only removes links.
