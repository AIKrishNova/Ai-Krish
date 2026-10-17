import { createHash, timingSafeEqual } from "node:crypto";

type Env = Record<string, string | undefined>;
export type AuthResult = { ok: true } | { ok: false; status: number; error: string };

function digest(s: string) {
  return createHash("sha256").update(s).digest();
}

export function clientKey(req: Request) {
  const fwd = req.headers.get("x-forwarded-for");
  return (fwd ? fwd.split(",")[0].trim() : req.headers.get("x-real-ip")) || "unknown";
}

// Fixed-window counters kept in memory. On Vercel each server instance has its own counters,
// so this is a best-effort brake, not a hard global limit.
const buckets = new Map<string, { count: number; reset: number }>();

export function rateLimit(key: string, limit: number, windowMs: number, now = Date.now()) {
  if (buckets.size > 5000) {
    for (const [k, v] of buckets) if (v.reset <= now) buckets.delete(k);
  }
  const b = buckets.get(key);
  if (!b || b.reset <= now) {
    buckets.set(key, { count: 1, reset: now + windowMs });
    return { ok: true as const, retryAfter: 0 };
  }
  b.count += 1;
  if (b.count > limit) return { ok: false as const, retryAfter: Math.max(1, Math.ceil((b.reset - now) / 1000)) };
  return { ok: true as const, retryAfter: 0 };
}

export function resetRateLimits() {
  buckets.clear();
}

export function authorize(req: Request, env: Env = process.env): AuthResult {
  const need = env.APP_PASSCODE;
  if (!need) {
    if (env.NODE_ENV === "production" && env.ALLOW_OPEN_ACCESS !== "true") {
      return { ok: false, status: 503, error: "APP_PASSCODE is not set on the server, so uploads are disabled. Set it in Vercel and redeploy." };
    }
    return { ok: true };
  }
  const given = req.headers.get("x-krish-pass") ?? "";
  if (!timingSafeEqual(digest(given), digest(need))) {
    return { ok: false, status: 401, error: "locked" };
  }
  return { ok: true };
}
