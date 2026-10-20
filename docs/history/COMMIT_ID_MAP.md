# Commit ID map (local history sanitization, 2026-10-20)

History was rewritten **locally** with `git filter-repo`. The rewrite changed two things:

- personal filesystem-path fragments in 5 history-only blobs;
- the author/committer identity, which is now a GitHub noreply address.

File contents at HEAD are unchanged, including the tree hash and every frozen evaluation file's SHA-256.
Commit IDs cited in `docs/history/*` and in commit messages written before the rewrite use the **old** IDs. filter-repo rewrote abbreviated IDs inside commit messages; this table resolves the rest.

The freeze tag `dst04b-freeze` now points to the new commit. Its manifest SHA-256 is unchanged (`361e21ba…`). The evaluation results record the pre-rewrite tag commit `16245583…`.

| old | new | subject |
|---|---|---|
| `04df3b0` | `da545f0` | Use write_json in part download script |
| `1511959` | `bc8b7a7` | Historical plan A5: DST-04B freeze + scoring protocol (pre-freeze, pre-unseal) |
| `1624558` | `8ddfa24` | DST-04B FREEZE: cohorts M (469) and E (890), classifications, baselines, audit sample |
| `17a496c` | `7608437` | DST-04B link audit completed before unsealing: 40/40 VERIFIED (20 DIRECT, 10 OTHER_SITE, 1 |
| `1a5b33f` | `dd230cc` | Historical plan A4.1 (pre-rerun): record getFile 404 cutoff versions; same-version doc-ID  |
| `27f3e52` | `af4c422` | DST-05: offline re-verification modes, CI workflow (stdlib + PostgreSQL 18), progress log |
| `282269d` | `02f9d6f` | Git history audit (read-only): no secrets; 4 history-only home-path blobs; personal author |
| `28abe31` | `e7a5d30` | Git history audit after final commits |
| `319b950` | `07fb891` | Historical plan amendment A4: DST-04A draft universe and coverage method (pre-run) |
| `3aaf062` | `6e5708b` | Write evidence JSON with LF on every platform |
| `3e82a6e` | `0183fcd` | Ingest writes a PID file (operator visibility, external kill test) |
| `5179eb9` | `7a5663f` | DST-00: acquisition scripts, streaming SPL parser, tests, evidence; pre-register frame |
| `5533384` | `64f2553` | Plan A5.2 (post-unseal, extraction only): repair one stray space inside a 5-4-2 NDC segmen |
| `579bf36` | `1bfbd07` | Stream zip metadata into COPY line by line (peak RSS 229 MB -> 90 MB on smoke run) |
| `5cc9425` | `d162ed8` | Audit report masks to category tokens only (first report leaked partial fragments) |
| `5e595d9` | `30e27d1` | DST-02/03 evidence from clean-tree build 6: graph build, coverage, query benchmark, exampl |
| `6585e2c` | `f393c37` | DST-05: clean-environment reproduction script and comparison tool; freeze --out-dir |
| `6766255` | `137ae3f` | Add fineprint spec v1.3 documents |
| `7617411` | `6732dc9` | DST-00: frame pilot, source manifest, feasibility report |
| `7e8e909` | `65d3f2d` | DST-04B scored: graph recovers 63/65 Pfizer warning NDCs with a 46% (E) / 50% (M) shorter  |
| `8514aaf` | `aee1a7e` | DST-01: ingestion report, final coverage, restart/idempotence evidence |
| `a143ab6` | `d231998` | DST-04A: draft historical candidate universe, coverage and source manifest (A4-A4.2) |
| `b937da1` | `b22120e` | Historical plan A4.2 (pre-run): recover cutoff versions from 2023 monthly archives by rang |
| `be930fa` | `c2b3a3d` | DST-05: clean-clone reproduction verified identical (DB fingerprints, frozen files, result |
| `c27cc17` | `0fa1591` | Historical A1: reconcile DailyMed labeler search (A) with archived NDC Directory (D) |
| `c947aee` | `6d5a084` | Plan A5.1 (post-unseal, extraction only): rejoin spaced hyphens in PDF text before NDC tok |
| `ccf2a7a` | `44e6b8a` | DST-02/03: version selection, dated DUNS identity, provenance edges, explainable CLI |
| `d0b1b51` | `98c3004` | Review: precise history-audit findings (5 history-only blobs) |
| `d4c2f20` | `1200f44` | DST-02/03/04A combined review document; README query usage |
| `e3d07b5` | `1ad4091` | DST-01: schema, resumable downloader, ingest pipeline, tests; plan amendments A1-A3 |
| `e48334a` | `98b740e` | Ingest: retry a batch on MemoryError; never dead-letter resource exhaustion |
| `e5466dd` | `a06266b` | graph_build.finished_at uses clock_timestamp() (now() is transaction-start time) |
| `ea4b55b` | `002eae2` | DST-05 docs: README, architecture, evaluation report, reproducibility guide; tidy tree |
