# DST-08 source-NDC relationships: semantics, sources and rules

**Status: research only.** This note fixes the meaning of the three relationships and the eligibility rules
*before* the stratified sample is drawn and before any prototype count is computed. Nothing here changes the
production graph, `site/data/`, the frozen benchmark or any release.

## 1. Primary sources

Retrieved 2026-10-25 (UTC) with a generic User-Agent. The files are kept under
`$FINEPRINT_DATA/research/dst08/sources/` and are not committed; the hashes identify the exact bytes read.

| File | Source | URL |
|---|---|---|
| `ecfr_21_207_53.xml` | 21 CFR 207.53, eCFR point-in-time text as of 2026-10-01 | https://www.ecfr.gov/api/versioner/v1/full/2026-10-01/title-21.xml?part=207&section=207.53 |
| `ecfr_versions_207.json` | eCFR content versions of 207.53 | https://www.ecfr.gov/api/versioner/v1/versions/title-21.json?part=207&section=207.53 |
| `spl_ig_84201.pdf` | FDA, SPL Implementation Guide with Validation Procedures v1 (December 2023) | https://www.fda.gov/media/84201/download |
| `spl_step_by_step_76331.pdf` | FDA, Step-by-Step Instructions for Creating SPL Files for Electronic Drug Establishment Registration and Drug Listing v2.0 | https://www.fda.gov/media/76331/download |
| `spl_technical_errors_86156.pdf` | FDA, SPL technical errors and solutions (eBook) | https://www.fda.gov/media/86156/download |
| `repack_common_errors_154505.pdf` | FDA, repackers and relabelers: common listing errors (slides) | https://www.fda.gov/media/154505/download |

```
1e6d4d0eeb641be9784fdd44c7b0116c835e3a9e7df83083ec02f8a2f360679c  ecfr_21_207_53.xml
6aadfc512c3d1ec0fc27c08ebbe4745c7db240245859462a3b7400a298cffc08  ecfr_versions_207.json
9845e23cb51ee2e7f493b17ed5729b2bc946040244e6f6da2d78c9491a41f983  spl_ig_84201.pdf
d1f167b9edf911e16e38cc7ea40e49c788d4bdf99eb09a254e6a3c96d9798883  spl_step_by_step_76331.pdf
262995100631706d531e6fd98eab43bc4bcaa076f7a3f00f1d938ec5843ec431  spl_technical_errors_86156.pdf
982e10cd46066036673f68be97f09e99244f6d82cb74e0edc02c26db51d5f770  repack_common_errors_154505.pdf
```

### What they establish

- **Regulation.** 21 CFR 207.53(b): "Source NDC. The NDC assigned to each finished drug received by the registrant
  for repacking or relabeling, with the exception of medical gases. Each such NDC must be associated with the
  corresponding NDC(s) for repacked or relabeled drugs, reported under paragraph (a) of this section." 207.53(c)
  separately requires the establishments where *repacking or relabeling* is performed. The section names no
  manufacturer, lot, date or version of the source drug. The eCFR lists two substantive content versions
  (2016-11-29 and 2021-04-01); the 2021-04-01 text was in force throughout 2023 and is the current text.
- **Encoding (IG 3.1.2, 3.2.2).** Under a product (`subject/manufacturedProduct/manufacturedProduct`) or a kit part
  (`part/partProduct`):

  ```xml
  <asEquivalentEntity classCode="EQUIV">
    <code code="C64637" codeSystem="2.16.840.1.113883.3.26.1.1"/>          <!-- equivalence "Same" -->
    <definingMaterialKind>
      <code code="source NDC Product Code" codeSystem="2.16.840.1.113883.6.69"/>
    </definingMaterialKind>
  </asEquivalentEntity>
  ```

  The IG reserves other equivalence codes (for example a pending "Predecessor Product" code), so the equivalence
  code, not the element name, is what makes a reference a product source.
- **Submission-time validation.** The source code matches an NDC product code in an SPL with a *different set id*
  (3.1.2.4); it is not the product's own code (3.1.2.5); there is only one product source per product (3.1.2.8);
  active ingredient UNIIs and strengths, dosage form, size, shape, colour, imprint, flavour and scoring are the
  same as the source's (3.2.2.3–3.2.2.10); a repack or relabel operation requires a product source (3.2.2.11).
  The technical-errors eBook adds that the source code "should match an NDC product code/item code … in the
  original manufacturer's SPL file" and must not repeat the product's own code to bypass the rule that a product
  without a source lists a manufacture operation.
- **What validation cannot establish.** These checks run once, against whatever source listing existed at
  submission. Nothing re-checks the reference when the source label changes, nothing records which lots came
  from which supplier, and nothing says the source drug was made at any particular site.

## 2. The three relationships

| Relationship | Meaning | Evidence | What it does NOT mean |
|---|---|---|---|
| `DIRECT_MANUFACTURE` | The product's own canonical SPL lists a MANUFACTURE (C43360) operation scoped to the product's own NDC at an establishment that passes every DIRECT rule (current registration with FEI, not expired, FEI unchanged across snapshots, version selection not ambiguous). | Existing `national.operation_edge` with `confidence = 'DIRECT'`. | Not changed by DST-08 in any way. |
| `SOURCE_NDC_REFERENCE` | The citing registrant asserts, under 207.53(b), that the finished drug it repacks or relabels as this product was received under the cited NDC product code. | One `asEquivalentEntity` element (C64637, NDC code system) in the citing product's canonical SPL, kept with its exact location and the citing document's hashes. | Not a manufacturing statement. Not a statement about a version, a date or a lot. Not verified by FDA after submission. |
| `SOURCE_LINKED_MANUFACTURING_EVIDENCE` | An eligible `SOURCE_NDC_REFERENCE` (section 4) composed with a `DIRECT_MANUFACTURE` edge of the single resolved source product. Read as: "this product cites source product S; S's own current listing directly names establishment E as a manufacturer of S." | Both endpoints and every step: the citing element, the resolved source product (set id, version, document), the source's own MANUFACTURE performance, and the FDA registration line. | **Never** a direct manufacturing assertion for the repackaged product or any package of it. It does not say which of S's sites made the lots this repackager received, or that S was listed the same way when the repackager received it. |

`SOURCE_LINKED` is a separate, lower tier. A product that is DIRECT stays DIRECT whatever it cites; a product
reaches the source-linked tier only if it is not DIRECT. The two tiers are never added into one "coverage" figure
without both parts shown.

## 3. Normalization and resolution

- **Codes are matched exactly.** The cited code must be in the NDC code system (2.16.840.1.113883.6.69) and match a
  product pattern (4-4, 5-3 or 5-4). It is then put in 5-4 form by `fineprint.ndc.to_product_5_4`, the same
  function that keys `national.product`. A three-segment *package* code is a different identifier: it is recorded
  as `PACKAGE_CODE_NOT_PRODUCT_CODE` and never truncated into a product code, even when the truncation would match
  exactly one product. That count is reported only as a diagnostic of what an unsafe join would have done.
- **Candidates** are top-level products (not kit parts) in the canonical version of a *different* set of the same
  graph build. Exactly one candidate is `RESOLVED`; more than one is `MULTIPLE_CANDIDATES`; a code found only in
  the citing set, only as a kit part, or only in a non-canonical version is recorded as such and not resolved.
- **Versions.** The citing reference comes from the citing set's canonical version and the source from the source
  set's canonical version in the same release (DailyMed 2026-10-16, graph build 8). Both versions and both
  effective dates are kept. A source whose version selection is `ambiguous` or `unresolved` is excluded.

## 4. Eligibility for source-linked evidence (rule `dst08-lineage-v1`)

A reference carries `SOURCE_LINKED_MANUFACTURING_EVIDENCE` only if **all** hold; otherwise it is `EXCLUDED` with
every failing reason recorded:

1. it has the Implementation Guide form: class `EQUIV` or absent, equivalence C64637 in the NCI system, an NDC
   product-pattern code, not the product's own code, the only source on the product;
2. it is on a top-level product, not a kit part (a kit part's source is evidence about one component, not about
   the kit);
3. the code resolves to exactly one source product, whose set version selection is `confirmed` or `unconfirmed`;
4. the chain is a single hop: the source product cites no source of its own (a source that itself cites a source
   is a repackaged product; multi-hop chains and cycles are recorded but not followed in this pilot);
5. the source's dosage form and its active ingredients (UNII, numerator and denominator strength) equal the citing
   product's, read from both XML files — the checks FDA states it applies at submission, re-applied to the
   current listings; a difference is a conflict, not a tolerance;
6. the source product has at least one DIRECT MANUFACTURE edge scoped to it in its own SPL.

No name, company, address, labeler code, or product-name similarity is ever used to create, choose or rescue a
link.

## 5. Temporal validity

The source-linked relationship is a statement about the 2026-10-16 release only. It is **not** used in, and must not
be back-filled into, the historical 2023 evaluation (`dst04b-freeze`): a 2023 citing version may have cited a
different source, and the source's 2023 listing may have named different sites. Newer records are never
substituted for historical evidence; a historical relationship would need the historical citing version, the
historical source version, and a registration snapshot from the same period, which this pilot does not attempt.

## 6. What missing evidence means

| Observation | Meaning | Not a reason to conclude |
|---|---|---|
| no source reference | the product does not state a source | that it is not repackaged, or that it is manufactured in-house |
| `NO_CANDIDATE` | no canonical human-Rx product in another set has the code in this release | that the source does not exist (it may be OTC, discontinued, outside this release, or a code error) |
| `MULTIPLE_CANDIDATES`, conflict, multi-hop, cycle | the source cannot be identified safely by these rules | that the reference is wrong |
| source not DIRECT | the source's own listing lacks DIRECT evidence | anything about where the source is made |
| `EXCLUDED` | not used for coverage | that the relationship is false |

## 7. What is measured, and how it is checked

- `source_inventory.json`: an independent raw-XML inventory of every `asEquivalentEntity` in the 52,747 canonical
  labels, with every validity, resolution and chain class counted (script `dst08_source_inventory.py`).
- `sample_manifest.json` / `sample_FREEZE.json`: a seeded stratified sample, frozen and committed before any sampled
  reference is examined (script `dst08_sample.py`; strata and sizes are recorded there).
- `sample_checks.json`: mechanical re-derivation of each sampled reference from raw XML — the citing element, the
  source candidates from all product rows, both products' forms and ingredients, the source's MANUFACTURE
  performances, every version of the source set in the release (script `dst08_check_sample.py`).
- `sample_ai_review.csv`: an AI-assisted reading of those checks, kept separate from `human_review_worksheet.csv`,
  which is blank and awaits human adjudication. No AI-assisted result is presented as a human audit.
- The prototype (`src/fineprint/lineage.py`, `scripts/research/dst08_lineage.sql`) runs only in a scratch database
  and is checked against the inventory, for reproducibility, and for leaving every national table unchanged.
