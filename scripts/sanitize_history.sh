#!/usr/bin/env bash
# Controlled LOCAL history sanitization (never pushes). Steps:
#   1. full backup (bundle of every ref + mirror clone) outside the repo, verified by restoring it;
#   2. git-filter-repo: replace personal path/username fragments in blobs (rules file kept OUTSIDE the
#      repo because it necessarily names what it removes) and set a privacy-safe author/committer/tagger;
#   3. restore the remote URL that filter-repo removes; record old->new commit IDs.
#   scripts/sanitize_history.sh <backup-root> <replacements-file> <noreply-email> <filter-repo-exe>
set -euo pipefail
ROOT="$1"; RULES="$2"; EMAIL="$3"; FR="$4"
[ -z "$(git status --porcelain)" ] || { echo "working tree not clean"; exit 1; }
TS=$(date -u +%Y%m%dT%H%M%SZ); B="$ROOT/$TS"; mkdir -p "$B"
REMOTE=$(git remote get-url origin 2>/dev/null || true)

git bundle create "$B/fineprint-all-refs.bundle" --all
git bundle verify "$B/fineprint-all-refs.bundle" > "$B/bundle-verify.txt" 2>&1
git clone --quiet --mirror . "$B/fineprint-mirror.git"
git for-each-ref --format='%(objectname) %(refname)' > "$B/refs-before.txt"
git log --all --format='%H' > "$B/commits-before.txt"
# restore test: a clone from the bundle must reproduce every ref exactly
git clone --quiet --mirror "$B/fineprint-all-refs.bundle" "$B/restore-test.git"
( cd "$B/restore-test.git" && git for-each-ref --format='%(objectname) %(refname)' ) > "$B/refs-restored.txt"
diff <(sed 's#refs/remotes/origin/#refs/heads/#' "$B/refs-before.txt" | grep -v ' refs/remotes/' | sort) \
     <(grep -v ' refs/remotes/' "$B/refs-restored.txt" | sort) > /dev/null || { echo "backup restore test FAILED"; exit 1; }
rm -rf "$B/restore-test.git"
sha256sum "$B/fineprint-all-refs.bundle" > "$B/SHA256SUMS"
echo "backup verified: $B"

"$FR" --force --replace-text "$RULES" \
  --email-callback "return b'$EMAIL'" --name-callback "return b'Sandeep Kumar'"
[ -n "$REMOTE" ] && git remote add origin "$REMOTE"
cp .git/filter-repo/commit-map "$B/commit-map.txt"
git for-each-ref --format='%(objectname) %(refname)' > "$B/refs-after.txt"
echo "rewrite done; backup + commit map in $B"
