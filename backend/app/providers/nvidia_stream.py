"""Streaming NVIDIA chat. Reads reasoning_content as well as content. Never logs the API key."""
import json
from collections.abc import AsyncIterator

import httpx

from app.core.config import Settings
from app.providers.errors import ProviderError
from app.providers.nvidia import _retry_after, error_from_status
from app.providers.parsing import sse_event

STREAM_WAIT = 90.0  # seconds to wait for the first byte (slow models take 15-35s)


def parse_stream_line(raw: str) -> dict | None:
    """One SSE line -> dict, {"done": True} for [DONE], or None for lines to ignore."""
    line = raw.strip()
    if not line.startswith("data:"):
        return None
    payload = line[5:].strip()
    if payload == "[DONE]":
        return {"done": True}
    try:
        obj = json.loads(payload)
    except json.JSONDecodeError:
        return None
    usage = obj.get("usage")
    choices = obj.get("choices") or []
    if not choices:
        return {"usage": usage} if usage else None
    choice = choices[0]
    delta = choice.get("delta") or {}
    return {
        "content": delta.get("content") or "",
        "reasoning": delta.get("reasoning_content") or delta.get("reasoning") or "",
        "finish_reason": choice.get("finish_reason"),
        "usage": usage,
    }


def error_event(err: ProviderError) -> str:
    return sse_event("error", {"code": err.code, "message": err.message, "retryable": err.retryable})


async def stream_chat(
    settings: Settings,
    messages: list[dict],
    *,
    model: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.3,
    reasoning_effort: str | None = None,
    timeout: float | None = None,
    include_reasoning: bool = False,
) -> AsyncIterator[str]:
    used_model = model or settings.default_model
    yield sse_event("start", {"model": used_model})
    if not settings.nvidia_api_key:
        yield error_event(ProviderError("not_configured", "NVIDIA_API_KEY is missing from backend/.env.", False))
        return
    body = {
        "model": used_model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
    }
    if reasoning_effort:
        body["reasoning_effort"] = reasoning_effort
    wait = timeout or max(settings.request_timeout, STREAM_WAIT)
    limits = httpx.Timeout(connect=10.0, read=wait, write=10.0, pool=10.0)
    headers = {
        "Authorization": "Bearer " + settings.nvidia_api_key,
        "Content-Type": "application/json",
    }
    got_content = False
    finish = None
    usage = None
    try:
        async with httpx.AsyncClient(timeout=limits) as client:
            async with client.stream("POST", settings.nvidia_base_url + "/chat/completions", headers=headers, json=body) as response:
                if response.status_code != 200:
                    yield error_event(error_from_status(response.status_code, _retry_after(response)))
                    return
                async for line in response.aiter_lines():
                    item = parse_stream_line(line)
                    if item is None:
                        continue
                    if item.get("done"):
                        break
                    if item.get("usage"):
                        usage = item["usage"]
                    if item.get("finish_reason"):
                        finish = item["finish_reason"]
                    if item.get("reasoning"):
                        yield sse_event("thinking", {"text": item["reasoning"] if include_reasoning else ""})
                    if item.get("content"):
                        got_content = True
                        yield sse_event("token", {"text": item["content"]})
    except httpx.TimeoutException:
        yield error_event(ProviderError(
            "timeout",
            f"NVIDIA sent nothing for {wait:.0f}s. The model may be busy. Try again or choose another model.",
            True,
        ))
        return
    except httpx.HTTPError as exc:
        yield error_event(ProviderError("unavailable", f"Could not reach NVIDIA ({type(exc).__name__}).", True))
        return
    warning = None
    if not got_content and finish == "length":
        warning = "The model used all of max_tokens for thinking before it started the answer. Increase max_tokens."
    yield sse_event("done", {"model": used_model, "finish_reason": finish, "usage": usage, "warning": warning})
