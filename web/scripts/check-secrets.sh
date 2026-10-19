#!/usr/bin/env bash
# Looks for key-shaped text and env files that must never be committed.
# Prints FILE NAMES only, never the matching text.
#   bash scripts/check-secrets.sh             check the working tree (tracked + new, non-ignored files)
#   bash scripts/check-secrets.sh --history   also check every commit in git history
set -u
cd "$(dirname "$0")/.."
PAT='AIza[0-9A-Za-z_-]{20,}|sk-[A-Za-z0-9_-]{20,}|gsk_[A-Za-z0-9]{20,}|csk-[A-Za-z0-9]{20,}|nvapi-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|eyJ[A-Za-z0-9_-]{30,}\.[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----'
bad=0

echo "== env files that should not be tracked =="
tracked_env=$(git ls-files | grep -E '(^|/)\.env' | grep -vE '\.env\.example$' || true)
if [ -n "$tracked_env" ]; then echo "$tracked_env"; bad=1; else echo "none"; fi

echo "== key-shaped text in the working tree =="
hits=$(git grep -I -l --untracked -E "$PAT" -- . ':!package-lock.json' 2>/dev/null || true)
if [ -n "$hits" ]; then echo "$hits"; bad=1; else echo "none"; fi

if [ "${1:-}" = "--history" ]; then
  echo "== env files ever committed =="
  ever=$(git log --all --name-only --pretty=format: | grep -E '(^|/)\.env' | grep -vE '\.env\.example$' | sort -u || true)
  if [ -n "$ever" ]; then echo "$ever"; bad=1; else echo "none"; fi
  echo "== key-shaped text anywhere in history =="
  revs=$(git rev-list --all)
  if [ -n "$revs" ]; then
    # shellcheck disable=SC2086
    h=$(git grep -I -l -E "$PAT" $revs -- . ':!package-lock.json' 2>/dev/null | sed 's/^[0-9a-f]*://' | sort -u || true)
  else h=""; fi
  if [ -n "$h" ]; then echo "$h"; bad=1; else echo "none"; fi
fi

if [ "$bad" -ne 0 ]; then
  echo
  echo "FOUND POSSIBLE SECRETS. Do not push. Remove them, then replace (rotate) the real key at its provider."
  exit 1
fi
echo "OK: nothing found."
