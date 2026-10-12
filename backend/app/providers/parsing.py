"""Parsing of OpenAI-style streamed chat chunks and SSE framing. Pure stdlib."""
import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass


@dataclass
class StreamChunk:
    text: str = ""
    finish_reason: str | None = None
    usage: dict | None = None   # only when the provider supplies it; never estimated


def parse_stream_lines(lines: Iterable[str]) -> Iterator[StreamChunk]:
    """Parse `data: {...}` lines from an OpenAI-compatible streaming response."""
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith(":") or not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            return
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError:
            continue  # tolerate keep-alives / partial garbage; caller sees no text for it
        usage = obj.get("usage")
        choices = obj.get("choices") or []
        if not choices:
            if usage:
                yield StreamChunk(usage=usage)
            continue
        ch = choices[0]
        text = (ch.get("delta") or {}).get("content") or ""
        if text or ch.get("finish_reason") or usage:
            yield StreamChunk(text=text, finish_reason=ch.get("finish_reason"), usage=usage)


def sse_event(event: str, data: dict) -> str:
    """Correctly framed SSE event (JSON on a single data line; newlines are escaped by json)."""
    if not event.replace("_", "").isalnum():
        raise ValueError("invalid event name")
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
