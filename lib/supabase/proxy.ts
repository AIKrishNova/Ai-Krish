import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

const AUTH_PAGES = ["/login", "/signup", "/forgot-password"];
const OPEN = ["/reset-password", "/verify", "/auth", "/manifest.webmanifest", "/pwa-192", "/pwa-512", "/apple-icon", "/favicon.ico"];
const starts = (p: string, list: string[]) => list.some((x) => p === x || p.startsWith(x + "/"));

export async function updateSession(request: NextRequest) {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  const path = request.nextUrl.pathname;
  let response = NextResponse.next({ request });

  const go = (to: string, search = "") => {
    const u = request.nextUrl.clone();
    u.pathname = to;
    u.search = search;
    const r = NextResponse.redirect(u);
    response.cookies.getAll().forEach((c) => r.cookies.set(c));
    return r;
  };

  let user: { email_confirmed_at?: string | null } | null = null;
  if (url && key) {
    const supabase = createServerClient(url, key, {
      cookies: {
        getAll: () => request.cookies.getAll(),
        setAll(list) {
          list.forEach(({ name, value }) => request.cookies.set(name, value));
          response = NextResponse.next({ request });
          list.forEach(({ name, value, options }) => response.cookies.set(name, value, options));
        },
      },
    });
    user = (await supabase.auth.getUser()).data.user;
  }

  // API routes answer 401 themselves (lib/auth.ts); the proxy only refreshes the session for them.
  if (path.startsWith("/api/")) return response;

  if (!user) {
    if (starts(path, AUTH_PAGES) || starts(path, OPEN)) return response;
    return go("/login", path === "/" ? "" : `?next=${encodeURIComponent(path)}`);
  }
  if (!user.email_confirmed_at) {
    if (starts(path, AUTH_PAGES) || starts(path, OPEN)) return response;
    return go("/verify");
  }
  const verifiedPage = path === "/verify" && request.nextUrl.searchParams.get("status") === "verified";
  if (starts(path, AUTH_PAGES) || (path === "/verify" && !verifiedPage)) return go("/");
  return response;
}
