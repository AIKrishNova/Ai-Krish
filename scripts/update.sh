#!/usr/bin/env bash
# Brings this copy up to date with GitHub.   bash scripts/update.sh [--build]
# Refuses to run if you have uncommitted work, and never overwrites it.
set -eu
cd "$(dirname "$0")/.."
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
git remote get-url origin >/dev/null 2>&1 || fail "No 'origin' remote is set."
if ! git diff --quiet || ! git diff --cached --quiet; then
  fail "You have uncommitted changes. Commit them (or copy them somewhere safe) first."
fi
echo "== Fetching"
git fetch origin
echo "== Fast-forwarding (no merge commits, no overwriting)"
git pull --ff-only
echo "== Installing dependencies"
npm ci
if [ "${1:-}" = "--build" ]; then echo "== Building"; npm run build; fi
echo
echo "Up to date. Restart the app if it is running. Checking for new environment variables:"
bash scripts/check-env.sh || true
