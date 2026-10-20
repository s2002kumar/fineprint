# fineprint DST-01 ingestion report — 2026-10-19

**Status: DST-01 complete; stopped at the review gate (DST-02 not started).**

The full current DailyMed human-Rx release (2026-10-16, all six parts) is ingested into PostgreSQL with:
- **0 failed documents**;
- a **verified restart test**;
- a **verified idempotent re-run**.

Every number below comes from a recorded run in `evidence/dst01/`. Machine: Windows 11, 22 logical CPUs, 15.4 GB RAM; Python 3.14.5, psycopg 3.3.6, PostgreSQL 18.0.

## 1. What was implemented
- **Project PostgreSQL cluster** (`scripts/pg_local.py`).
  - Data lives under `$FINEPRINT_DATA` (default `~/fineprint-data`, outside OneDrive); the server listens on 127.0.0.1:55432 only.
  - The generated password is stored in `$FINEPRINT_DATA/secrets`.
  - The existing PostgreSQL service is untouched.
  - Override with `FINEPRINT_DSN`.
- **Schema `national`** (`migrations/001_national_ingest.sql`; migrations are immutable and checksummed).
  - `source_file` has a `CHECK (source_role = 'current')`, so historical sources cannot enter it.
  - Tables: `archive_member` (unit of resume and isolation), `dead_letter`, `spl_document`, `organization_mention` (labeler / registrant / establishment as positioned in the SPL), `product` (products and kit parts), `package`, `operation_assertion` (one row per performance × product code × DUNS, with indexed XPath `loc`), `operation_type`, `dailymed_zip_metadata`.
  - Views: `v_product_establishment_evidence` and `v_version_conflicts`.
- **Downloads** (`download.py`, `scripts/dst01_fetch_release.py`).
  - Parts are discovered from the live page.
  - Resume uses `Range` + `If-Range: <ETag>`, so a changed object restarts and is never spliced.
  - A file is accepted only if its length equals Content-Length and its MD5 equals the advertised value; its SHA-256 is recorded.
- **Ingestion** (`ingest.py`, `scripts/dst01_ingest.py`).
  - Single writer, enforced by an advisory lock.
  - Each source file is re-hashed before use.
  - One member is in memory at a time, with hard byte caps.
  - Each document is stored in a SAVEPOINT, so any per-document error becomes a `dead_letter` row and the batch continues.
  - Commits happen per 200-member batch together with `archive_member` rows, so a kill loses at most the open batch.
  - Re-runs skip recorded members; documents are unique on `(set_id, version, xml_sha256)`.
  - `MemoryError` triggers a batch rollback and bounded retry, and is never dead-lettered (§5).
- **Normalization.**
  - Operations are keyed by NCI **code**; raw display names are kept, and `operation_type.canonical_name` is the dominant upper-cased variant.
  - Products get `ndc_product_5_4` and packages get `ndc_package_5_4_2`, in separate tables and shapes.
  - Normalization works only from explicit hyphen patterns; raw codes are always kept.
- **Publication date** comes only from DailyMed's official `dm_spl_zip_files_meta_data` `UPLOAD_DATE`, and only when ZIP name, set ID **and** version all agree. Otherwise it is NULL. The filename date and XML `effectiveTime` are stored separately.
- **Tests:** 51 pass (`python -I -m unittest discover -s tests -t .` with the venv interpreter).
  - They run against real PostgreSQL: load semantics, crash → resume fingerprint equality, idempotent re-run, cross-part dedup, injected `MemoryError`, migration re-apply.
  - Plus a local HTTP Range/If-Range server, real current and historical fixtures, and guards against contacts and home paths in the repo.
  - With a stdlib-only interpreter the 7 DB tests skip.

## 2. Sources (`evidence/dst01/release_manifest.json`)
**Release parts.**
- 6 parts, all advertised Last Modified 2026-10-16.
- **17,979,089,637 bytes**; every part's **MD5 = advertised**; SHA-256s are recorded.
  - Part 6 (`7708d214…`) is byte-identical to the DST-00 download.
- Downloads ran on 3 parallel connections, about 3 MB/s each, in a 37-minute window (20:53–21:31 UTC).
  - Part 6 was deliberately interrupted at 318,767,104 bytes and resumed from that byte; the final MD5 matched.
- A second fetch re-hashed all 18 GB in 40 s; all parts were `verified_existing`, with no re-download.

**Metadata file:** `dm_spl_zip_files_meta_data.zip`, 7,670,995 bytes, MD5 = advertised, 159,373 rows, 0 malformed.

## 3. Ingest measurements (run 1, clean, commit `3e82a6e`, clean tree)
| Measure | Value |
|---|---|
| Archive members processed / advertised | **55,064 / 55,064** (each part's member count = advertised) |
| Loaded / duplicate / failed (dead letters) | 55,064 / 0 / **0** |
| Wall clock (incl. re-verifying 18 GB, ~100 s) | **1,387 s (23.1 min)**; 33–52 members/s and 11–17 MB/s per part |
| Time split, all parts | read 179 s · parse 605 s · DB 439 s |
| Peak RSS (ingest process) | **73.3 MB** |
| Storage | raw 17.99 GB; database `fineprint` 532 MB; cluster dir 1.51 GB (3 DBs + WAL) |

Rows: `spl_document` 55,064 · `organization_mention` 158,291 · `product` 88,501 · `package` 233,934 · `operation_assertion` 129,952 · `operation_type` 15 · `dailymed_zip_metadata` 159,373. Full detail: `evidence/dst01/coverage.json`.

## 4. Coverage (counts over all ingested documents)
- **Documents.** 55,064 documents cover 52,747 set IDs.
  - **2,311 set IDs ship in this "full" release at more than one version**, for example `a2e01d9b…` at v6 and at v7. All are kept; picking one current version per set is DST-02's job.
  - 0 same-version conflicts.
  - Document types: 54,851 `34391-3` "human prescription drug label", plus small variants (`45129-4` labels with highlights; 1 vaccine label).
- **Establishment evidence.**
  - 43,138 documents have an establishment block; **11,926 have none**.
  - 15,329 documents assert ≥ 1 `MANUFACTURE` to a DUNS.
  - Establishment mentions: 52,158 · without DUNS 0 · **with FEI or address 0** (labels carry DUNS only).
  - 4,347 distinct establishment DUNS; 3,352 distinct `MANUFACTURE` DUNS.
  - **1,265 DUNS appear as both labeler and establishment**, so role is judged per assertion.
- **Products by evidence state** (84,467 products; kit parts excluded):

| Evidence state | Products | Highest version per set only |
|---|---|---|
| EXPLICIT_MANUFACTURE | 27,648 (32.7%) | 26,015 of 80,508 |
| OTHER_OPERATIONS_ONLY (e.g. repack/relabel) | 28,888 | 28,157 |
| NO_ESTABLISHMENT_BLOCK | 20,045 | 18,453 |
| ONLY_UNSCOPED_OPERATIONS_IN_DOCUMENT | 7,762 | 7,762 |
| ESTABLISHMENTS_LISTED_NOT_FOR_THIS_PRODUCT | 124 | 121 |

- **Assertion scope:** `product` 123,364 · `no_product_scope` 6,060 · `kit_part` 528 · `unmatched_code` 0.
- **Operation codes.** 15 codes; each maps to exactly one normalized name, despite up to 5 raw spellings (case, trailing spaces).
  - `MANUFACTURE` C43360: 35,785 assertions · REPACK 27,410 · ANALYSIS 22,408 · RELABEL 18,441 · PACK 12,732 · LABEL 8,133 · API MANUFACTURE C82401: 3,423 · others below 1,000.
- **NDC normalization.**
  - Products: patterns 5-3: 47,344 · 5-4: 28,486 · 4-4: 8,637. 11 product codes could not be normalized and are kept raw.
  - Packages: 233,934 in total; 27,025 have no NDC; 21 could not be normalized (including 4 unhyphenated 13/14-digit codes); 195,191 distinct 11-digit codes.
  - 28 packages whose raw segments don't match their product are kept and flagged, not "fixed".
- **Publication date.** 51,910 documents have one. Checked against the history service on a seeded sample of 60: **54/54 exact** where `UPLOAD_DATE` exists; the filename date matched only 44/60. The **3,154 undated** documents are:
  - 2,317 superseded versions shipped alongside their successors;
  - 730 set IDs absent from the metadata file;
  - 107 cases where the metadata lists a newer version than the release contains.

  None of these is filled from other dates.
- **Anomalies:** 306 documents (602 products outside the product-data section, 9 duplicate product codes, 2 duplicate operation codes). All are flagged and loaded.

## 5. Reliability results
- **Idempotent re-run (run 2):** 101 s; 0 members processed (55,064 already done); 0 metadata rows; **fingerprint identical**.
  - The fingerprint is a natural-key MD5 per table, with no surrogate IDs.
- **Restart test on real data**, separate database `fineprint_restart` (`evidence/dst01/restart_test.json`):
  1. In-process hard exit after 7,000 members, at a batch boundary.
  2. Resume, then hard exit with 150 members in an open, uncommitted batch. Exactly those rolled back.
  3. Resume, then **external `taskkill /F`** after 90 s.
  4. Resume, which **failed with `MemoryError`** (see below).
  5. Resume to completion.

  Members committed per run: 7,000 + 3,000 + 3,000 + 40,953 + 1,111 = 55,064. **All 7 table fingerprints equal the clean run.** Stale runs were marked `interrupted` automatically.
- **Failed-document isolation** on real data: 0 failures occurred, so it is verified by tests (corrupt nested ZIP, truncated XML, traversal name → 3 dead letters while 5 documents load).

**Failures found and fixed during DST-01:**
1. **`MemoryError` in restart run 4.** It happened in `read_member` while reading a part-6 batch whose largest member is 11.3 MB. The machine was at about 1.3 GB free commit (WSL alone held 5.4 GB); the process peak was only 82 MB.
   - The batch rolled back correctly, but the run stopped.
   - Worse, a `MemoryError` during the DB step would have been **dead-lettered as a document defect**.
   - Fixed in `e48334a`: batch-level rollback and bounded retry, never dead-lettered; persistent failure still fails the run. Tested.
2. **Peak RSS of 229 MB** from loading the metadata file whole. It now streams line by line into COPY: 90 MB on the smoke test, 73 MB on the full run.
3. **The pgpass file had CRLF line endings**, which libpq rejects; it is now forced to LF.
4. **Stopping a hung setup command killed the cluster process**; it was restarted, and `pg_ctl start` now detaches stdio.
5. **Committed evidence embedded absolute home-directory paths** (23 strings across DST-00 and DST-01 files). They are now scrubbed to `$FINEPRINT_DATA/…`, and a guard test was added.

## 6. Historical follow-ups (historical domain only; nothing entered `national`)
- **189 vs 213.** Plan amendment A1 was committed before the run (`evidence/historical/frame_reconcile.json`).
  - Of the 213 `0409` documents in the archived NDC Directory (FDA-generated 2023-05-05):
    - **164 match** a current DailyMed Hospira set by exact document ID;
    - 6 have their product in a set under another version (2 resolved by the adjacent version);
    - **43 documents (67 of 477 packages, 14.0%)** have product NDCs found in **no** set DailyMed returns today. The `ndc=` search was verified on known NDCs.
  - On the DailyMed side, 17 sets carry only labeler `61703` (not `0409`) and 11 were first published after the cutoff.
  - **Conclusion:** today's search cannot enumerate the full 2023 frame. The date-archive request remains necessary.
- **A2:** the 2022 registration record establishes site identity only, **not** registration status in 2023.
- **A3:** B3 stays **NOT EVALUABLE** until a dated shortage-state source exists.
- The outcome appendix has still never been fetched.

## 7. Incomplete / not done
- No facility identity resolution or DIRECT/TENTATIVE/UNKNOWN (DST-02).
- No current-snapshot version selection (2,311 multi-version sets await DST-02's precedence rule).
- No CLI (DST-03).
- No weekly deltas.
- Real-data dead-letter handling is untested because no real failures occurred.
- Throughput is one machine under heavy unrelated memory pressure; the raw files and the cluster are local only, with no backup.
- The DailyMed date-archive request (needs your email) is still outstanding.
- Run 2 (the re-run) had uncommitted edits in the tree; run 1, the source of every count here, did not.
