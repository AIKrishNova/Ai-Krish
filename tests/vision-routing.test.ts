import { describe, expect, it } from "vitest";
import { routeForImages, visionProviders } from "../lib/ai/vision";

describe("vision routing", () => {
  it("has no vision route when nothing is configured", () => {
    expect(visionProviders({})).toEqual([]);
    expect(routeForImages({})).toBeNull();
  });
  it("uses Gemini when its key is set, with an overridable vision model", () => {
    expect(routeForImages({ GEMINI_API_KEY: "x" })?.name).toBe("gemini");
    expect(routeForImages({ GEMINI_API_KEY: "x", GEMINI_VISION_MODEL: "my-vision" })?.model).toBe("my-vision");
  });
  it("never sends images to text-only providers (Groq/Cerebras keys alone are not enough)", () => {
    expect(visionProviders({ GROQ_API_KEY: "x", CEREBRAS_API_KEY: "y" })).toEqual([]);
  });
  it("uses a compatible provider only when a vision model is declared explicitly", () => {
    const r = visionProviders({ GROQ_API_KEY: "x", GROQ_VISION_MODEL: "some-vision-model" });
    expect(r).toEqual([{ name: "groq", kind: "openai-compat", model: "some-vision-model" }]);
    expect(visionProviders({ GROQ_VISION_MODEL: "some-vision-model" })).toEqual([]);
  });
  it("builds a Gemini fallback list from GEMINI_VISION_MODELS, without duplicates, ahead of the single-model setting", () => {
    const r = visionProviders({ GEMINI_API_KEY: "x", GEMINI_VISION_MODEL: "ignored", GEMINI_VISION_MODELS: "m1, m2,m1,," });
    expect(r.map((p) => p.model)).toEqual(["m1", "m2"]);
    expect(r.every((p) => p.name === "gemini")).toBe(true);
  });
  it("respects VISION_PROVIDER_ORDER and falls back across providers", () => {
    const env = { GEMINI_API_KEY: "x", GROQ_API_KEY: "y", GROQ_VISION_MODEL: "v" };
    expect(visionProviders(env).map((p) => p.name)).toEqual(["gemini", "groq"]);
    expect(visionProviders({ ...env, VISION_PROVIDER_ORDER: "groq,gemini" }).map((p) => p.name)).toEqual(["groq", "gemini"]);
  });
});
