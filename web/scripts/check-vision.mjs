// Sends a tiny solid-red image to every vision provider you have configured and reports PASS or FAIL.
// Run:  npm run check:vision      (reads .env.local, prints no keys)
import { GoogleGenAI } from "@google/genai";

const env = process.env;
const RED_PNG = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAeUlEQVR4nO3PQQkAMAzAwCqpf1ETMxF7HINABFzm7H7dcEEDWtCAFjSgBQ1oQQNa0IAWNKAFDWhBA1rQgBY0oAUNaEEDWtCAFjSgBQ1oQQNa0IAWNKAFDWhBA1rQgBY0oAUNaEEDWtCAFjSgBQ1oQQNa0IAWNKAFj13PLIEAOXyUUwAAAABJRU5ErkJggg==";
const QUESTION = "What is the dominant colour of this image? Answer with one word.";
const COMPAT = {
  groq: { url: "https://api.groq.com/openai/v1/chat/completions", key: "GROQ_API_KEY" },
  openrouter: { url: "https://openrouter.ai/api/v1/chat/completions", key: "OPENROUTER_API_KEY" },
  mistral: { url: "https://api.mistral.ai/v1/chat/completions", key: "MISTRAL_API_KEY" },
};

const targets = [];
if (env.GEMINI_API_KEY) {
  const list = (env.GEMINI_VISION_MODELS || "").split(",").map((s) => s.trim()).filter(Boolean);
  const models = list.length ? [...new Set(list)] : [env.GEMINI_VISION_MODEL || env.GEMINI_MODEL || "gemini-3.8-flash"];
  for (const model of models) targets.push({ name: "gemini", model });
}
for (const [name, c] of Object.entries(COMPAT)) {
  const model = env[name.toUpperCase() + "_VISION_MODEL"];
  if (env[c.key] && model) targets.push({ name, model });
}

if (targets.length === 0) {
  console.log("No vision provider is configured. Set GEMINI_API_KEY (or <PROVIDER>_VISION_MODEL plus its key) in .env.local.");
  process.exit(1);
}

const BUSY = /\b503\b|\b429\b|UNAVAILABLE|RESOURCE_EXHAUSTED|high demand|overloaded/i;
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function ask(t) {
  if (t.name === "gemini") {
    const ai = new GoogleGenAI({ apiKey: env.GEMINI_API_KEY });
    const r = await ai.models.generateContent({
      model: t.model,
      contents: [{ role: "user", parts: [{ text: QUESTION }, { inlineData: { mimeType: "image/png", data: RED_PNG } }] }],
    });
    return r.text ?? "";
  }
  const c = COMPAT[t.name];
  const res = await fetch(c.url, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + env[c.key] },
    body: JSON.stringify({
      model: t.model,
      messages: [{ role: "user", content: [{ type: "text", text: QUESTION }, { type: "image_url", image_url: { url: "data:image/png;base64," + RED_PNG } }] }],
    }),
  });
  if (!res.ok) throw new Error(res.status + " " + (await res.text()).slice(0, 160));
  return (await res.json())?.choices?.[0]?.message?.content ?? "";
}

let failed = 0;
let inconclusive = 0;
for (const t of targets) {
  const label = t.name + " (" + t.model + ")";
  let done = false;
  for (let attempt = 1; attempt <= 4 && !done; attempt++) {
    try {
      const text = await ask(t);
      const ok = /red/i.test(text);
      console.log((ok ? "PASS" : "FAIL") + "  " + label + "  answered: " + JSON.stringify(text.trim().slice(0, 60)));
      if (!ok) failed++;
      done = true;
    } catch (e) {
      const msg = String(e instanceof Error ? e.message : e).replace(/\s+/g, " ").slice(0, 200);
      if (BUSY.test(msg) && attempt < 4) {
        console.log("..    " + label + "  busy (try " + attempt + " of 4), waiting " + attempt * 5 + "s");
        await wait(attempt * 5000);
        continue;
      }
      if (BUSY.test(msg)) {
        console.log("BUSY  " + label + "  still overloaded or rate limited. This does NOT mean images are unsupported. Run again in a few minutes.");
        inconclusive++;
      } else {
        console.log("FAIL  " + label + "  " + msg);
        failed++;
      }
      done = true;
    }
  }
}
if (failed) console.log("\nSome providers cannot read images. Remove them from VISION_PROVIDER_ORDER or fix the model name.");
else if (inconclusive) console.log("\nNo failures, but some providers were too busy to test. Run it again later.");
else console.log("\nAll configured vision providers can read images.");
process.exit(failed ? 1 : inconclusive ? 2 : 0);
