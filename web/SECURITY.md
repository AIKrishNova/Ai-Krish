# Security

## Rules
- Never commit `.env.local`, API keys, tokens, passwords or private keys. Only `.env.example` (placeholders) is committed.
- Keys stay on the server. Only `NEXT_PUBLIC_*` values reach the browser, and those are the Supabase URL and publishable key, which are public by design. Never use a Supabase secret or service-role key in this app.
- Run `bash scripts/check-secrets.sh` before committing. The CI workflow runs it, including a scan of history, on every push.
- Keep `ALLOW_OPEN_ACCESS` unset. Setting it to `true` lets an endpoint run in production without a passcode.

## If a key leaks
1. **Revoke or rotate it first** at the provider (Google AI Studio, Groq, Cerebras, OpenRouter, Mistral, Supabase). Removing it from GitHub does not make it safe again.
2. Put the new key in `.env.local` and in the host's environment variables, then redeploy.
3. Remove it from the repository and history (for example with `git filter-repo`), which means a force push is needed once. Do this carefully, with a backup, and only after step 1.
4. If the repository was ever public, assume the key was copied.

## Accounts
- Passwords are handled by Supabase Auth and are never stored by this app.
- Row-level security means each signed-in user can only read and change their own chats and settings.

## Reporting a problem
This is a personal project. Report issues to the repository owner privately.
