# Reproducibility guide

Everything is stdlib Python ≥ 3.11 plus `psycopg[binary]==3.3.6` and PostgreSQL 18.

`$FINEPRINT_DATA` (default `~/fineprint-data`) holds the raw downloads (~18 GB), the database cluster
(~1.5 GB), the credentials and the run logs. It must be **outside** any synced folder and outside git.
Run every script as `python -I …`.

## 0. Environment
```sh
python -m venv $FINEPRINT_DATA/venv && $FINEPRINT_DATA/venv/bin/python -m pip install "psycopg[binary]==3.3.6"
python -I scripts/pg_local.py init      # project-owned cluster on 127.0.0.1:55432, generated password in $FINEPRINT_DATA/secrets
python -I scripts/pg_local.py start
python -I scripts/pg_local.py createdb fineprint fineprint_test
```
To use an existing server instead, set `FINEPRINT_DSN`; the tests then use `FINEPRINT_TEST_DB`.

## 1. Current national graph
| Step | Command | Measured (reference machine) |
|---|---|---|
| Download all parts (resumable) | `scripts/dst01_fetch_release.py --out evidence/dst01/release_manifest.json` | 17,979,089,637 bytes in ≈37 min (3 parallel × ≈3 MB/s); every part's MD5 = advertised |
| Ingest | `scripts/dst01_ingest.py --manifest evidence/dst01/release_manifest.json --db fineprint` | 55,064/55,064 members, 0 failures, 23.1 min, peak RSS 73 MB, database 532 MB |
| Registration evidence | `scripts/dst02_registration.py --db fineprint --out evidence/dst02/registration_manifest.json` | 5 dated FDA files |
| Graph | `scripts/dst02_build_graph.py --db fineprint --verify-rebuild` | 9.6–12.5 s per atomic rebuild (reference and clean-clone runs); rebuild fingerprints identical |
| Query | `scripts/fp.py product 0409-4346`, `… evidence 105515 --raw`, `… coverage` | 3–32 ms per lookup; coverage 0.7 s |

**Live sources move.** DailyMed replaces the full release, and FDA regenerates DECRS daily. To rebuild exactly
the reference graph, re-verify the recorded inputs without any network access:
```sh
python -I scripts/dst01_fetch_release.py --offline evidence/dst01/release_manifest.json --out /tmp/verified.json
python -I scripts/dst02_registration.py --db <db> --offline --out /tmp/registration.json
```

**Reference fingerprints** (natural keys only; any correct rebuild must match):

| Table | Rows | MD5 |
|---|---|---|
| spl_document | 55,064 | `04bf4b5d3b57f3742af9558f840c3e95` |
| organization_mention | 158,291 | `c69b6faf19eb80d3f19d7774b2e49447` |
| product | 88,501 | `f186be0f14782ab00747cb0d343e8dc0` |
| package | 233,934 | `d048095ddb44df6b44fb5e6a1e508004` |
| operation_assertion | 129,952 | `03ffb65cd00a45b8a4b4c782f882c437` |
| set_version_selection | 52,747 | `72501b8f199b1e2922572e7fd053ebd7` |
| duns_identity | 4,314 | `e33f31c51d86decd5d4ae89570f3a137` |
| facility | 3,444 | `1b80520b74caa184360d9a65203d2939` |
| operation_edge | 123,200 | `a301d92d3d87d4cebdada4aa4ebe35c2` |

## 2. Historical evaluation
All pre-cutoff sources are cached, with provenance, under `$FINEPRINT_DATA/raw/historical/`. They are listed
in `evidence/historical/historical_source_manifest.json`.
```sh
python -I scripts/hist_dst04a_prepare.py --config config/dst00_targets.json \
    --out evidence/historical/dst04a_candidates_draft.json --manifest-out evidence/historical/historical_source_manifest.json
python -I scripts/hist_dst04b_freeze.py --config config/dst00_targets.json --out-dir /tmp/freeze   # re-derive; never overwrite the seal
python -I scripts/hist_dst04b_unseal_and_score.py --out /tmp/evaluation_results.json             # refuses if the seal is broken
```
The re-derived freeze files must equal the committed ones byte for byte. The scores must equal
`evidence/historical/evaluation_results.json`.

## 3. One-command clean-clone check
```sh
PYTHON=python bash scripts/reproduce.sh <path-to-this-repo> $FINEPRINT_DATA/repro fineprint_repro
```
It runs the following and exits non-zero on any difference:
1. a fresh `git clone` and fresh venv;
2. offline input verification;
3. a clean ingest into a new database, the registration load and two graph builds;
4. the freeze re-derivation and scoring;
5. the full test suite;
6. a comparison of every fingerprint and frozen file with the reference.

**Measured clean-clone run (2026-10-20)** — `evidence/dst05/reproduction.json`:
- All 6 parts and the metadata file were re-verified offline.
- The fresh ingest processed 55,064/55,064 members with 0 failures in 662 s, at a peak RSS of 95 MB.
- Graph builds took 10.8 s and 12.5 s.
- **Every DST-01 and graph table fingerprint, all 6 frozen historical files (byte-identical) and the evaluation
  results were identical to the reference.** 73/73 tests passed in the clone.

## Optional: incremental refresh (DST-06)
```sh
# work on a copy so the release build stays the reference
psql -c "CREATE DATABASE fineprint_refresh TEMPLATE fineprint"      # or any equivalent
python -I scripts/dst06_refresh.py --db fineprint_refresh --update dm_spl_daily_update_10192026.zip --out /tmp/refresh.json
```
**Measured 2026-10-20** (`evidence/dst06/`):
- First pass: it loaded 207 prescription labels (ingest step 4.19 s) and applied 196 in-scope retractions.
  Edges: +80 / −89 / 0 modified / 624 carried forward.
- Second pass: 0 changes.
- End-to-end wall times of about 42 s and 19 s were timed at the shell; they are not in the evidence files.
- Updates are advertised on the DailyMed page only for a short window, and older ones disappear.

## Explorer data (`site/data/`)
```sh
python -I scripts/export_explorer.py --db fineprint            # writes site/data/ (about 21 s)
python -I scripts/export_explorer.py --db fineprint --verify   # a fresh export must equal the committed files byte for byte
python -I scripts/verify_explorer_csv.py --db fineprint        # browser CSV code (run under Node) vs independent SQL
python -I scripts/export_explorer.py --check                   # no database: files vs manifest checksums
python -I scripts/make_human_audit_worksheet.py                # regenerate the seeded human audit sample
node scripts/check_live_explorer.mjs <chrome> https://s2002kumar.github.io/fineprint/   # headless browser check of the deployed site
```
On the reference database, `--verify` reported all 101 data files identical. 34,494 CSV rows matched the graph on all
28 fields (`evidence/explorer/csv_verification.json`).

## 4. Tests and CI
- `python -I -m unittest discover -s tests -t .` ran **87 tests** against PostgreSQL 18 in CI on 2026-10-26. Without a database, PostgreSQL-dependent tests skip.
- With psycopg and a test database, the same command runs the full suite. It covers:
  - real ingest semantics and crash/kill/resume;
  - graph rules, CLI answers and historical rules;
  - the published site data;
  - the repo privacy guards.
- `.github/workflows/ci.yml` runs both against a PostgreSQL 18 service container. The full national download stays
  out of CI.
- `.github/workflows/pages.yml` re-checks the site data, then deploys `site/` to GitHub Pages.
