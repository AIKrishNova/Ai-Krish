export function isEmail(v: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim());
}

export function passwordIssues(p: string): string[] {
  const out: string[] = [];
  if (p.length < 8) out.push("Use at least 8 characters.");
  if (!/[A-Za-z]/.test(p) || !/\d/.test(p)) out.push("Mix letters and numbers.");
  return out;
}

/** 0 (empty/weak) to 4 (strong). */
export function passwordScore(p: string): number {
  if (!p) return 0;
  let s = 0;
  if (p.length >= 8) s++;
  if (p.length >= 12) s++;
  if (/[a-z]/.test(p) && /[A-Z]/.test(p)) s++;
  if (/\d/.test(p)) s++;
  if (/[^A-Za-z0-9]/.test(p)) s++;
  if (p.length < 8) s = Math.min(s, 1);
  return Math.min(4, s);
}

export const STRENGTH_LABELS = ["Too weak", "Weak", "Fair", "Good", "Strong"];

/** Only allow same-site relative paths after sign-in. Blocks open redirects. */
export function safeNext(v: string | null | undefined, fallback = "/") {
  if (!v || !v.startsWith("/") || v.startsWith("//") || v.includes("\\")) return fallback;
  return v;
}
