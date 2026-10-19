#!/usr/bin/env bash
# One-time repository tidy-up. Changes NOTHING unless you add --apply.
#   bash scripts/prepare-repo.sh            show what would change
#   bash scripts/prepare-repo.sh --apply    do it
# It never deletes files from your disk, never rewrites history, never commits or pushes.
set -eu
cd "$(dirname "$0")/.."
APPLY=0; [ "${1:-}" = "--apply" ] && APPLY=1
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "Run this inside the project (a git repository)."; exit 1; }
run() { if [ "$APPLY" -eq 1 ]; then "$@"; fi; }
say() { if [ "$APPLY" -eq 1 ]; then echo "DONE   $*"; else echo "WOULD  $*"; fi; }
MARK="# --- AI KRISH repo additions ---"
for t in gitignore-additions.txt env.example README.md; do
  [ -f "scripts/templates/$t" ] || { echo "Missing scripts/templates/$t. Re-extract the setup bundle."; exit 1; }
done

if grep -qF "$MARK" .gitignore 2>/dev/null; then
  echo "SKIP   .gitignore already has the AI KRISH block"
else
  say "append the AI KRISH block to .gitignore (keeps .env.example, ignores backups, zips, logs)"
  run sh -c 'printf "\n" >> .gitignore; cat scripts/templates/gitignore-additions.txt >> .gitignore'
fi

if [ -f .env.example ]; then
  echo "SKIP   .env.example already exists (left untouched)"
else
  say "create .env.example from the template (placeholders only)"
  run cp scripts/templates/env.example .env.example
fi

if [ -f README.md ] && grep -q 'bootstrapped with \[`create-next-app`\]' README.md; then
  say "replace the default Next.js README.md (old copy saved as README.md.bak-before-readme)"
  run sh -c 'cp README.md README.md.bak-before-readme && cp scripts/templates/README.md README.md'
elif [ -f README.md ]; then
  echo "SKIP   README.md is not the default template (left untouched)"
else
  say "create README.md"
  run cp scripts/templates/README.md README.md
fi

list=$(git ls-files | grep -E '(\.bak($|-[^/]*$))|\.old\.txt$|\.zip$' || true)
if [ -n "$list" ]; then
  n=$(printf '%s\n' "$list" | wc -l | tr -d ' ')
  say "stop tracking $n backup/zip files in git (they stay on your disk; old versions remain in history)"
  printf '%s\n' "$list" | sed 's/^/         /'
  if [ "$APPLY" -eq 1 ]; then printf '%s\n' "$list" | while IFS= read -r f; do git rm --cached -q -- "$f"; done; fi
else
  echo "SKIP   no tracked backup or zip files"
fi

[ "$APPLY" -eq 1 ] || { echo; echo "Nothing was changed. Run again with --apply to do it."; }
