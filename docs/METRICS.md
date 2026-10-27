# Metrics, and what is and is not verified

Reference machine: Windows 11, Python 3.14, PostgreSQL 18, consumer laptop running close to its memory commit limit.
Linux is covered by CI on PostgreSQL 18; CI runs the tests, not the 18 GB build.

## Measured, with the evidence file that records it
| Stage | Result | Evidence |
|---|---|---|
| Download | 6 release parts, 17,979,089,637 bytes; every MD5 equals DailyMed's advertised value; interrupted download resumed at byte 318,767,104 | `evidence/dst01/release_manifest.json` |
| Ingest | 55,064 / 55,064 archive members, 0 failed; 1,387 s (23.1 min); peak RSS 73 MB; database 532 MB | `evidence/dst01/ingest_run1_clean_full.json` |
| Idempotent re-run | 101 s; 0 rows added or changed (table counts identical) | `evidence/dst01/ingest_run2_idempotent_rerun.json` |
| Crash and resume on real data | 5 runs: two forced exits mid-batch, an OS kill, a real `MemoryError`, then a resume to completion; table fingerprints equal to the clean run | `evidence/dst01/restart_test.json` |
| Graph build | 11.8 s and 9.6 s; second build fingerprint-identical; peak RSS 131 MB | `evidence/dst02/graph_build.json` |
| Graph contents | 52,747 sets; 123,200 edges (MANUFACTURE: 30,015 DIRECT, 553 TENTATIVE, 3,008 UNKNOWN); 3,444 facilities (FEI) | `evidence/dst02/graph_build.json`, `evidence/dst02/coverage.json` |
| Query latency (median of 5) | `compare` 2.8 ms · `facility` 3.9–6.1 ms · `labeler` 8.2 ms · `product` 16–22 ms · `search` 27 ms · `unresolved` 32 ms · `coverage` 0.73 s · `evidence --raw` 81 ms | `evidence/dst03/query_benchmark.json` |
| Clean-clone reproduction | fresh clone and venv; ingest 662 s at 95 MB peak; graph builds 10.8 s and 12.5 s; every table fingerprint, all 6 frozen historical files and the evaluation results identical to the reference | `evidence/dst05/reproduction.json` |
| Daily update 2026-10-19 (on a copy of the database) | 207 prescription labels ingested in 4.19 s (90 MB); 196 retractions applied; edges +80 / −89 / 0 modified / 624 carried forward; second application: 0 labels loaded, 0 changes | `evidence/dst06/refresh_10192026_pass1.json`, `…_pass2.json` |
| Historical replay | P = 65 validated outcome NDCs; graph 480 candidates, 63 recovered; all-Hospira 890, 63 recovered; 0 leakage violations; seal verified | `evidence/historical/evaluation_results.json`, `evidence/historical/frozen/` |
| Explorer export | 101 data files, 21.2 MB raw; a second export was byte-identical; 34,494 CSV rows produced by the site's JavaScript matched the database on all 28 fields | `site/data/manifest.json`, `evidence/explorer/csv_verification.json` |
| Tests | **87 tests** passed in the PostgreSQL 18 CI job on 2026-10-26 ([run 40345956194](https://github.com/s2002kumar/fineprint/actions/runs/40345956194)); separate standard-library-only jobs run on Python 3.11 and 3.14. The count is a dated measurement, not an invariant. | `.github/workflows/ci.yml` |

## Observed but not recorded in an evidence file
- **Daily-update wall time.** The first application of the 2026-10-19 daily update took about 42 s end to end, and
  re-applying it about 19 s. Both were timed at the shell. The evidence files record only the ingest step.
- **Explorer export wall time.** About 21 s, timed at the shell on 2026-10-20.
- **Download wall time.** About 37 minutes with three parallel streams, timed at the shell.

## Assumed or not verified
- **Completeness of the 2023 label universe.** DailyMed's all-labels-on-a-date export was not obtained, and one label
  set's cutoff version could not be retrieved.
- **Rocky Mount's identity during 2023.** It rests on a 2015 facility filing and a 2022-10-13 registration record.
- **That every label is accurate.** fineprint reports what labels and registration files assert. It cannot detect a
  wrong DUNS or a missing establishment in a label.
- **That a documented manufacturing link implies supply exposure.** Not tested. Volume, inventory, alternative sites
  and substitution are outside the data.
- **An independent human audit.** Not performed. The 40/40 link audit was done by the AI assistant that built the
  project. [HUMAN_AUDIT_WORKSHEET.md](HUMAN_AUDIT_WORKSHEET.md) is the plan for a person to check a seeded sample.
- **Behavior on other machines with the full data.** The full pipeline was run on one Windows machine, twice (the
  reference run and the clean-clone reproduction). Linux has only run the test suite, in CI.
