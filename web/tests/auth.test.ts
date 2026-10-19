import { beforeEach, describe, expect, it, vi } from "vitest";
import { isEmail, passwordIssues, passwordScore, safeNext } from "../lib/authValidation";

const { getUser } = vi.hoisted(() => ({ getUser: vi.fn() }));
vi.mock("../lib/supabase/server", () => ({ createClient: async () => ({ auth: { getUser } }) }));
import { requireUser } from "../lib/auth";

describe("validation", () => {
  it("checks emails", () => {
    expect(isEmail("a@b.co")).toBe(true);
    expect(isEmail("nope")).toBe(false);
    expect(isEmail("a b@c.com")).toBe(false);
  });
  it("flags weak passwords and scores strength", () => {
    expect(passwordIssues("abc").length).toBe(2);
    expect(passwordIssues("abcdefg1")).toEqual([]);
    expect(passwordScore("")).toBe(0);
    expect(passwordScore("abc")).toBeLessThanOrEqual(1);
    expect(passwordScore("Correct-Horse-9-Battery")).toBe(4);
  });
  it("blocks open redirects", () => {
    expect(safeNext("/alerts")).toBe("/alerts");
    expect(safeNext("//evil.com")).toBe("/");
    expect(safeNext("https://evil.com")).toBe("/");
    expect(safeNext("/\\evil.com")).toBe("/");
    expect(safeNext(null)).toBe("/");
  });
});

describe("requireUser (server-side access control)", () => {
  beforeEach(() => {
    getUser.mockReset();
    process.env.NEXT_PUBLIC_SUPABASE_URL = "https://example.supabase.co";
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "test-key";
  });
  it("rejects when nobody is signed in", async () => {
    getUser.mockResolvedValue({ data: { user: null }, error: new Error("no session") });
    expect(await requireUser()).toMatchObject({ ok: false, status: 401 });
  });
  it("rejects an unverified email", async () => {
    getUser.mockResolvedValue({ data: { user: { id: "1", email: "a@b.co", email_confirmed_at: null } }, error: null });
    expect(await requireUser()).toMatchObject({ ok: false, status: 401 });
  });
  it("allows a verified user", async () => {
    getUser.mockResolvedValue({ data: { user: { id: "1", email: "a@b.co", email_confirmed_at: "2026-10-17T00:00:00Z" } }, error: null });
    expect(await requireUser()).toMatchObject({ ok: true, user: { id: "1" } });
  });
  it("fails closed when the auth service throws", async () => {
    getUser.mockRejectedValue(new Error("network"));
    expect(await requireUser()).toMatchObject({ ok: false, status: 401 });
  });
  it("fails closed when Supabase is not configured", async () => {
    delete process.env.NEXT_PUBLIC_SUPABASE_URL;
    expect(await requireUser()).toMatchObject({ ok: false, status: 503 });
  });
});
