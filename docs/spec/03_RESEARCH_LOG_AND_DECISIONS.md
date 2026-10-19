# fineprint — decisions, verified leads, disclosures
**As of 2026-10-19; no national ingestion or new historical evaluation has been run as part of this spec revision.** All numerical performance/coverage results are pending.

## Change from Drug Supply Twin v1.2
- **Name:** `fineprint`; tagline "Which factory actually makes your medicine?". No live digital-twin/simulation claim. Repo slug suggested `fineprint`; no trademark/name availability assessment performed.
- **Priority:** user explicitly switched on 2026-10-19; **fineprint active, Environment Truth on hold**. This is deliberate, not a tool assumption.
- **Scope:** wide *modern* national human-prescription bulk ingest; narrow *historical* Hospira/Pfizer evaluation. Removed prior "all-company graph" exclusion. National-scale claim requires real completed import and numbers, not merely downloaded archive metadata.
- **Optional after V1:** `DST-06` weekly delta refresh; V2 evaluated LLM free-text factory-mention extraction, not part of V1 or V1.5.
- **Still cut:** frontend, all historical U.S. drugs, shortage forecasting, RxNorm, alternative supplier equivalence, fancy graph DB, five-grade confidence, additional scored incidents, interview-prep build card.

## External source confirmations for architecture
- [DailyMed national bulk releases](https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm): complete available human-Rx SPL release published in multiple multi-GB parts; daily/weekly/monthly delta release archives also listed. File counts and checksums change with releases; record manifest at fetch time.
- [DailyMed older-version ZIP documentation](https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm): documented historical ZIP by Set ID/version; latest API must not masquerade as old version.
- [DailyMed date archives](https://dailymed.nlm.nih.gov/dailymed/archives/index.cfm): documentation directs requests for all labels on a chosen date to support. Complete historical discovery still open.
- [FDA drug listing](https://www.fda.gov/drugs/drug-registration-and-listing-instructions/how-list-drug): requires establishment names/DUNS per product; [FDA labeler codes](https://www.fda.gov/drugs/drug-registration-and-listing-instructions/how-request-labeler-code) identify marketing company, not a plant.
- [FDA current establishment registrations](https://www.fda.gov/drugs/drug-approvals-and-databases/drug-establishments-current-registration-site-decrs) may help nationwide contemporary DUNS-to-site lookup, but **must not** be treated as historically valid without dated documentation.

## Previously established historical leads — exact XML checks outstanding
- Pfizer [July 21, 2023 letter](https://www.fda.gov/media/170647/download): after July 19 tornado, warehouse largely impacted; 65 low-inventory warning package NDCs reported by independent Vizient review, not a complete all-site-manufactured list.
- Hospira [2015 facility filing](https://dailymed.nlm.nih.gov/dailymed/fda/fdaDrugXsl.cfm?setid=f435e79d-dea3-49dc-8268-146c60ba52a1): DUNS `093132819` / FEI `1021343` / Rocky Mount NC, address "Highway 301 North". Today's other address spelling does not imply another site.
- FDA [2018 filing](https://www.accessdata.fda.gov/drugsatfda_docs/nda/2018/125545Orig1s000ChemR.pdf): `030606222` / `1925262` / Hospira McPherson KS. Naloxone and diazepam historical manufacturing relationships are negative-control candidates and still need exact historical SPL inspection.
- Five Rocky Mount-selected target SPL version dates are listed in evaluation; **contents of exact historical XML versions remain unverified**. Their current counterparts cannot substitute.
- Baxter [Sep 29 notice](https://www.fda.gov/media/182564/download), [Sep 30 made-at-site list](https://nutritioncare.org/wp-content/uploads/2025/01/240930_Baxter-North-Cove_Medical-Assessment.pdf) and [Oct 1 allocation letter](https://nutritioncare.org/wp-content/uploads/2025/03/241001_Allocation-Letter-Baxter.pdf) differ in outcome meaning. North Cove DUNS and admissible pre-event labels not yet demonstrated.
- Prior analogous public project: [ProPublica Rx Inspector data](https://github.com/propublica/rx-inspector-data). Do not present facility/product mapping itself as unprecedented, or use 2025 reference data for 2023 preregistration.

## Holdout contamination and discipline
- User previously saw **count and first ten rows** of Baxter October 1 allocation list, with no linkage analysis.
- Previous assistant saw **heading and some entries** in Baxter September 30 site-made list while searching, with no site-link analysis. **Therefore Baxter is not a blind holdout**, even if later scored under a fully declared protocol.
- Pfizer event positives and candidate examples have been seen before the experiment. Candidate frame must be defined independently of outcomes; separate source paths and manifests; never claim researcher blinding.

## Open questions that can narrow—not expand—V1
1. Can full DailyMed human-Rx bulk files be downloaded affordably/legally and streamed reliably on the chosen machine? What is *measured* storage, memory and retry behavior?
2. What fraction of bulk SPLs have product-specific `MANUFACTURE` operation with usable DUNS? What fraction of DUNS can be matched to physical sites from FDA registration sources? Separately report unresolved identities.
3. Is a sufficiently complete July 18, 2023 Hospira historical package-NDC frame obtainable? If not, how much bias/coverage uncertainty remains?
4. Can the five exact historical positives and historical McPherson counterexample be retrieved and checked from XML?
5. Can B3's as-of shortage status be reconstructed at comparable package granularity? Otherwise B3 = NOT EVALUABLE.
