import { GoogleGenAI } from "@google/genai";
import { findProvider } from "../chatProviders";

type Env = Record<string, string | undefined>;
export type ImageInput = { name: string; mime: string; data: Buffer | Uint8Array };
export type ChatTurn = { role: string; text: string };
export type VisionProvider = { name: string; model: string; kind: "gemini" | "openai-compat" };

const DEFAULT_GEMINI = "gemini-3.8-flash";

// A provider counts as "vision-capable" only when we have a key AND a model that is declared for images.
// Text models such as gpt-oss are never used for images unless you set <PROVIDER>_VISION_MODEL yourself.
export function visionProviders(env: Env = process.env): VisionProvider[] {
  const order = (env.VISION_PROVIDER_ORDER || "gemini,groq,openrouter,mistral")
    .split(",")
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
  const out: VisionProvider[] = [];
  for (const name of Array.from(new Set(order))) {
    if (name === "gemini") {
      if (env.GEMINI_API_KEY) {
        // GEMINI_VISION_MODELS is a fallback list: if one model is busy or rate limited, the next one is tried.
        const list = (env.GEMINI_VISION_MODELS || "").split(",").map((s) => s.trim()).filter(Boolean);
        const models = list.length ? Array.from(new Set(list)) : [env.GEMINI_VISION_MODEL || env.GEMINI_MODEL || DEFAULT_GEMINI];
        for (const model of models) out.push({ name, kind: "gemini", model });
      }
      continue;
    }
    const cfg = findProvider(name);
    const model = env[`${name.toUpperCase()}_VISION_MODEL`];
    if (cfg && env[cfg.keyEnv] && model) out.push({ name, kind: "openai-compat", model });
  }
  return out;
}

export function routeForImages(env: Env = process.env): VisionProvider | null {
  return visionProviders(env)[0] ?? null;
}

export function explainProviderError(e: unknown): string {
  const raw = e instanceof Error ? e.message : String(e);
  if (/429|RESOURCE_EXHAUSTED|rate limit/i.test(raw)) return "rate limit reached, try again in a minute";
  if (/\b503\b|UNAVAILABLE|high demand|overloaded/i.test(raw)) return "the model is overloaded right now (temporary), try again in a minute";
  if (/timed out|abort/i.test(raw)) return "timed out";
  if (/401|403|API key|permission/i.test(raw)) return "the key was rejected";
  if (/image|multimodal|vision|modalit/i.test(raw) && /(not support|unsupported|invalid|cannot)/i.test(raw)) return "this model does not accept images";
  return raw.replace(/\s+/g, " ").slice(0, 160);
}

function toTurns(history: ChatTurn[]) {
  const turns = history.filter((m) => typeof m.text === "string" && m.text && !m.text.startsWith("Error:"));
  const first = turns.findIndex((m) => m.role === "user");
  return turns.slice(first === -1 ? turns.length : first);
}

const b64 = (d: Buffer | Uint8Array) => Buffer.from(d).toString("base64");

async function callGemini(p: VisionProvider, system: string, history: ChatTurn[], prompt: string, images: ImageInput[], ms: number) {
  const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
  const contents = [
    ...toTurns(history).map((m) => ({ role: m.role === "user" ? "user" : "model", parts: [{ text: m.text }] })),
    {
      role: "user",
      parts: [{ text: prompt }, ...images.map((im) => ({ inlineData: { mimeType: im.mime, data: b64(im.data) } }))],
    },
  ];
  const result = await Promise.race([
    ai.models.generateContent({ model: p.model, contents, config: { systemInstruction: system } }),
    new Promise<never>((_, rej) => setTimeout(() => rej(new Error(`gemini: timed out after ${ms / 1000}s`)), ms)),
  ]);
  if (!result.text) throw new Error("gemini: empty reply (the image may have been blocked by the safety filter)");
  return result.text;
}

async function callCompat(p: VisionProvider, system: string, history: ChatTurn[], prompt: string, images: ImageInput[], ms: number) {
  const cfg = findProvider(p.name);
  if (!cfg) throw new Error(`Unknown provider ${p.name}`);
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  try {
    const res = await fetch(cfg.url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${process.env[cfg.keyEnv]}`, ...(cfg.extraHeaders ?? {}) },
      body: JSON.stringify({
        model: p.model,
        messages: [
          { role: "system", content: system },
          ...toTurns(history).map((m) => ({ role: m.role === "user" ? "user" : "assistant", content: m.text })),
          {
            role: "user",
            content: [
              { type: "text", text: prompt },
              ...images.map((im) => ({ type: "image_url", image_url: { url: `data:${im.mime};base64,${b64(im.data)}` } })),
            ],
          },
        ],
      }),
      signal: ctrl.signal,
    });
    if (!res.ok) throw new Error(`${p.name} ${res.status}: ${(await res.text()).slice(0, 200)}`);
    const text = (await res.json())?.choices?.[0]?.message?.content;
    if (!text) throw new Error(`${p.name}: empty reply`);
    return String(text);
  } finally {
    clearTimeout(timer);
  }
}

export type VisionRequest = { provider: VisionProvider; system: string; history: ChatTurn[]; prompt: string; images: ImageInput[] };

export async function callVisionProvider(r: VisionRequest): Promise<string> {
  const ms = Number(process.env.VISION_TIMEOUT_MS) || 30000;
  return r.provider.kind === "gemini"
    ? callGemini(r.provider, r.system, r.history, r.prompt, r.images, ms)
    : callCompat(r.provider, r.system, r.history, r.prompt, r.images, ms);
}
