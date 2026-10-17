import { analyzeImages } from "../../../lib/ai/imageAnalysis";
import { validateImages } from "../../../lib/files/image";
import { serverLimits } from "../../../lib/files/limits";
import { clientKey, rateLimit } from "../../../lib/security";
import { requireUser } from "../../../lib/auth";

// Reading several photos with a thorough check can take a while.
export const maxDuration = 60;

type Turn = { role: string; text: string };

function json(body: unknown, status: number, headers: Record<string, string> = {}) {
  return Response.json(body, { status, headers: { "Cache-Control": "no-store", ...headers } });
}

export async function POST(req: Request) {
  const ip = clientKey(req);

  // 1. Access control: a signed-in, email-verified user is required.
  const session = await requireUser();
  if (!session.ok) return json({ error: session.error }, session.status);

  // 2. Rate limit and size checks before reading the body.
  const perMin = Number(process.env.ANALYZE_RATE_PER_MIN) || 10;
  const rl = rateLimit("analyze:" + ip, perMin, 60_000);
  if (!rl.ok) {
    return json({ error: `Too many requests. Try again in ${rl.retryAfter} seconds.` }, 429, { "Retry-After": String(rl.retryAfter) });
  }
  const limits = serverLimits();
  const declared = Number(req.headers.get("content-length") || 0);
  if (declared > limits.maxRequestBytes) {
    return json({ error: `The upload is too large. Keep all images in one message under ${(limits.maxTotalBytes / 1_000_000).toFixed(1)} MB.` }, 413);
  }

  let form: FormData;
  try {
    form = await req.formData();
  } catch {
    return json({ error: "Could not read the upload. Please try again." }, 400);
  }

  const question = String(form.get("question") ?? "").trim().slice(0, 4000);
  const userData = String(form.get("context") ?? "").trim().slice(0, 4000);
  const memory = String(form.get("memory") ?? "").slice(0, 2000);
  const deep = form.get("think") === "1";
  let history: Turn[] = [];
  try {
    const parsed = JSON.parse(String(form.get("history") ?? "[]"));
    if (Array.isArray(parsed)) {
      history = parsed
        .filter((m) => m && typeof m.text === "string" && typeof m.role === "string")
        .map((m) => ({ role: m.role === "user" ? "user" : "jarvis", text: String(m.text).slice(0, 4000) }))
        .slice(-10);
    }
  } catch {
    history = [];
  }

  const entries = form.getAll("files").filter((f): f is File => typeof f !== "string");
  if (entries.length === 0) return json({ error: "Attach at least one image." }, 400);

  const { valid, skipped } = await validateImages(
    entries.map((f) => ({ name: f.name, type: f.type, size: f.size, read: async () => Buffer.from(await f.arrayBuffer()) })),
    limits
  );
  if (valid.length === 0) {
    return json({ error: "None of the files could be used. " + skipped.map((s) => `${s.file}: ${s.reason}`).join(" "), skipped }, 400);
  }

  // 3. Stream progress lines, then the final result. Nothing is written to disk: images live in memory for this request only.
  const enc = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const send = (o: unknown) => controller.enqueue(enc.encode(JSON.stringify(o) + "\n"));
      try {
        send({ type: "status", message: `Received ${valid.length} image${valid.length === 1 ? "" : "s"}.` });
        const result = await analyzeImages({
          question,
          userData,
          history,
          memory,
          images: valid,
          deep,
          maxSteps: Number(process.env.THINK_MAX_STEPS) || 4,
          emit: (message) => send({ type: "status", message }),
        });
        if (result.ok) send({ type: "result", ...result, skipped });
        else send({ type: "error", code: result.code, error: result.error, skipped });
      } catch (e) {
        send({ type: "error", code: "server_error", error: "Something went wrong while analysing: " + (e instanceof Error ? e.message : String(e)), skipped });
      } finally {
        controller.close();
      }
    },
  });
  return new Response(stream, {
    headers: { "Content-Type": "application/x-ndjson; charset=utf-8", "Cache-Control": "no-store", "X-Accel-Buffering": "no" },
  });
}
