# fineprint — six core Claude Code cards + optional later
**Order matters.** Complete one card with proof and concise report before advancing. No feature expansion during a card. Normal PRs/commits; tests at each checkpoint. Data coverage and rates must come from actual runs.

### DST-00 — Feasibility & real-data acquisition spike (start immediately)
- Test five exact pre-2023 archived DailyMed SPL ZIP versions; cite raw product-specific `MANUFACTURE` DUNS, versions, dates and hashes. Verify pre-event Rocky Mount and McPherson identities.
- Document independent historical Hospira panel construction (request complete date archive if appropriate), limitations and candidate count *only if actually observed*.
- Test streaming parsing of a **bounded current human-Rx bulk sample**; record source manifest, read performance and actual XML/operation/unknown categories. Choose one bounded shard/sampling mechanism without inventing national stats.
- **Deliver:** <=2-page `feasibility_report.md`, source manifest, small scripts/tests, independent historical-panel plan, separate **national ingest GO** and **historical eval GO/NARROW**. Stop for review if fundamental inputs inaccessible.

### DST-01 — Nationwide, reproducible bulk ingestion
- Discover and fetch **all available full human prescription release parts**, with checksums, resumability and immutable source manifest. Stream ZIP/XML safely; process each SPL exactly once per version; handle malformed and duplicate documents deterministically.
- Store source records, product/package mappings and raw manufacturing/pack/label operations in Postgres. Batch writes, indexes, idempotence, bounded memory, per-part error/dead-letter report. Keep original file paths and source-level citations.
- **Deliver:** a verified actual national ingest, logs, total/processed/failed document counts, elapsed runtime/memory/storage, tests on fixed real XML samples. Do not label data complete when partitions fail.

### DST-02 — Facility identity, provenance and graph projection
- Resolve DUNS→FEI→physical location from cited FDA facility records; retain aliases and ambiguous/unresolved cases; do not infer production site from labeler or address string.
- Produce source/version/operation aware product→facility relationships and a current snapshot projection. Add separate historical projection from eligible archived sources (not 2026 bulk).
- **Deliver:** Postgres schema/migrations, direct/tentative/unknown decisions, deterministic rebuild and tests (Rocky Mount, McPherson, alias, `PACK` only, multiple facilities, missing DUNS, later version excluded from historical graph).

### DST-03 — Explainable CLI queries & coverage
- CLI query a facility DUNS or product/package NDC for the current national snapshot, returning evidence, operation, original NDC, version and unresolved status; support as-of 2023 **only for the supported historical subset**, with visible scope limitation.
- Produce real counts: represented SPL files, unique package NDCs, distinct facility DUNS, physically resolved sites, direct MANUFACTURE edges, tentative and unknown rate. Optional one descriptive `observed-single-facility` query, explicitly not sole-supplier or substitution analysis.
- **Deliver:** working commands and golden-result tests plus screenshot/text demo from actual imported records.

### DST-04 — Rocky Mount historical evaluation
- Freeze independently built 2023 candidate manifest, date-cutoff policy, normalized package-level panel and outcome separation **before** computing comparisons.
- Evaluate **B1 all Hospira**, **B2 injectables**, **B3 already-short stays short** (mark NOT EVALUABLE if source history doesn't support it), and direct-facility graph. Report equal-denominator positive-list recall, conditional recall, number flagged, list reduction, unknown coverage, separately audited link accuracy. Explicitly note warehouse-vs-production mismatch.
- **Deliver:** versioned eval report with commands, labels, exclusions, tables, real numbers and failure analysis. **Baxter not scored; Intas unscored.**

### DST-05 — Public engineering release
- Repo cleanup, CI on small real/synthetic fixtures (full national download outside CI), deterministic data-rebuild instructions and licensing/attribution checks. README first screen: tornado question + what actually shipped + link to national coverage and 2023 eval; show source evidence trace and honest unknowns.
- **Deliver:** reproducible release/tag and actual source hashes + metrics with environment. No unmeasured national coverage/shortage-prediction claims; no frontend requirement.

### OPTIONAL DST-06 — Weekly refresh and diff (after strong V1)
- Scheduled job ingests DailyMed weekly updates, saves run timestamp and source hashes, applies idempotent set/version updates including explicit withdrawal/supersession policy, reports added/changed/removed product/operation links. Tests for retries, duplicates, missed updates and rebase onto latest full release; publishes a dated changelog.
- This is **not** a prerequisite for V1 acceptance. Never call the feed real-time.

### OPTIONAL V2 (not a current build card) — Evaluated free-text manufacturing mention extraction
- Extract candidate factory mentions from narrative SPL label text (LLM or rule baseline), measure entity/exact-site accuracy/abstention against a manually reviewed and **independently sampled** reference subset with structured establishment edges. Structured records are not perfect ground truth; missing narrative mentions and missing structured links require manual adjudication. Preserve model cost and false-positive analysis; **no automatic promotion to DIRECT**.
- Only consider this after V1 ships and interview/core project priorities allow it.

**Change control:** Six core cards are locked. Scope additions require measured V1 gap or explicit user decision in Career HQ. Maintain technical project decisions here, strategic project priority in Career HQ.
