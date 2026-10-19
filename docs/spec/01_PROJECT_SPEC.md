# fineprint — implementation spec v1.3
**Tagline:** Which factory actually makes your medicine?
**Decision:** 2026-10-19. fineprint is active; Environment Truth is paused (explicit user decision). Six core cards; optional refresh later. This replaces Drug Supply Twin v1.2.

## Product and research questions
**User question:** Given a medicine or U.S. manufacturing facility, what product/manufacturing links do public FDA/DailyMed records actually establish, which links are unresolved, and what exact records support each answer?

**National engineering objective:** Reproducibly ingest the complete *available current DailyMed human-prescription* SPL bulk release into a versioned graph of facilities, drugs, companies and documented operations. Measure actual documents, links, failures, coverage, throughput and build reproducibility; do not promise that every drug has a resolvable factory.

**Historical research question:** Using only admissible SPL versions and site identity evidence published by **2023-07-18**, can fineprint identify a smaller set of Hospira package NDCs with direct `MANUFACTURE` links to **Rocky Mount** (`DUNS 093132819`) while recovering many of the approximately 65 package NDCs Pfizer flagged in its July 21 post-tornado low-inventory warning? This tests list overlap and candidate reduction, **not** shortage prediction, inventory exposure, manufacturing exclusivity, or causal consequences of the tornado.

## Two deliberately separate data products
| | CURRENT national graph | HISTORICAL Rocky Mount replay |
|---|---|---|
| Inputs | Current human Rx SPL bulk releases, dated ingestion manifest, contemporary site filings | Individual pre-cutoff SPL versions, dated pre-event identity filings, independent candidate-frame method |
| Coverage | All accessible SPL files in the declared release; counts measured, missing links explicit | Hospira 00409 historically discoverable candidate package NDCs; report survivorship/incompleteness |
| Claim | What current public source records assert | What records published by 2023-07-18 assert (reconstructed now) |
| Forbidden | Calling manufacturer labeler or corporate HQ a production site | Using 2026 bulk files, post-event corrections or Pfizer outcomes as historical inputs |

**The current nationwide bulk release is not a historical backfill.** Never substitute a current SPL for a missing 2023 version. Do not imply complete historical coverage without a defensible archival enumeration.

## Sources
1. **National source:** [DailyMed full drug-label releases](https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm) — specifically all `dm_spl_release_human_rx_part*.zip` parts, dynamically discoverable; very large multi-GB files. Record release part, posted/modified date, advertised checksum, bytes, actual SHA-256, retrieval date, file count. Daily/weekly/monthly updates are **not** part of required V1 ingestion.
2. **Historical source:** [DailyMed historical version ZIP](https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm) and [date archives](https://dailymed.nlm.nih.gov/dailymed/archives/index.cfm). For all labels on a date, archive documentation directs researchers to DailyMed support. Archive availability and a complete 2023 Hospira denominator are separate feasibility questions.
3. **Physical-site identity:** dated FDA facility registration filings / [DECRS](https://www.fda.gov/drugs/drug-approvals-and-databases/drug-establishments-current-registration-site-decrs); distinguish present-day site registries from pre-event site evidence. Rocky Mount `093132819` / FEI `1021343`; McPherson `030606222` / FEI `1925262` backed by pre-event FDA filings (see research log).
4. **Outcome, segregated from ingest:** [Pfizer July 21, 2023 warning appendix](https://www.fda.gov/media/170647/download). Do not use to select candidates or link facilities.

## Minimal data model
- `source_document`: kind, source URL, SPL set ID + version or archive part, `published_at`, `retrieved_at`, SHA-256, source role (`current`, `historical`, `outcome`); immutable raw artifact or reproducible download recipe. Publication date can be **unknown**; never fabricate it from retrieval date.
- `organization`: sourced name and labeler identifiers; **not a physical site**.
- `facility`: DUNS and, when admissibly established, FEI; address/name variants retained as cited attributes; no inferred exact identity from corporate name.
- `product`: SPL set ID + version, raw product NDC and parsed NDC segments, labelled name/form/route when present.
- `package`: raw package NDC with explicit link to product NDC; preserve 10-/11-digit ambiguities, never pad or join uncritically.
- `assertion`: product NDC → DUNS → operation (`MANUFACTURE`, `PACK`, `LABEL`, etc.), specific version/source and confidence; many-to-many accepted.
- Graph is a **relational graph projection** on PostgreSQL (Python ingestion + SQL/CLI traversal), not a Neo4j requirement. Index source/version, product NDC, DUNS, operation.

**Confidence:** `DIRECT` = explicit `MANUFACTURE(product)` in the SPL plus exact cited DUNS→physical-site identity; `TENTATIVE` = partial identity/role evidence; `UNKNOWN` = missing/unsupported. A DUNS manufacturing operation with unknown physical address can be direct-to-DUNS but must **not** be presented as a known physical factory. `PACK`/`LABEL` never become `MANUFACTURE`.

**Provenance & time:** Keep the original XML, raw values, parsing location/excerpt, release/version, source publication date and retrieval date. As-of queries use **publication dates** only where historical archives support them; ingestion snapshots show **retrieval date** as a separate dimension. Historical availability does not prove the drug was marketed or stocked on that date. Handle contradictory versions as separate assertions; current snapshot chooses one documented version per Set ID with deterministic precedence.

## Core workflow / representative queries
1. Ingest and count national source files, unique SPLs, product/package codes, facility DUNS, resolved FEIs, operation-specific links, unresolved site identities and parse failures. Benchmarks use real source bytes; log hardware, wall-clock and storage.
2. `fineprint facility <DUNS> [--snapshot current | --as-of YYYY-MM-DD]` returns supported products, other-site comparisons, unresolved statuses, direct evidence (source+version+operation), and **scope/coverage warning**.
3. `fineprint explain <NDC> ...` returns product→facility path or an honest reason for unknown. Correctly distinguish manufacture vs packaging and normalize `00409-3308-03` ↔ `0409-3308` only through explicit segment relationships.
4. Optional README descriptive query: products for which **only one documented manufacturing DUNS is observed**. Label as *observed uniqueness in ingested sources*, NOT unique U.S. supply or absence of other manufacturers. No clinical drug-equivalence semantics.

## Non-goals
No national historical time machine, real-time factory status, shortage-risk prediction, inventory/stock levels, substitute drugs or suppliers, RxNorm concept graph, LLM, React UI, automatic address-geocoding identity joins, separate graph database, or all-company impact claims. **Baxter** remains a conditional case only; **Intas** remains an unscored ambiguity note.

## V1 acceptance
- Full current human Rx release processed, or failures/blocked partitions explicitly reported without claiming completeness; manifest with source hash/bytes and deterministic re-runs, idempotent ingest, tests for corrupt/missing/duplicate/XML version cases. Full national processing need not run inside CI; fixed real samples must.
- Exact operation-aware evidence paths for every reported direct facility link; tests proving labeler != facility, `PACK` != `MANUFACTURE`, DUNS-to-FEI identity exact and source-dated, and unknown != absence.
- Archived 2023 Rocky Mount panel and honest denominator caveats; 3 fixed baselines; published measured evidence report **only if historical gate passes**.
- README: problem, source inventory, example evidence trace, architecture, data coverage and benchmark measured on actual workload, historical limitations, failures, and reproducible CLI. No manufactured throughput, recall, completeness or precision.

## Technical risks & response
- **Multi-GB source size:** implement bounded-memory streaming archive traversal; checksum validation, archive-bomb/path-traversal protection, resumable part ingestion, incremental commit batches. Test on small part/sample before full sweep.
- **Factory identifiers not resolved:** report DUNS-only relationships without a physical address, never guess; audit identity coverage.
- **Version/source survivorship:** current bulk index cannot enumerate a complete 2023 historical census. Mark panel as incomplete if archival coverage fails.
- **Hindsight leakage:** run current graph and historical replay in separate source domains; seal outcome data until candidate frame and source hashes frozen.
- **Company-wide baseline is deliberately strong on recall:** compare at the same candidate denominator and show recall vs list-size tradeoff, not spurious precision.

## Source differentiation / originality
Facility-product public linkage is not newly invented; ProPublica's [Rx Inspector data](https://github.com/propublica/rx-inspector-data) is prior work. fineprint differentiates on reproducible national SPL ingestion, operation-aware provenance, explicit unresolved identity, and historically constrained evaluation, with no claim of first-ever mapping.
