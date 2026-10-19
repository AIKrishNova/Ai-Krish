import { beforeEach, describe, expect, it } from "vitest";
import { authorize, rateLimit, resetRateLimits } from "../lib/security";

const req = (pass?: string) => new Request("http://x/api/analyze", { method: "POST", headers: pass ? { "x-krish-pass": pass } : {} });

describe("authorize", () => {
  it("accepts the right passcode and rejects wrong or missing ones", () => {
    expect(authorize(req("secret"), { APP_PASSCODE: "secret" })).toEqual({ ok: true });
    expect(authorize(req("nope"), { APP_PASSCODE: "secret" })).toMatchObject({ ok: false, status: 401 });
    expect(authorize(req(), { APP_PASSCODE: "secret" })).toMatchObject({ ok: false, status: 401 });
  });
  it("fails closed in production when no passcode is configured", () => {
    expect(authorize(req(), { NODE_ENV: "production" })).toMatchObject({ ok: false, status: 503 });
    expect(authorize(req(), { NODE_ENV: "production", ALLOW_OPEN_ACCESS: "true" })).toEqual({ ok: true });
  });
  it("stays open for local development without a passcode", () => {
    expect(authorize(req(), { NODE_ENV: "development" })).toEqual({ ok: true });
  });
});

describe("rateLimit", () => {
  beforeEach(() => resetRateLimits());
  it("blocks after the limit and recovers after the window", () => {
    expect(rateLimit("k", 2, 1000, 0).ok).toBe(true);
    expect(rateLimit("k", 2, 1000, 10).ok).toBe(true);
    const blocked = rateLimit("k", 2, 1000, 20);
    expect(blocked.ok).toBe(false);
    expect(blocked.retryAfter).toBeGreaterThan(0);
    expect(rateLimit("k", 2, 1000, 1500).ok).toBe(true);
  });
  it("keeps separate counters per key", () => {
    rateLimit("a", 1, 1000, 0);
    expect(rateLimit("a", 1, 1000, 1).ok).toBe(false);
    expect(rateLimit("b", 1, 1000, 1).ok).toBe(true);
  });
});
