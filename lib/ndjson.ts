// Reads a newline-delimited JSON stream (one JSON object per line) and calls onEvent for each line, in order.
// Lines that are not valid JSON are skipped. A last line without a trailing newline is still delivered.
export type StreamEvent = { type?: string; [key: string]: unknown };

export async function readNdjson(body: ReadableStream<Uint8Array>, onEvent: (event: StreamEvent) => void): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  const emit = (line: string) => {
    const t = line.trim();
    if (!t) return;
    let parsed: unknown;
    try {
      parsed = JSON.parse(t);
    } catch {
      return;
    }
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) onEvent(parsed as StreamEvent);
  };
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let nl: number;
      while ((nl = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, nl);
        buf = buf.slice(nl + 1);
        emit(line);
      }
    }
    buf += decoder.decode();
    emit(buf);
  } finally {
    try {
      reader.releaseLock();
    } catch {
      /* already released */
    }
  }
}
