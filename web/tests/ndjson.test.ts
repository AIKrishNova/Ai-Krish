import { describe, expect, it } from "vitest";
import { readNdjson, type StreamEvent } from "../lib/ndjson";

function streamOf(chunks: (string | Uint8Array)[]) {
  const enc = new TextEncoder();
  return new ReadableStream<Uint8Array>({
    start(c) {
      for (const x of chunks) c.enqueue(typeof x === "string" ? enc.encode(x) : x);
      c.close();
    },
  });
}

async function collect(body: ReadableStream<Uint8Array>) {
  const out: StreamEvent[] = [];
  await readNdjson(body, (e) => out.push(e));
  return out;
}

describe("readNdjson", () => {
  it("delivers events in order", async () => {
    const out = await collect(streamOf(['{"type":"meta","provider":"groq"}\n{"type":"delta","text":"Hi"}\n{"type":"done"}\n']));
    expect(out.map((e) => e.type)).toEqual(["meta", "delta", "done"]);
  });

  it("joins a line that is split across chunks", async () => {
    const out = await collect(streamOf(['{"type":"delta","te', 'xt":"Hello"}\n{"type":"do', 'ne"}\n']));
    expect(out).toEqual([{ type: "delta", text: "Hello" }, { type: "done" }]);
  });

  it("keeps a multi-byte character that is split between chunks", async () => {
    const bytes = new TextEncoder().encode('{"type":"delta","text":"வணக்கம்"}\n');
    const cut = 22; // inside the Tamil text
    const out = await collect(streamOf([bytes.slice(0, cut), bytes.slice(cut)]));
    expect(out).toEqual([{ type: "delta", text: "வணக்கம்" }]);
  });

  it("delivers a last line that has no newline", async () => {
    const out = await collect(streamOf(['{"type":"delta","text":"a"}\n{"type":"done"}']));
    expect(out.map((e) => e.type)).toEqual(["delta", "done"]);
  });

  it("skips lines that are not JSON and blank lines", async () => {
    const out = await collect(streamOf(['garbage\n\n{"type":"done"}\n{broken\n']));
    expect(out).toEqual([{ type: "done" }]);
  });

  it("reports an error line like any other event", async () => {
    const out = await collect(streamOf(['{"type":"delta","text":"Part"}\n{"type":"error","partial":true,"error":"timed out"}\n']));
    expect(out[1]).toMatchObject({ type: "error", partial: true });
  });
});
