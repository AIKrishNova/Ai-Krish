# Installing AI KRISH

Pick the section for your device. You need your own keys (see "Environment file"). Never put keys in GitHub, chat, or screenshots.

## 1. Get the code (Mac or Windows)

The repository is private, so you must sign in to GitHub on that computer first. Either way works:

- **GitHub CLI (browser sign-in):** install from https://cli.github.com, run `gh auth login`, then `gh repo clone <your-github-username>/ai-krish`.
- **SSH key:** create a key on that computer, add its `.pub` file at GitHub > Settings > SSH and GPG keys, then `git clone git@github.com:<your-github-username>/ai-krish.git`.

Git for Windows includes Git Credential Manager, which opens a browser sign-in when you clone over HTTPS.

## 2. Mac

1. Install Node.js 20 or newer (the LTS) from https://nodejs.org and Git (`xcode-select --install`).
2. In Terminal: `cd ai-krish && bash scripts/setup-macos.sh`
3. Fill in `.env.local`.
4. `npm run dev`, then open http://localhost:3000

## 3. Windows

1. Install Git (https://git-scm.com/download/win) and Node.js 20 or newer (https://nodejs.org). Open a new PowerShell window.
2. `cd ai-krish`
3. `powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1`
4. Fill in `.env.local` in Notepad.
5. `npm.cmd run dev`, then open http://localhost:3000

## 4. iPhone and iPad

1. Open your hosted AI KRISH address in **Safari** (see DEPLOYMENT.md).
2. Sign in.
3. Tap Share, then **Add to Home Screen**.

Limits: it is a web app. Speech recognition on iOS is less reliable, "Hey Krish" only works while the page is open, and nothing listens in the background. A native iOS app would be a separate project.

## 5. Android

1. Open your hosted AI KRISH address in **Chrome**.
2. Sign in.
3. Tap the menu (three dots), then **Install app** (or **Add to Home screen**).

Limits: same as iPhone. Allow the microphone when asked. A Trusted Web Activity or native wrapper could be added later if you need a Play Store style app.

## Environment file

`.env.local` is created from `.env.example` by the setup scripts. Fill in at least:

- `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` (Supabase > Project Settings > API; these two are public by design)
- one AI provider key, for example `GEMINI_API_KEY`
- `APP_PASSCODE` (a long passcode)

Keep a copy of these values in a password manager. `.env.local` is never in GitHub, which means a new computer needs them re-entered.

## Run a production build locally

```bash
npm run build
npm run start
```

## Update to the latest version

```bash
bash scripts/update.sh          # add --build to also run a production build
```

It refuses to run if you have uncommitted changes.

## Restore on a replacement computer

1. Install Git and Node (steps 1 to 3 above).
2. Clone the repository and run the setup script.
3. Re-create `.env.local` from your password manager.
4. `npm run dev` and sign in. Your chats come back from the database automatically if "Save chat history to database" is on.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Node ... is too old` | Install Node 20 or newer from https://nodejs.org |
| Sign-in page loops or errors | Check the two Supabase values in `.env.local`, then restart `npm run dev` |
| Microphone does not work | Browsers need HTTPS or `localhost`. A phone opening `http://192.168...` will not get the mic |
| History says tables are missing | Run `supabase/chat-sync.sql` once in Supabase > SQL Editor |
| `npm ci` fails | Delete `node_modules`, make sure `package-lock.json` is present, run again |
| Windows blocks the script | Use the `-ExecutionPolicy Bypass` command shown above |
| Verification email link says "open in same browser" | Open the link in the browser where you signed up (see docs/AUTH.md) |
