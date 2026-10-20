# fineprint

**Which factory actually makes your medicine?**

Status: **DST-02/03/04A complete, awaiting review.** See [DST_02_03_04A_REVIEW.md](DST_02_03_04A_REVIEW.md)
(earlier: [dst01_ingestion_report.md](dst01_ingestion_report.md), [feasibility_report.md](feasibility_report.md)).

## Query the current graph
```sh
python -I scripts/dst02_registration.py --db fineprint --out evidence/dst02/registration_manifest.json
python -I scripts/dst02_build_graph.py --db fineprint --out evidence/dst02/graph_build.json --verify-rebuild
python -I scripts/fp.py product 0409-4346            # manufacturing sites: DIRECT / TENTATIVE / UNKNOWN
python -I scripts/fp.py facility 093132819           # products made at a DUNS (or FEI:1021343)
python -I scripts/fp.py compare 093132819 030606222 --labeler 141588017
python -I scripts/fp.py evidence 105515 --raw        # exact source, re-read from the archive
python -I scripts/fp.py coverage
```
Answers describe the **current** DailyMed release and FDA registration file only, never a historical state.

## Reproduce DST-01 (current national ingest)
Needs PostgreSQL 18 binaries and `psycopg[binary]==3.3.6` in a venv. `$FINEPRINT_DATA` defaults to
`~/fineprint-data` and must be outside any synced folder (≈18 GB raw + ≈1.5 GB database).

```sh
python -I scripts/pg_local.py init && python -I scripts/pg_local.py start   # project cluster, 127.0.0.1:55432
python -I scripts/pg_local.py createdb fineprint fineprint_test
python -I scripts/dst01_fetch_release.py --out evidence/dst01/release_manifest.json   # resumable, MD5-verified
python -I scripts/dst01_ingest.py --manifest evidence/dst01/release_manifest.json --db fineprint \
    --out evidence/dst01/ingest_run.json                                             # idempotent; re-run to resume
python -I scripts/dst01_coverage.py --db fineprint --out evidence/dst01/coverage.json
python -I -m unittest discover -s tests -t .                                         # DB tests use fineprint_test
```
Set `FINEPRINT_DSN` to use another PostgreSQL server instead of the project cluster.

- Spec: [docs/spec/](docs/spec/)
- Pre-registered historical frame method: [docs/historical_panel_plan.md](docs/historical_panel_plan.md)
- Evidence: [evidence/dst00/](evidence/dst00/), merged in [source_manifest.json](source_manifest.json)

## Reproduce DST-00
Stdlib-only Python ≥ 3.11. Raw downloads go to `$DATA`, which must be **outside the repo**
(part 6 alone is 1.9 GB). Every script is safe to run under `python -I`.

```sh
python -I -m unittest discover -s tests -t .                      # 38 tests, real + synthetic fixtures
python -I scripts/dst00_historical.py --config config/dst00_targets.json --data-dir $DATA/hist \
    --out evidence/dst00/historical_spl.json --fixtures tests/fixtures/historical
python -I scripts/dst00_identity.py --config config/dst00_targets.json --data-dir $DATA/identity \
    --out evidence/dst00/identity_evidence.json
python -I scripts/dst00_fetch_part.py --part dm_spl_release_human_rx_part6.zip --data-dir $DATA/bulk \
    --out evidence/dst00/bulk_part6_download.json
python -I scripts/dst00_shard_stream.py --zip $DATA/bulk/bulk/dm_spl_release_human_rx_part6.zip \
    --advertised evidence/dst00/bulk_part6_download.json --duns-index $DATA/identity/decrs_current/duns_index.json \
    --records $DATA/bulk/part6_records.jsonl --out evidence/dst00/bulk_shard_part6.json
python -I scripts/dst00_bulk_probe.py --data-dir $DATA/probe --sample-per-part 25 --seed fineprint-dst00 \
    --duns-index $DATA/identity/decrs_current/duns_index.json --out evidence/dst00/bulk_probe.json
python -I scripts/dst00_frame_pilot.py --config config/dst00_targets.json --data-dir $DATA/pilot \
    --out evidence/dst00/frame_pilot.json
python -I scripts/build_manifest.py --evidence evidence/dst00 --data-dir $DATA/bulk --out source_manifest.json
```

Live sources change: a re-run against a newer DailyMed release produces different counts and hashes.
That is expected, and it is why every run records its own manifest.

Data: DailyMed SPL documents (NLM) and FDA files are U.S. government works. Registration files
also name individual contacts; fineprint never copies those fields, and the two facility-filing fixtures
are derived copies with `contactParty` removed (original hashes are in the evidence).
