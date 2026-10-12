"""Offline tests for streaming helpers. No network and no API key needed."""
import asyncio
import json

from app.core.config import Settings
from app.providers.errors import ProviderError
from app.providers.nvidia_stream import error_event, parse_stream_line, stream_chat


def _line(delta, finish=None, usage=None):
    obj = {"choices": [{"delta": delta, "finish_reason": finish}]}
    if usage:
        obj["usage"] = usage
    return "data: " + json.dumps(obj)


def test_parse_reads_answer_text():
    assert parse_stream_line(_line({"content": "hi"}))["content"] == "hi"


def test_parse_reads_reasoning_text():
    assert parse_stream_line(_line({"reasoning_content": "hmm"}))["reasoning"] == "hmm"


def test_parse_accepts_alternative_reasoning_name():
    assert parse_stream_line(_line({"reasoning": "alt"}))["reasoning"] == "alt"


def test_parse_done_marker():
    assert parse_stream_line("data: [DONE]") == {"done": True}


def test_parse_ignores_comments_and_garbage():
    assert parse_stream_line(": keep-alive") is None
    assert parse_stream_line("data: {not json") is None
    assert parse_stream_line("") is None


def test_parse_usage_only_chunk():
    assert parse_stream_line('data: {"choices": [], "usage": {"total_tokens": 7}}') == {"usage": {"total_tokens": 7}}


def test_error_event_shape():
    out = error_event(ProviderError("timeout", "slow", True))
    assert out.startswith("event: error\n")
    assert '"retryable": true' in out


def test_stream_without_key_sends_start_then_error():
    async def collect():
        return [e async for e in stream_chat(Settings(nvidia_api_key=""), [{"role": "user", "content": "hi"}])]

    events = asyncio.run(collect())
    assert events[0].startswith("event: start")
    assert "not_configured" in events[-1]
