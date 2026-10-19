import { createClient } from "./supabase/server";

export type SessionResult =
  | { ok: true; user: { id: string; email: string | undefined } }
  | { ok: false; status: 401 | 503; error: string };

/** Server-side check for API routes. Fails closed: no valid verified session, no access. */
export async function requireUser(): Promise<SessionResult> {
  if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY) {
    return { ok: false, status: 503, error: "Sign-in is not configured on the server." };
  }
  try {
    const supabase = await createClient();
    const { data, error } = await supabase.auth.getUser();
    if (error || !data.user) return { ok: false, status: 401, error: "locked" };
    if (!data.user.email_confirmed_at) return { ok: false, status: 401, error: "Verify your email first." };
    return { ok: true, user: { id: data.user.id, email: data.user.email } };
  } catch {
    return { ok: false, status: 401, error: "locked" };
  }
}
