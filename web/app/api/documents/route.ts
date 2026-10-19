import { requireUser } from "../../../lib/auth";
import { docLimits, extractDocument } from "../../../lib/files/documents";
import { serverLimits } from "../../../lib/files/limits";
import { clientKey, rateLimit } from "../../../lib/security";

export const maxDuration = 30;

function json(body: unknown, status: number, headers: Record<string, string> = {}) {
  return Response.json(body, { status, headers: { "Cache-Control": "no-store", ...headers } });
}

/** Reads attached PDF / Word / CSV / text files and returns their text. Nothing is stored. */
export async function POST(req: Request) {
  const session = await requireUser();
  if (!session.ok) return json({ error: session.error }, session.status);

  const perMin = Number(process.env.DOCS_RATE_PER_MIN) || 10;
  const rl = rateLimit("docs:" + clientKey(req), perMin, 60_000);
  if (!rl.ok) {
    return json({ error: `Too many requests. Try again in ${rl.retryAfter} seconds.` }, 429, { "Retry-After": String(rl.retryAfter) });
  }

  const bytes = serverLimits();
  const docs = docLimits();
  const declared = Number(req.headers.get("content-length") || 0);
  if (declared > bytes.maxRequestBytes) {
    return json({ error: `The upload is too large. Keep files under ${(bytes.maxTotalBytes / 1_000_000).toFixed(1)} MB in total.` }, 413);
  }

  let form: FormData;
  try {
    form = await req.formData();
  } catch {
    return json({ error: "Could not read the upload. Please try again." }, 400);
  }

  const files = form.getAll("files").filter((f): f is File => typeof f !== "string");
  if (files.length === 0) return json({ error: "Attach at least one document." }, 400);
  if (files.length > docs.maxFiles) return json({ error: `Attach at most ${docs.maxFiles} documents at a time.` }, 400);

  const documents = [];
  const skipped: { file: string; reason: string }[] = [];
  let total = 0;
  for (const f of files) {
    if (f.size > bytes.maxFileBytes) {
      skipped.push({ file: f.name, reason: `Larger than ${(bytes.maxFileBytes / 1_000_000).toFixed(1)} MB.` });
      continue;
    }
    total += f.size;
    if (total > bytes.maxTotalBytes) {
      skipped.push({ file: f.name, reason: "Over the total upload size for one message." });
      continue;
    }
    const r = await extractDocument(
      { name: f.name, type: f.type, size: f.size, read: async () => Buffer.from(await f.arrayBuffer()) },
      docs.perDocChars
    );
    if (r.ok) documents.push(r.doc);
    else skipped.push({ file: f.name, reason: r.reason });
  }

  if (documents.length === 0) {
    return json({ error: "None of the files could be read. " + skipped.map((s) => `${s.file}: ${s.reason}`).join(" "), skipped }, 400);
  }
  return json({ documents, skipped }, 200);
}
