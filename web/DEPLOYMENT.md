# Deployment

## Architecture

```
iPhone / Android / Mac / Windows browser or installed web app
        |  HTTPS
        v
Hosted Next.js app (Vercel)  --- API routes hold the AI keys (server only)
        |                \
        v                 v
AI providers          Supabase (sign-in + chat history, row-level security)

GitHub (private repo) = source code only. It does not serve the app.
```

A private GitHub repository does **not** make the deployed website private. Anyone who can reach the hosted address can see the login page. What protects your data is the Supabase sign-in (every API route requires a verified session, see docs/AUTH.md) plus, optionally, Vercel Deployment Protection.

## What runs where

- **Browser:** UI, voice, camera. Only `NEXT_PUBLIC_*` values (the Supabase URL and publishable key) are visible here, by design.
- **Server (API routes):** AI provider keys, rate limits, input validation, auth checks. Keys are read from environment variables and never sent to the browser.
- **Supabase:** accounts and the `chats` and `user_settings` tables (`supabase/chat-sync.sql`).

## Environment variables on the host

Set the same names as `.env.example` in your host's dashboard (Vercel > Project > Settings > Environment Variables). `NEXT_PUBLIC_*` values are baked in at build time, so set them before building. Check names any time with `bash scripts/check-env.sh`.

## Supabase settings

Authentication > URL Configuration: set the Site URL to your hosted address and add redirect URLs for it and for `http://localhost:3000/**` (details in docs/AUTH.md).

## Security features in the app

- HTTPS: provided by the host.
- Authentication: Supabase Auth with email verification; `proxy.ts` and `requireUser()` enforce it.
- Input validation and size limits: upload and request limits are configurable (see `.env.example`).
- Rate limiting: in-memory counters in the server code. On serverless hosting each instance counts separately, so treat it as a safety net, not a hard global limit.
- CORS: the app calls its own API from the same address, so no cross-origin access is enabled. If you ever host the frontend separately, add an explicit allow-list for that one address only.

## Before any change to hosting

Nothing here deploys anything. Moving hosts, connecting GitHub to a host, enabling paid plans or making a deployment public needs your explicit decision first. Check the host's current free-tier limits before relying on them.

## Optional later work

- A desktop app wrapper (Tauri or Electron) for Mac and Windows.
- A Trusted Web Activity or native wrapper for Android.
- A native iOS app if you need background voice features that web apps cannot do.
- iOS safe-area handling (`viewport-fit=cover` and padding) if content touches the notch or home bar on your iPhone.

## Backup and restore

- Code: committed and pushed to the private GitHub repo (`bash scripts/backup.sh --push`).
- Keys: in a password manager. Not in GitHub.
- Chats and settings: in Supabase. Export or back them up from the Supabase dashboard if you need an extra copy.
- Restore steps: see INSTALL.md.
