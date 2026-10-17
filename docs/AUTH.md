# Sign-in (Supabase)

AI KRISH uses Supabase Auth: accounts, password hashing, verification emails, reset emails and sessions.
Passwords are never stored by this app. Sessions live in HTTP-only cookies.

## Environment variables (names only; values go in `.env.local` and Vercel, never in chat or git)
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`

These two are meant to be public (they ship to the browser). Never use the secret/service-role key in this app.
`NEXT_PUBLIC_` values are baked in at build time, so set them on Vercel BEFORE `npx vercel --prod`.

## Supabase dashboard
- Authentication > URL Configuration: Site URL `https://ai-krish-liard.vercel.app`; Redirect URLs `https://ai-krish-liard.vercel.app/**` and `http://localhost:3000/**`.
- Authentication > Sign In / Providers > Email: enabled, Confirm email ON. Optional: raise minimum password length to 8.
- Authentication > Rate Limits: Supabase enforces sign-in, sign-up, resend and reset limits on its server. Built-in email allows only a few messages per hour; add a custom SMTP provider (for example Resend) before real users arrive.

## How protection works
- `proxy.ts` refreshes the session and sends signed-out visitors to `/login`, unverified users to `/verify`.
- Every API route calls `requireUser()` (lib/auth.ts) on the server. No valid, email-verified session means 401.
- The old shared passcode (`APP_PASSCODE`, `x-krish-pass`) is no longer read by the routes.

## Known limits
- Verification and reset links must be opened in the same browser that requested them (PKCE).
- No "Remember me" box: Supabase sessions already persist. No Google button: no provider is configured.
- While Vercel Deployment Protection is on, email links open Vercel's login wall first for anyone not logged in to Vercel.
- The terms/privacy checkbox has no linked pages yet.
