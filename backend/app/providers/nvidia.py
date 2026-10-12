"""NVIDIA chat client (OpenAI-compatible API, plain httpx). Never logs the API key."""
import httpx

from app.core.config import Settings
from app.providers.errors import ProviderError, from_http_status


def error_from_status(status: int, retry_after: float | None = None) -> ProviderError:
    """Turn an HTTP status into a friendly, secret-free error."""
    if status == 410:
        return ProviderError("bad_request", "NVIDIA has retired this model. Choose another model.", False, status)
    if status == 404:
        return ProviderError("bad_request", "This model is not available to your NVIDIA account. Choose another model.", False, status)
    return from_http_status(status, retry_after)


def parse_completion(data: dict) -> dict:
    """Pull the answer and the reasoning out of a non-streaming response."""
    choices = data.get("choices") or []
    if not choices:
        raise ProviderError("unknown", "The provider returned no choices.", False)
    choice = choices[0]
    message = choice.get("message") or {}
    content = message.get("content") or ""
    reasoning = message.get("reasoning_content") or message.get("reasoning") or ""
    finish = choice.get("finish_reason")
    warning = None
    if not content and finish == "length":
        warning = (
            "The model used all of max_tokens for thinking before it started the answer. "
            "Increase max_tokens or use a lower reasoning effort."
        )
    return {
        "content": content,
        "reasoning": reasoning,
        "finish_reason": finish,
        "usage": data.get("usage"),
        "warning": warning,
    }


def _retry_after(response: httpx.Response) -> float | None:
    try:
        return float(response.headers.get("retry-after", ""))
    except ValueError:
        return None


async def chat_completion(
    settings: Settings,
    messages: list[dict],
    *,
    model: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.3,
    reasoning_effort: str | None = None,
    timeout: float | None = None,
) -> dict:
    if not settings.nvidia_api_key:
        raise ProviderError("not_configured", "NVIDIA_API_KEY is missing from backend/.env.", False)
    body = {
        "model": model or settings.default_model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    if reasoning_effort:
        body["reasoning_effort"] = reasoning_effort
    read_timeout = timeout or settings.request_timeout
    limits = httpx.Timeout(connect=10.0, read=read_timeout, write=10.0, pool=10.0)
    headers = {
        "Authorization": "Bearer " + settings.nvidia_api_key,
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=limits) as client:
            response = await client.post(settings.nvidia_base_url + "/chat/completions", headers=headers, json=body)
    except httpx.TimeoutException:
        raise ProviderError(
            "timeout",
            f"NVIDIA did not answer within {read_timeout:.0f}s. The model may be busy. Try again or choose another model.",
            True,
        ) from None
    except httpx.HTTPError as exc:
        raise ProviderError("unavailable", f"Could not reach NVIDIA ({type(exc).__name__}).", True) from None
    if response.status_code != 200:
        raise error_from_status(response.status_code, _retry_after(response))
    try:
        data = response.json()
    except ValueError:
        raise ProviderError("unknown", "NVIDIA returned a response that was not valid JSON.", False) from None
    result = parse_completion(data)
    result["model"] = body["model"]
    return result
