#!/usr/bin/env bash
# Safe backup of AI KRISH.   bash scripts/backup.sh [--push] [output-folder]
#   1. scans for secrets (stops if any are found)
#   2. lists uncommitted work, which is NOT yet backed up on GitHub
#   3. with --push: pushes the current branch to GitHub (never forced)
#   4. writes a .tar.gz snapshot WITHOUT .env files, node_modules or .next
# Your .env.local is deliberately NOT included anywhere. Keep its values in a password manager.
set -eu
cd "$(dirname "$0")/.."
PUSH=0; OUT="$HOME/Desktop"
for a in "$@"; do case "$a" in --push) PUSH=1;; *) OUT="$a";; esac; done
bash scripts/check-secrets.sh || { echo "Backup stopped: fix the problem above first."; exit 1; }
echo
echo "== Uncommitted work (commit it to back it up on GitHub) =="
if [ -n "$(git status --short)" ]; then git status --short | head -30; else echo "none"; fi
if [ "$PUSH" -eq 1 ]; then
  git remote get-url origin >/dev/null 2>&1 || { echo "No 'origin' remote yet."; exit 1; }
  echo; echo "== Pushing $(git rev-parse --abbrev-ref HEAD) =="; git push
fi
mkdir -p "$OUT"
FILE="$OUT/ai-krish-snapshot-$(date +%Y-%m-%d-%H%M).tar.gz"
tar --exclude='./node_modules' --exclude='./.next' --exclude='./.vercel' --exclude='./.git' --exclude='.env*' \
    -czf "$FILE" -C . .
echo; echo "Snapshot written: $FILE"
echo "Reminder: .env.local is not in GitHub or in this snapshot. Store its values in a password manager."
