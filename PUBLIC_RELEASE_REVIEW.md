# Public release review — fineprint v1.1.0 (2026-10-20)

| | |
|---|---|
| Repository | <https://github.com/s2002kumar/fineprint> (public; license detected by GitHub as MIT) |
| Explorer (deployed and verified) | <https://s2002kumar.github.io/fineprint/> |
| Release identifier | tag **`v1.1.0`** on the commit that adds this file |
| Earlier tags, unchanged | `v1.0.0` → `24d22ba` (the original local release, not retagged); `dst04b-freeze` → `8ddfa24` (frozen evaluation inputs) |

Everything listed as verified was checked by commands run on 2026-10-20. Items not verified are listed under "Known
issues" and "Still needs a human".

## 1. Publication
- **Remote state before pushing.** The GitHub repository already existed. It was public and empty: `git ls-remote`
  returned no refs, and the API reported size 0 with no branches, tags, releases or Pages site. There was no
  unexpected work to protect.
- **Pushed, with no force push at any point:**
  - `main`;
  - the existing tags `v1.0.0` and `dst04b-freeze`.

  The local work branches (`release-v1`, `dst-*`) were not pushed.
- **Commits after `v1.0.0`:**
  1. `3438df2`: MIT license for the code and `NOTICE.md` for third-party data terms. Internal documents were removed
     from the tree: gate reports, commit-ID map, implementation spec, progress log, v1.0.0 review and history-rewrite
     script.
  2. `f3f3a8f`: CI fix. The first GitHub run failed before any job started, because the `runner` context is not
     allowed in job-level `env` (confirmed with actionlint).
  3. `1b2c59c`: the Facility Evidence Explorer and its data exports; the README rewrite; the case study, metrics,
     example queries and human audit worksheet.
  4. `a9a6739`: explorer search also matches registered addresses; headless-browser check script; screenshots of the
     deployed site.
  5. The `v1.1.0` commit: this review, the browser-check evidence and a refreshed history audit.
- **Repository settings changed:**
  - description and homepage (the explorer URL);
  - GitHub Pages enabled with GitHub Actions as the source.

## 2. Verification
| Check | Result | Evidence or command |
|---|---|---|
| Public repo loads | yes; default branch `main`; license MIT | GitHub API |
| History and tree privacy | 356 blobs on every local ref: no database password; only commit identity is the GitHub noreply address; no home path, username or institution string. HEAD hits are pattern literals in guard and audit code plus the CI service container's throwaway password | `evidence/security/git_history_audit.json`; `scripts/audit_git_history.py` |
| No DB files, venvs or raw archives tracked | none; 253 tracked files, the largest a 2.5 MB explorer data shard | `git ls-files` |
| Code license separate from data terms | `LICENSE` (MIT, code only); `NOTICE.md` (NLM terms incl. "Courtesy of the U.S. National Library of Medicine" and the currency notice, checked against nlm.nih.gov on 2026-10-20; FDA public domain; psycopg LGPL-3.0, optional and not vendored) | `LICENSE`, `NOTICE.md` |
| Tests | 84/84 pass locally on PostgreSQL 18. With the stdlib only, 64 pass and 20 skip | `python -I -m unittest discover -s tests -t .` |
| CI including integration tests | `ci` passed on `a9a6739` (run 39489434144). The PostgreSQL job ran all tests with 0 skipped | GitHub Actions |
| Explorer deployed | `pages` passed (run 39489433883). Live `manifest.json` is byte-identical to the repo, and 7/7 sampled live data files match their SHA-256 | GitHub Actions; download and hash |
| Explorer works in a browser | headless Chrome on the live URL: search finds Rocky Mount and McPherson; Rocky Mount lists 183 MANUFACTURE rows; the case-study page loads; 0 page exceptions | `evidence/explorer/live_browser_check.json` (`scripts/check_live_explorer.mjs`) |
| CSV exports match graph records | 34,494 CSV rows produced by the site's own JavaScript matched independent SQL on all 28 fields, with 0 missing or extra rows. The CSV produced by the live "Download CSV" button equals those verified rows | `evidence/explorer/csv_verification.json`, `…/live_browser_check.json` |
| Export is deterministic and matches the reference graph | a fresh export is byte-identical (101/101 files); table fingerprints in the manifest equal the reference values in `docs/REPRODUCIBILITY.md` | `scripts/export_explorer.py --verify` |
| Source links resolve | DailyMed label pages, version ZIPs and history JSON return 200. FDA XML by document ID matched the ingested XML's SHA-256 for all 24 documents checked (20 worksheet samples, 3 Rocky Mount rows, 1 example query) | download and hash |
| Historical evaluation unchanged and reproducible | the 6 frozen files and `FREEZE_MANIFEST` are identical to the `dst04b-freeze` tag; `evaluation_results.json` SHA-256 `749b4bb3…` unchanged. Re-scoring through the seal-verifying script gives identical cohorts and metrics; only `seal.tag_commit` differs (see known issue 2) | `scripts/hist_dst04b_unseal_and_score.py --out <tmp>` |
| README claims match code and reports | every number traced to an evidence file; corrections below | §3 |

## 3. Corrections made during this review
- **Archival recovery.** "6 of the 63 recovered NDCs exist only through archival recovery" was wrong. The correct
  figure is **5**: `00409-4928-34` is also DIRECT in a set that is still searchable. Fixed in
  `docs/EVALUATION_REPORT.md`, with a dated note. No metric changes. The v1.0.0 review at the `v1.0.0` tag still
  carries the old wording.
- **Refresh wall times.** The daily-update times (42 s, 19 s) are not in any evidence file. They are now labeled as
  shell timings, and the documents cite the recorded 4.19 s ingest step instead.
- **Lookup latency.** The README now gives 3–32 ms, as the benchmark file records.
- **Audit wording.** The pre-unsealing link audit's "independent extraction" is now described as an independent code
  path written by the same AI author, not an independent reviewer.

## 4. Known issues
1. **Internal planning documents remain in git history** at commits up to `v1.0.0`:
   - the original research log and decisions (`docs/spec/03_…`);
   - the Claude Code task cards and kickoff note (`docs/spec/04_…`, `CLAUDE_CODE_KICKOFF.txt`);
   - the gate reports and the v1.0.0 review.

   They mention another paused project, "Career HQ" and interview priorities. They contain no credentials or contact
   data. Removing them would mean rewriting history and retagging `v1.0.0`, which this release was told not to do.
2. **`evidence/historical/evaluation_results.json` records `seal.tag_commit` as `16245583…`.** That is the freeze
   commit's ID before the privacy rewrite; the published tag points to `8ddfa24…`. The file is frozen by hash, so it
   is not edited. The old→new map is in `docs/history/COMMIT_ID_MAP.md` at tag `v1.0.0`.
3. **Evidence IDs (`assertion_pk`) are database row keys.** A fresh ingest can number them differently. The set ID,
   version and XML location are the portable reference.
4. **The explorer is a dated snapshot** (DailyMed 2026-10-16, FDA registration files 2026-10-19). It states that it
   does not reflect the most current/accurate data available from NLM. Nothing refreshes it automatically.
5. **National explorer pages list MANUFACTURE assertions only.** Other operations are counted, and listed only for
   the two examples. Tables show the first 500 rows; the CSV has all of them.
6. **Mobile layout was tested in a 390 px frame in headless Chrome only,** not on a physical phone. There has been no
   screen-reader test.
7. **The full 18 GB pipeline has run only on Windows** (reference and clean-clone runs). Linux runs the test suite in
   CI. GitHub reports that `ubuntu-latest` is moving to Ubuntu 26; runs on 2026-10-20 passed.
8. **The CSV download was verified by capturing the Blob the button creates.** Headless Chrome did not write the file
   to disk, so the saved-file path itself was not exercised.

## 5. Still needs a human
- **Run the independent audit.** Work through [docs/HUMAN_AUDIT_WORKSHEET.md](docs/HUMAN_AUDIT_WORKSHEET.md): 20
  current links, 11 historical packages and 2 identities, each with public source URLs. Record verdicts in
  `docs/human_audit_verdicts.csv`.
  - No human has audited any record yet. The existing 40/40 audit was done by the AI assistant that built the
    project.
  - An automated pre-check confirmed only that the worksheet's 20 current-link URLs, hashes and XML locations are
    correct. It is not an audit.
- **Read the README and the case study** for accuracy and tone before sharing them.
- **Look at the explorer on a real phone** and with a screen reader.
- **Optional:** ask DailyMed support for the all-labels-on-2023-07-18 archive to test frame completeness.
- **Decide what to delete locally.** Nothing was deleted. These remain:
  - the pre-rewrite backup in `$FINEPRINT_DATA/backups/20261020T043746Z/`;
  - the scratch databases `fineprint_repro`, `fineprint_refresh` and `fineprint_restart`;
  - the clean-clone directory `$FINEPRINT_DATA/repro/fineprint`, which holds pre-rewrite history;
  - the screenshot captures in `$FINEPRINT_DATA/tmp-shots/`;
  - the local branches `release-v1` and `dst-*`.

Work stopped after this release. No forecasting, substitution, alerting, RxNorm or LLM extraction was built.
