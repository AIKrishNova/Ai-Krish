// Updates tests/route.test.ts from passcode checks to signed-in-user checks, and removes the unused passcode() helper.
// Checks first, writes nothing if a marker is missing. Backups: <file>.bak-authfix
import fs from "node:fs";
const problems = [], jobs = [];
const need = (cond, msg) => { if (!cond) problems.push(msg); };

const tf = "tests/route.test.ts";
let t = fs.readFileSync(tf, "utf8");
const t0 = t;
if (!t.includes("lib/auth")) {
  const mockLine = `vi.mock("../lib/ai/imageAnalysis", () => ({ analyzeImages: analyze }));`;
  const envLine = `  vi.stubEnv("APP_PASSCODE", "secret");`;
  const s = t.indexOf(`  it("rejects a missing or wrong passcode`);
  const e = t.indexOf(`  it("asks for an image when none`);
  need(t.includes(mockLine), "mock line for imageAnalysis not found");
  need(t.includes(envLine), "APP_PASSCODE stub line not found");
  need(s > 0 && e > s, "the two passcode tests were not found");
  if (!problems.length) {
    t = t.replace(mockLine, mockLine + `\nconst session = vi.hoisted(() => vi.fn());\nvi.mock("../lib/auth", () => ({ requireUser: session }));`);
    t = t.replace(envLine, `  session.mockReset();\n  session.mockResolvedValue({ ok: true, user: { id: "u1", email: "a@b.co" } });`);
    const s2 = t.indexOf(`  it("rejects a missing or wrong passcode`), e2 = t.indexOf(`  it("asks for an image when none`);
    t = t.slice(0, s2) + `  it("rejects signed-out requests", async () => {
    session.mockResolvedValue({ ok: false, status: 401, error: "locked" });
    const res = await call(formWith([{ name: "a.png", data: PNG }]));
    expect(res.status).toBe(401);
    expect(analyze).not.toHaveBeenCalled();
  });

  it("returns 503 when sign-in is not configured", async () => {
    session.mockResolvedValue({ ok: false, status: 503, error: "Sign-in is not configured on the server." });
    const res = await call(formWith([{ name: "a.png", data: PNG }]));
    expect(res.status).toBe(503);
    expect(analyze).not.toHaveBeenCalled();
  });

` + t.slice(e2);
  }
}
if (t !== t0) jobs.push([tf, t0, t]);

const pf = "app/page.tsx";
let p = fs.readFileSync(pf, "utf8");
const dead = `  function passcode() {\n    try { return localStorage.getItem("krish-pass") ?? ""; } catch { return ""; }\n  }\n\n`;
if (p.includes(dead)) jobs.push([pf, p, p.replace(dead, "")]);

if (problems.length) { console.error("STOPPED. Nothing changed:\n- " + problems.join("\n- ")); process.exit(1); }
for (const [f, before, after] of jobs) { fs.writeFileSync(f + ".bak-authfix", before); fs.writeFileSync(f, after); console.log("updated", f); }
console.log(jobs.length ? "Done." : "Nothing to change.");
