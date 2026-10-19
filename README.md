# fineprint

**Which factory actually makes your medicine?**

Status: **DST-00 feasibility spike complete, awaiting review.** See [feasibility_report.md](feasibility_report.md).
Nothing has been ingested nationally yet; there is no database or CLI.

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
