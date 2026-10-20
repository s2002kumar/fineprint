# fineprint — final release review (2026-10-20)

**Status:** locally validated release on branch `release-v1`. `main` is fast-forwarded to it and tagged
`v1.0.0`. **Nothing has been pushed.** Every number below comes from a committed evidence file.

## 1. Completed vs incomplete
| Area | Status |
|---|---|
| DST-00 – DST-04A (feasibility, national ingest, identity graph, CLI, historical preparation) | complete (earlier gates) |
| **DST-04B** historical evaluation | **complete.** Frozen, audited and seal-verified before unsealing. B3 NOT EVALUABLE |
| **DST-05** release (CI, docs, reproducibility) | **complete.** CI workflow written but **not yet executed on GitHub** (no push) |
| Privacy / history sanitization | **complete, local only.** Backup kept |
| **DST-06** incremental refresh (optional) | **complete, minimal.** Manual command; no scheduler, no deployment |
| Not built, by design | frontend, LLM, RxNorm, shortage prediction, substitutes, recurring automation |
| Not obtained | DailyMed all-labels-on-2023-07-18 export (needs your email); package-level pre-event shortage data |

## 2. Benchmark (Rocky Mount, labels published ≤ 2023-07-18; P = 65 validated warning NDCs)
| Cohort | Method | N | Recovered | Recall | List reduction |
|---|---|---|---|---|---|
| E (890) | B1 all Hospira `00409` | 890 | 63 | 0.969 | — |
| E | B2 injectables | 886 | 62 | 0.954 | 0.4% |
| E | **Graph (DIRECT Rocky Mount MANUFACTURE)** | **480** | **63** | **0.969** | **46.1%** |
| M (469, May 2023 FDA directory) | Graph vs B1 | 235 vs 469 | 63 vs 63 | 0.969 | 49.9% |

- **Panel-conditional recall is 1.0.** Every in-frame positive is DIRECT.
- **The 2 misses are sterile empty vials,** which have no drug SPL. B2 cannot reach the graph's recall at any list size.
- **Link audit:** 40/40 VERIFIED; DIRECT 20/20, with a Clopper–Pearson 95% lower bound of 0.83. **The auditor was the AI assistant, not a human.**
- **6 of the 63 recovered positives exist only through archival recovery** of retired labels (FDA SPL by document ID, and 2023 monthly archives read by HTTP Range).
- **After unsealing,** two disclosed *text-extraction-only* fixes repaired the PDF text layer (A5.1, A5.2). P was validated against the appendix's 65 rows. No method, cohort or metric changed.
- **Exploratory, post-hoc:** packages naming Rocky Mount as the sole site were listed at 57/306, against 6/174 for multi-site packages. This is a hypothesis only.

Full report: [docs/EVALUATION_REPORT.md](docs/EVALUATION_REPORT.md).

## 3. Ingestion, graph and query metrics
- **Release.** Release 2026-10-16: 6 parts, 17,979,089,637 bytes, every MD5 = advertised. Download resume was tested with an interruption at 318,767,104 bytes.
- **Ingest.**
  - 55,064/55,064 members, **0 failed**.
  - 23.1 min on the reference run and 11.0 min in the reproduction. Peak RSS 73 MB and 95 MB respectively. Database 532 MB after DST-01.
  - A crash, kill, MemoryError and resume test on real data gave fingerprints identical to a clean run. An idempotent re-run changed 0 rows.
- **Graph.**
  - 52,747 sets: 51,910 confirmed, 730 unconfirmed, 107 ambiguous, 0 unresolved. 2,311 sets ship with more than one version.
  - 80,508 products: DIRECT 30.6% · TENTATIVE 0.5% · UNKNOWN site 1.2% · no manufacture evidence 67.6% (reasons itemized).
  - Of 3,333 manufacturing DUNS, 2,562 (76.9%) resolve to a registered facility; 656 (19.7%) are not found.
  - 3,444 facilities (FEI) and 123,200 edges. Builds take 6–15 s and are rebuild-identical.
- **Queries.** 2.8–32 ms per lookup (medians of 5). `coverage` takes 0.73 s, and `evidence --raw` (re-reads the 3 GB part and verifies its hashes) 81 ms.
- **Refresh (real 2026-10-19 daily update, on a database copy).** 207 labels in 42 s: +80 / −89 / 0 modified / 624 carried-forward edges. Re-apply: 0 changes in 19 s.

## 4. Tests and CI
- **75 tests**, all passing with PostgreSQL 18 + psycopg 3.3.6. With the stdlib only, 55 pass and 20 database tests skip.
- **What they cover:**
  - streaming parser, archive safety, NDC rules;
  - real PostgreSQL ingest semantics, crash/resume fingerprint equality, idempotence, cross-part deduplication, injected MemoryError;
  - version selection, every identity state, an SQL = Python confidence mirror, misleading same-name products, PACK ≠ MANUFACTURE, missing establishment blocks, raw-XML evidence;
  - historical classification and normalization rules; refresh add/supersede/retract/re-apply;
  - repo guards against contacts and home paths.
- **The CI workflow** (`.github/workflows/ci.yml`: stdlib matrix on 3.11/3.14, plus PostgreSQL 18 service) is untested on GitHub until pushed.
- **Clean-clone reproduction** (`scripts/reproduce.sh`):
  - every DST-01 and graph table fingerprint, all 6 frozen files (byte-identical) and the evaluation results were **identical** to the reference;
  - 73/73 tests passed in the clone (before DST-06 added 2).

## 5. Reproduction
Start with `docs/REPRODUCIBILITY.md`. In short:
1. Run `pg_local.py init/start/createdb`.
2. Run `dst01_fetch_release.py`, `dst01_ingest.py`, `dst02_registration.py` and `dst02_build_graph.py`.
3. Query with `fp.py …`.

For exact reproduction of the reference build, the offline flags re-verify recorded inputs. `scripts/reproduce.sh` does all of it from a fresh clone.

## 6. Security and git history
- **Before:** five history-only blobs contained a home path or username, and all commits carried a personal email.
- **Backup.** A bundle of all refs plus a mirror clone is in `$FINEPRINT_DATA/backups/20261020T043746Z/`, outside the repo and OneDrive, 3.1 MB. It was restore-tested ref-for-ref and its SHA-256 recorded. **It has not been deleted.**
- **Rewrite** (`git filter-repo`, local):
  - the 5 blobs were sanitized;
  - all commits, and the tag, now carry `Sandeep Kumar <s2002kumar@users.noreply.github.com>`;
  - the remote URL was restored (filter-repo removes it). New commits use the same identity through repo-local config.
- **Integrity after the rewrite:**
  - the HEAD tree hash is unchanged (`ca7e01b6…` at the time), as is every frozen evaluation file's SHA-256 (freeze manifest `361e21ba…`);
  - the seal re-verified on the rewritten tag, and the evaluation results reproduce exactly apart from the recorded tag commit ID;
  - the old→new map is in `docs/history/COMMIT_ID_MAP.md`.
- **Final audit** (208 blobs, all refs): no credentials, no contact data, no home paths or username.
  - The only identity is the noreply address.
  - The remaining hits are pattern literals in guard and audit code, the CI file's throwaway service-container password, and old audit reports holding redacted placeholders.
  - Personal contact fields from FDA files never reach the database or the repo, and requests use a generic User-Agent.

## 7. Blockers, caveats and open research questions
- **Frame completeness is unproven.** The DailyMed date-archive export was not obtained, and 1 set's cutoff version (`99a0571d` v14) is unretrievable.
- **The 2023 identity** of Rocky Mount rests on 2015 and 2022 records; 2023 registration status is not established.
- **The outcome list** is a warehouse-affected low-inventory warning, not production truth. Flagged-but-unlisted packages (417) are not false positives.
- **The audit was AI-performed.** A human spot-check of `evidence/historical/frozen/audit_worksheet.md` is advisable.
- **National coverage is limited by the labels themselves.** 23% of products come from labels with no establishment block, and 19.7% of manufacturing DUNS have no FDA registration evidence in any snapshot.
- **Refresh limits:** updates must be applied in chronological order, documents added by updates have no `published_date`, and update archives are only briefly advertised.
- **Platform.** Verified on Windows 11 with Python 3.14 and PostgreSQL 18; Linux runs only through the (unexecuted) CI file.
- **Leftovers.** The local work databases `fineprint_repro`, `fineprint_refresh` and `fineprint_restart`, and the reproduction clone `$FINEPRINT_DATA/repro/fineprint` (which holds **pre-rewrite** history), still exist outside the repo.

## 8. Exact remaining actions before a public GitHub release
1. **Choose a license** and add `LICENSE`. None is included, because that choice is yours.
2. **Review** `docs/spec/` (the original spec; it mentions internal context) and `docs/history/`, and decide whether to keep them public. Earlier spec files remain in history.
3. **Approve the push** of `main`, the tags (`v1.0.0`, `dst04b-freeze`) and optionally the stage branches. This clone has never fetched `origin`, so check first whether the GitHub repository already holds commits. If it does, a non-fast-forward push would have to be resolved, never forced without your say.
4. **After pushing, confirm the GitHub Actions run passes**, and fix if not.
5. Optionally, have a human spot-check the audit worksheet.
6. Optionally, send DailyMed support the 2023-07-18 date-archive request, to test frame completeness.
7. **Decide what to delete:** the backup, the pre-rewrite reproduction clone and the scratch databases. Deletion needs your approval.

## 9. Suggested resume bullets (verified claims only)
- **National ingest.** Built a reproducible Python/PostgreSQL pipeline that ingests the full DailyMed prescription-label release: 55,064 SPL documents, 18 GB, at ≤95 MB peak memory with 0 failed documents. Crash/kill/resume recovery was verified by identical table fingerprints.
- **Provenance graph.** Designed a graph that links 80,508 drug products to FDA-registered facilities (DUNS → FEI → address) with DIRECT, TENTATIVE and UNKNOWN confidence. Every link is re-verifiable from an XPath-cited element in the raw archive. 76.9% of manufacturing DUNS resolve to a registered facility.
- **Historical evaluation.** Ran a pre-registered, leakage-controlled replay of the 2023 Pfizer Rocky Mount tornado. Using only pre-event labels, the method cut the candidate list by 46% (890 → 480) while recovering the same 63 of 65 warned package NDCs as the company-wide baseline.
- **Archival recovery.** Recovered retired 2023 label versions through FDA document-ID retrieval and HTTP Range reads of multi-GB archives (13 MB read of 8.7 GB). Those versions supplied 6 of the recovered positives.
- **Engineering.** Shipped an explainable CLI (≤32 ms lookups), an offline clean-clone reproduction with identical results, an idempotent incremental refresh, CI, and a git-history privacy audit and sanitization.
