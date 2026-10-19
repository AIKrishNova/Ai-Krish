# AI KRISH

A private, personal AI assistant: chat with streaming replies, voice in and out, photo and document questions, and saved chat history. Built with Next.js, Supabase (sign-in and chat history) and several AI providers behind server-side API routes.

> This repository is private. Keys never live here: they stay in `.env.local` on your computer and in your host's Environment Variables.

## Quick start

```bash
git clone git@github.com:<your-github-username>/ai-krish.git
cd ai-krish
bash scripts/setup-macos.sh          # Mac    (Windows: see INSTALL.md)
# edit .env.local and add your own keys, then:
npm run dev                          # http://localhost:3000
```

Full steps for every device: [INSTALL.md](INSTALL.md).

## What works where

| Device | How you use it | Works | Limits |
|---|---|---|---|
| Mac | Browser, installed web app, or run locally | Everything | Safari's "Add to Dock" needs a recent macOS and Safari; Chrome and Edge can install it on any supported Mac |
| Windows | Browser, installed web app (Chrome or Edge), or run locally | Everything | Needs Node 20+ only if you run it locally |
| iPhone / iPad | Safari, then Share, then Add to Home Screen | Chat, history, photos, documents, spoken replies | Speech recognition is less reliable on iOS. "Hey Krish" only listens while the page is open on screen. No background listening. It is a web app, not a native app |
| Android | Chrome, then menu, then Install app | Same as above | No background listening. It is a web app, not a native app |

Phones and tablets use the hosted web address (HTTPS). Microphone access in browsers needs HTTPS or `localhost`.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/setup-macos.sh` / `scripts/setup-windows.ps1` | Install dependencies and create `.env.local` on a new computer |
| `scripts/update.sh` | Pull the latest committed version safely |
| `scripts/backup.sh` | Secret scan, list unsaved work, optional push, snapshot without secrets |
| `scripts/check-secrets.sh` | Look for keys or env files before you commit |
| `scripts/check-env.sh` | Make sure `.env.example` lists every variable the code reads |

## Documents

[INSTALL.md](INSTALL.md) · [DEPLOYMENT.md](DEPLOYMENT.md) · [SECURITY.md](SECURITY.md) · [docs/AUTH.md](docs/AUTH.md)
