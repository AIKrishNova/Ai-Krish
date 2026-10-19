export type ChatMsg = { role: string; text: string };

type ProviderCfg = {
  name: string;
  url: string;
  keyEnv: string;
  modelEnv: string;
  defaultModel: string;
  extraHeaders?: Record<string, string>;
};

// Groq, OpenRouter and Mistral all use the same "OpenAI-style" request format.
export const OPENAI_COMPAT: ProviderCfg[] = [
  {
    name: "groq",
    url: "https://api.groq.com/openai/v1/chat/completions",
    keyEnv: "GROQ_API_KEY",
    modelEnv: "GROQ_MODEL",
    defaultModel: "openai/gpt-oss-120b",
  },
  {
    name: "cerebras",
    url: "https://api.cerebras.ai/v1/chat/completions",
    keyEnv: "CEREBRAS_API_KEY",
    modelEnv: "CEREBRAS_MODEL",
    defaultModel: "gpt-oss-120b",
  },
  {
    name: "openrouter",
    url: "https://openrouter.ai/api/v1/chat/completions",
    keyEnv: "OPENROUTER_API_KEY",
    modelEnv: "OPENROUTER_MODEL",
    defaultModel: "meta-llama/llama-3.3-70b-instruct:free",
    extraHeaders: { "X-Title": "AI Krish" },
  },
  {
    name: "mistral",
    url: "https://api.mistral.ai/v1/chat/completions",
    keyEnv: "MISTRAL_API_KEY",
    modelEnv: "MISTRAL_MODEL",
    defaultModel: "mistral-small-latest",
  },
];

export function findProvider(name: string) {
  return OPENAI_COMPAT.find((p) => p.name === name);
}

export function hasKey(name: string) {
  const p = findProvider(name);
  return !!(p && process.env[p.keyEnv]);
}

export function toOpenAIMessages(system: string, history: ChatMsg[]) {
  return [
    { role: "system", content: system },
    ...history.map((m) => ({
      role: m.role === "user" ? "user" : "assistant",
      content: m.text,
    })),
  ];
}

export async function callOpenAICompat(
  name: string,
  system: string,
  history: ChatMsg[],
  timeoutMs: number
): Promise<{ reply: string; model: string }> {
  const cfg = findProvider(name);
  if (!cfg) throw new Error(`Unknown provider: ${name}`);
  const key = process.env[cfg.keyEnv];
  if (!key) throw new Error(`${cfg.name}: key missing`);
  const model = process.env[cfg.modelEnv] || cfg.defaultModel;

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(cfg.url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${key}`,
        ...(cfg.extraHeaders ?? {}),
      },
      body: JSON.stringify({
        model,
        messages: toOpenAIMessages(system, history),
      }),
      signal: ctrl.signal,
    });
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`${cfg.name} ${res.status}: ${body.slice(0, 200)}`);
    }
    const data = await res.json();
    const text = data?.choices?.[0]?.message?.content;
    if (!text) throw new Error(`${cfg.name}: empty reply`);
    return { reply: String(text), model };
  } catch (e) {
    if (e instanceof Error && e.name === "AbortError") {
      throw new Error(`${cfg.name}: timed out after ${timeoutMs / 1000}s`);
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Streams text pieces from any OpenAI-style /chat/completions endpoint (server-sent events).
 * Throws on HTTP errors. Ends when the server sends [DONE] or closes the connection.
 */
export async function* streamChatCompletions(opts: {
  label: string;
  url: string;
  key: string;
  model: string;
  messages: { role: string; content: string }[];
  headers?: Record<string, string>;
  signal?: AbortSignal;
}): AsyncGenerator<string> {
  const res = await fetch(opts.url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${opts.key}`,
      ...(opts.headers ?? {}),
    },
    body: JSON.stringify({ model: opts.model, messages: opts.messages, stream: true }),
    signal: opts.signal,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${opts.label} ${res.status}: ${body.slice(0, 200)}`);
  }
  if (!res.body) throw new Error(`${opts.label}: no response body`);

  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let nl: number;
      while ((nl = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, nl).trim();
        buf = buf.slice(nl + 1);
        if (!line.startsWith("data:")) continue;
        const data = line.slice(5).trim();
        if (data === "[DONE]") return;
        let j: { choices?: { delta?: { content?: unknown } }[]; error?: { message?: string } };
        try {
          j = JSON.parse(data);
        } catch {
          continue; // ignore partial or non-JSON lines
        }
        if (j?.error) throw new Error(`${opts.label}: ${j.error.message ?? "stream error"}`);
        const piece = j?.choices?.[0]?.delta?.content;
        if (typeof piece === "string" && piece) yield piece;
      }
    }
  } finally {
    reader.cancel().catch(() => {});
  }
}

export function streamOpenAICompat(
  name: string,
  system: string,
  history: ChatMsg[],
  signal?: AbortSignal
): AsyncGenerator<string> {
  const cfg = findProvider(name);
  if (!cfg) throw new Error(`Unknown provider: ${name}`);
  const key = process.env[cfg.keyEnv];
  if (!key) throw new Error(`${cfg.name}: key missing`);
  return streamChatCompletions({
    label: cfg.name,
    url: cfg.url,
    key,
    model: process.env[cfg.modelEnv] || cfg.defaultModel,
    messages: toOpenAIMessages(system, history),
    headers: cfg.extraHeaders,
    signal,
  });
}
