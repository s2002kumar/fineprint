#!/usr/bin/env bash
# Clean-environment reproduction from already-downloaded, hash-verified inputs (no network).
#   scripts/reproduce.sh <repo-to-clone> <work-dir> [db-name]
# Creates a fresh clone + venv in <work-dir>, rebuilds a new database from $FINEPRINT_DATA raw inputs,
# re-runs the historical freeze and scoring, and compares everything with the reference build.
set -euo pipefail
SRC="$1"; WORK="$2"; DB="${3:-fineprint_repro}"
PY_BOOT="${PYTHON:-python}"
mkdir -p "$WORK"
rm -rf "$WORK/fineprint" "$WORK/venv"
git clone --quiet "$SRC" "$WORK/fineprint"
"$PY_BOOT" -m venv "$WORK/venv"
VPY="$WORK/venv/Scripts/python.exe"; [ -x "$VPY" ] || VPY="$WORK/venv/bin/python"
"$VPY" -m pip install --quiet --disable-pip-version-check "psycopg[binary]==3.3.6"
cd "$WORK/fineprint"
T="$WORK/out"; mkdir -p "$T"
log() { echo "[$(date -u +%H:%M:%S)] $*"; }

log "createdb $DB"
"$VPY" -I scripts/pg_local.py createdb "$DB"
log "verify raw release inputs offline"
"$VPY" -I scripts/dst01_fetch_release.py --offline evidence/dst01/release_manifest.json --out "$T/release_verified.json"
log "ingest (clean)"
"$VPY" -I scripts/dst01_ingest.py --manifest evidence/dst01/release_manifest.json --db "$DB" --reset --out "$T/ingest.json"
log "registration evidence (offline)"
"$VPY" -I scripts/dst02_registration.py --db "$DB" --offline --out "$T/registration.json"
log "graph build x2"
"$VPY" -I scripts/dst02_build_graph.py --db "$DB" --out "$T/graph_build.json" --verify-rebuild
log "historical freeze + scoring from cached pre-cutoff sources"
"$VPY" -I scripts/hist_dst04b_freeze.py --config config/dst00_targets.json --out-dir "$T/frozen_repro"
"$VPY" -I scripts/hist_dst04b_unseal_and_score.py --out "$T/evaluation_results.json"
log "test suite in the clean clone"
FINEPRINT_TEST_DB="${FINEPRINT_TEST_DB:-fineprint_test}" "$VPY" -I -m unittest discover -s tests -t . > "$T/tests.log" 2>&1 \
  && log "tests OK" || { log "tests FAILED"; tail -20 "$T/tests.log"; exit 1; }
log "compare with reference"
F=evidence/historical/frozen
"$VPY" -I scripts/repro_compare.py --db-a fineprint --db-b "$DB" --out "$T/compare.json" \
  --files "$SRC/$F" "$T/frozen_repro" cohort_E.json cohort_M.json documents.json identity.json \
          audit_sample.json freeze_summary.json
"$VPY" -I -c "
import json,sys
a=json.load(open(r'$SRC/evidence/historical/evaluation_results.json',encoding='utf-8'))
b=json.load(open(r'$T/evaluation_results.json',encoding='utf-8'))
same = a == b
print('evaluation_results identical:', same); sys.exit(0 if same else 1)"
log "done"
