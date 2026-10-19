#!/usr/bin/env bash
# Sets up AI KRISH on a Mac after you have cloned the repository.   Run:  bash scripts/setup-macos.sh
set -eu
cd "$(dirname "$0")/.."
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
say()  { printf '\n== %s\n' "$*"; }

command -v git  >/dev/null 2>&1 || fail "git not found. In Terminal run: xcode-select --install"
command -v node >/dev/null 2>&1 || fail "Node.js not found. Install the LTS version from https://nodejs.org, then run this again."
command -v npm  >/dev/null 2>&1 || fail "npm not found. Reinstall Node.js from https://nodejs.org"
major=$(node -p 'process.versions.node.split(".")[0]')
[ "$major" -ge 20 ] || fail "Node $(node -v) is too old. Install Node 20 or newer (the LTS) from https://nodejs.org"
[ -f package-lock.json ] || fail "package-lock.json is missing. Are you inside the AI KRISH folder?"

say "Installing dependencies (npm ci)"
npm ci

say "Environment file"
if [ -f .env.local ]; then
  echo ".env.local already exists. Leaving it alone."
else
  [ -f .env.example ] || fail ".env.example is missing."
  cp .env.example .env.local
  chmod 600 .env.local
  echo "Created .env.local from .env.example."
fi
if grep -qE 'your-|choose-a-long' .env.local; then
  echo "NOTE: .env.local still has placeholder values. Open it in a text editor and fill in your own keys."
  echo "      (Never paste keys into chat or commit this file.)"
fi

say "Done"
echo "Start the app:        npm run dev      then open http://localhost:3000"
echo "Production check:     npm run build && npm run start"
