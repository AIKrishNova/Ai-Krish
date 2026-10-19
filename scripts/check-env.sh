#!/usr/bin/env bash
# Compares the environment variable names the code reads with the names listed in .env.example.
# A name counts as documented if it appears as NAME=... or as a commented "# NAME=...".
#   bash scripts/check-env.sh            report only (always exits 0)
#   bash scripts/check-env.sh --strict   exit 1 if anything is missing
set -u
cd "$(dirname "$0")/.."
[ -f .env.example ] || { echo "No .env.example found."; exit 1; }
dirs=""
for d in app lib scripts; do [ -d "$d" ] && dirs="$dirs $d"; done
[ -f proxy.ts ] && dirs="$dirs proxy.ts"
used=$( {
  # shellcheck disable=SC2086
  grep -rhoE 'env\.[A-Z][A-Z0-9_]+' $dirs 2>/dev/null | sed 's/^env\.//'
  # shellcheck disable=SC2086
  grep -rhoE '(keyEnv|modelEnv): *"[A-Z][A-Z0-9_]+"' $dirs 2>/dev/null | sed -E 's/.*"([A-Z0-9_]+)"/\1/'
} | sort -u | grep -vE '^(NODE_ENV|CI|NEXT_RUNTIME|VERCEL[A-Z_]*)$' || true)
documented=$(grep -oE '^#? *[A-Z][A-Z0-9_]+=' .env.example | sed -E 's/^# *//; s/=$//' | sort -u)
missing=$(comm -23 <(printf '%s\n' "$used") <(printf '%s\n' "$documented") | sed '/^$/d')
if [ -n "$missing" ]; then
  echo "Used in code but not listed in .env.example:"
  printf '  %s\n' $missing
  [ "${1:-}" = "--strict" ] && exit 1
  echo "(Add them to .env.example as placeholders, or as commented lines if optional.)"
else
  echo "OK: every variable the code reads is listed in .env.example."
fi
exit 0
