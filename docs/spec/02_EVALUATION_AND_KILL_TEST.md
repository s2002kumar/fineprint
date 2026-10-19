# fineprint — historical evaluation and DST-00 gate

## Fixed scored experiment
- Event: Pfizer/Hospira Rocky Mount tornado **2023-07-19**. Historical source cutoff **end of 2023-07-18**. Site: DUNS `093132819` / FEI `1021343`. Negative control: Hospira McPherson, DUNS `030606222` / FEI `1925262`.
- **Panel:** pre-register and freeze an *independently assembled*, historically discoverable Hospira `00409` **package-NDC** universe; other Hospira labels investigated separately. Preserve discoverability/marketing-status gaps and exact source manifest. A current index is not a full 2023 label census.
- **Outcomes:** approximately **65** Pfizer July 21 low-inventory *package NDCs*; validate actual count/dedup. Do not label them national shortages, all Rocky Mount products, or an exhaustive negative/positive manufacturing truth. Warehouse damage means matching an actual manufacturing link is not equivalent to explaining this warning list.

### Three baselines plus graph, on the identical candidate panel
| Method | Flagged candidates |
|---|---|
| B1 all Hospira | Every package NDC in frozen panel |
| B2 Hospira injectables | Panel subset classified injectable by pre-event label route/form; predefine missing forms |
| B3 already-short stays short | Panel subset with genuinely verifiable **pre-cutoff** shortage status; if not recoverable at comparable granularity -> **NOT EVALUABLE** (do not replace it silently) |
| Graph | Candidate packages whose **pre-cutoff** SPL product code has direct `MANUFACTURE` operation at Rocky Mount DUNS with dated physical identity proof; unknown separately |

**Primary headline only after running:** "Using labels published before July 19, fineprint flagged **N** eligible package NDCs with Rocky Mount manufacturing links and recovered **X** of Pfizer's **P** warnings, versus **M** candidates required to flag all Hospira products." Report P actual validated count. Also calculate baseline X and N at **comparable recall**. Do not invent N/X/M/P.

### Metrics & audit
- Named-positive recall `|flags ∩ P|/|P|`, and panel-conditional recall `|flags ∩ P ∩ panel| / |P ∩ panel|`; clearly report uncovered positives.
- Candidate size `N`, reduction relative to B1 `1-N/M`, B2 comparison when comparable; report tradeoff if graph misses named positives.
- Unknown/tentative/direct coverage, reason categories, count of sources and actually resolved physical factories.
- `|flags ∩ P|/N` can be called *overlap density*, **not** true manufacturing-link precision or shortage-prediction precision: unlisted drugs may still be made in Rocky Mount.
- Independently random/predeclared sample of asserted links (including other-site and missing-site controls), manually audit against raw archives; report verified/failed/unknown denominators. Five Pfizer-selected positives are **not** representative audit samples.

### DST-00: first acquisition spike, not a full platform
1. Fetch and checksum five *specified archived* pre-event label versions (DailyMed historical ZIP endpoint) and inspect `MANUFACTURE(product-code)` → `DUNS 093132819`. Targets: acetylcysteine `5558a5f5-e821-473b-7d8a-5d33d09f0586` v19; aminocaproic acid `1c5bc1dd-e9ec-44c1-9281-67ad482315d9` v17; aminophylline `9a663ef3-881f-48bd-2689-3713b24545c2` v26; atropine `ad8916e7-206e-409e-2582-30d072845dd4` v25; calcium chloride `c4c65e48-85f8-4dcf-6281-06e40959cc79` v18. Never replace archived data with modern labels.
2. Verify *pre-event* FDA filings: Rocky Mount `093132819`/`1021343`, McPherson `030606222`/`1925262`; verify negative-control **historical** drug label manufacturing at McPherson. Address strings are cited aliases, not inferred joins.
3. Document how an independent 2023 Hospira package-NDC frame could be enumerated, request date-wide archive if needed, and label partial coverage plainly. **Freeze panel definition before consulting appendix for scoring.**
4. Test current nationwide ingestion on a *small representative sample or one bounded shard*: manifest/checksum, streaming XML extraction, observed facilities/operations, malformed/unknown cases, rough memory/throughput. No full schema/graph service required until this passes.
5. Deliver `feasibility_report.md` ≤2 pages, evidence manifest with URLs/versions/SHA-256/published/retrieved, sample audit, national-source size estimate from official manifest (not claimed imported), candidate-frame plan, and explicit GO/NARROW/PIVOT/KILL for historical evaluation. Full national build can GO while historical scoring remains NARROW; separate the two decisions.

**Gates:** No invented evaluation counts; historical metric claims blocked until archived XML and candidacy denominator verified. A national graph without full historical evaluation can still ship honestly, but cannot claim successful 2023 replay.

### Cases excluded from current score
- Baxter North Cove September 2024: September 29 disruption notice has no NDC list; September 30 list titled “Product Codes Made in North Cove” is closer to site membership, whereas October 1 is an allocation list. First verify pre-event SPL DUNS and list semantics. **Not blind**: researcher saw count/first ten October 1 rows; earlier assistant encountered part of September 30 list. No Baxter metrics in V1.
- Intas cisplatin: private-label products mention multiple sites, public shortage history confounded; unscored case note only.

### Official technical references
- https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm
- https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm
- https://dailymed.nlm.nih.gov/dailymed/archives/index.cfm
- https://www.fda.gov/media/170647/download
