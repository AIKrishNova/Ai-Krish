import { describe, expect, it, vi } from "vitest";
import { analyzeImages, type AnalyzeDeps } from "../lib/ai/imageAnalysis";
import type { VisionProvider, VisionRequest } from "../lib/ai/vision";
import { PNG } from "./helpers";

const gem: VisionProvider = { name: "gemini", kind: "gemini", model: "g-vision" };
const grq: VisionProvider = { name: "groq", kind: "openai-compat", model: "q-vision" };
const images = [{ name: "receipt.png", mime: "image/png", data: PNG }];
const base = { question: "What is the total?", userData: "I paid by card", history: [], images, deep: false };

function deps(providers: VisionProvider[], fn: (r: VisionRequest, n: number) => Promise<string>) {
  let n = 0;
  const call = vi.fn((r: VisionRequest) => fn(r, n++));
  return { d: { providers, call } as AnalyzeDeps, call };
}

describe("analyzeImages", () => {
  it("refuses to claim success when there are no images", async () => {
    const { d, call } = deps([gem], async () => "x");
    const r = await analyzeImages({ ...base, images: [], deps: d });
    expect(r).toMatchObject({ ok: false, code: "no_images" });
    expect(call).not.toHaveBeenCalled();
  });

  it("refuses to analyse when no vision model is configured and never calls a text model", async () => {
    const { d, call } = deps([], async () => "x");
    const r = await analyzeImages({ ...base, deps: d });
    expect(r).toMatchObject({ ok: false, code: "no_vision_model" });
    expect((r as { error: string }).error).toMatch(/NOT analysed/);
    expect(call).not.toHaveBeenCalled();
  });

  it("sends the real image bytes, the question and the user's details to the vision model", async () => {
    const { d, call } = deps([gem], async () => "Answer: 12.50");
    const r = await analyzeImages({ ...base, memory: "my name is Krish", deps: d });
    expect(r).toMatchObject({ ok: true, reply: "Answer: 12.50", provider: "gemini", model: "g-vision", mode: "standard", analyzed: ["receipt.png"] });
    const req = call.mock.calls[0][0];
    expect(req.images[0].data).toBe(PNG);
    expect(req.prompt).toContain("What is the total?");
    expect(req.prompt).toContain("I paid by card");
    expect(req.prompt).toContain("receipt.png");
    expect(req.system).toContain("Never invent details");
    expect(req.system).toContain("Do not identify real people");
    expect(req.system).toContain("my name is Krish");
  });

  it("uses a default question when the user sends only a photo", async () => {
    const { d, call } = deps([gem], async () => "ok");
    await analyzeImages({ ...base, question: "", deps: d });
    expect(call.mock.calls[0][0].prompt).toMatch(/Describe this image/);
  });

  it("falls back to the next vision provider when the first fails", async () => {
    const { d } = deps([gem, grq], async (r) => {
      if (r.provider.name === "gemini") throw new Error("429 RESOURCE_EXHAUSTED");
      return "from groq";
    });
    const r = await analyzeImages({ ...base, deps: d });
    expect(r).toMatchObject({ ok: true, reply: "from groq", provider: "groq" });
  });

  it("reports every provider failure instead of pretending it worked", async () => {
    const { d } = deps([gem, grq], async (r) => {
      throw new Error(r.provider.name === "gemini" ? "429 RESOURCE_EXHAUSTED" : "model does not support image input");
    });
    const r = await analyzeImages({ ...base, deps: d });
    expect(r.ok).toBe(false);
    const msg = (r as { error: string }).error;
    expect(msg).toMatch(/NOT be analysed|NOT analysed/);
    expect(msg).toMatch(/gemini: rate limit/);
    expect(msg).toMatch(/groq: this model does not accept images/);
  });

  it("moves on to the next Gemini model when the first is rate limited, and names the models in the error if all fail", async () => {
    const g1: VisionProvider = { name: "gemini", kind: "gemini", model: "m1" };
    const g2: VisionProvider = { name: "gemini", kind: "gemini", model: "m2" };
    const ok = deps([g1, g2], async (r) => {
      if (r.provider.model === "m1") throw new Error("429 RESOURCE_EXHAUSTED");
      return "from m2";
    });
    expect(await analyzeImages({ ...base, deps: ok.d })).toMatchObject({ ok: true, reply: "from m2", model: "m2" });
    const bad = deps([g1, g2], async () => { throw new Error("429 RESOURCE_EXHAUSTED"); });
    const r = await analyzeImages({ ...base, deps: bad.d });
    expect((r as { error: string }).error).toMatch(/gemini \(m1\): rate limit.*gemini \(m2\): rate limit/);
  });

  describe("temporary 'model is busy' errors", () => {
    const busy = () => new Error('{"error":{"code":503,"message":"This model is currently experiencing high demand.","status":"UNAVAILABLE"}}');

    it("retries a busy model and then succeeds", async () => {
      const sleep = vi.fn(async () => {});
      const { d, call } = deps([gem], async (_r, n) => {
        if (n < 2) throw busy();
        return "Answer: ok";
      });
      const r = await analyzeImages({ ...base, deps: { ...d, sleep } });
      expect(r).toMatchObject({ ok: true, reply: "Answer: ok" });
      expect(call).toHaveBeenCalledTimes(3);
      expect(sleep).toHaveBeenCalledTimes(2);
    });

    it("gives up after three tries and says the model is overloaded", async () => {
      const sleep = vi.fn(async () => {});
      const { d, call } = deps([gem], async () => { throw busy(); });
      const r = await analyzeImages({ ...base, deps: { ...d, sleep } });
      expect(call).toHaveBeenCalledTimes(3);
      expect(r.ok).toBe(false);
      expect((r as { error: string }).error).toMatch(/overloaded right now/);
    });

    it("does not retry real errors such as a rejected key", async () => {
      const sleep = vi.fn(async () => {});
      const { d, call } = deps([gem], async () => { throw new Error("403 API key not valid"); });
      await analyzeImages({ ...base, deps: { ...d, sleep } });
      expect(call).toHaveBeenCalledTimes(1);
      expect(sleep).not.toHaveBeenCalled();
    });
  });

  describe("deep analysis", () => {
    it("observes, answers, checks and corrects when the check finds problems", async () => {
      const { d, call } = deps([gem], async (_r, n) =>
        ["Scene: a receipt", "Answer: total 15.00", '{"issues":["The total is not 15.00 in the image"]}', "Answer: total 12.50"][n]
      );
      const status: string[] = [];
      const r = await analyzeImages({ ...base, deep: true, emit: (m) => status.push(m), deps: d });
      expect(call).toHaveBeenCalledTimes(4);
      expect(r).toMatchObject({ ok: true, reply: "Answer: total 12.50", mode: "deep" });
      expect((r as { explanation: string }).explanation).toMatch(/1 issue, and the answer was corrected/);
      expect(call.mock.calls[1][0].prompt).toContain("Scene: a receipt");
      expect(status).toHaveLength(4);
    });

    it("keeps the answer and says so when the check finds nothing", async () => {
      const { d, call } = deps([gem], async (_r, n) => ["Scene: x", "Answer: fine", '{"issues":[]}'][n]);
      const r = await analyzeImages({ ...base, deep: true, deps: d });
      expect(call).toHaveBeenCalledTimes(3);
      expect(r).toMatchObject({ ok: true, reply: "Answer: fine" });
      expect((r as { explanation: string }).explanation).toMatch(/no problems found/);
    });

    it("admits when the check could not be completed", async () => {
      const { d } = deps([gem], async (_r, n) => ["Scene: x", "Answer: maybe", "not json at all"][n]);
      const r = await analyzeImages({ ...base, deep: true, deps: d });
      expect((r as { explanation: string }).explanation).toMatch(/could not be completed/);
      expect((r as { reply: string }).reply).toBe("Answer: maybe");
    });

    it("respects THINK_MAX_STEPS", async () => {
      const { d, call } = deps([gem], async (_r, n) => ["Scene: x", "Answer: quick"][n]);
      const r = await analyzeImages({ ...base, deep: true, maxSteps: 2, deps: d });
      expect(call).toHaveBeenCalledTimes(2);
      expect((r as { explanation: string }).explanation).toMatch(/check is disabled/);
    });
  });
});
