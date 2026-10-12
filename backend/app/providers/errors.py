"""Normalized provider errors. Pure stdlib."""
from dataclasses import dataclass


@dataclass
class ProviderError(Exception):
    code: str          # not_configured | auth | rate_limited | bad_request | timeout | unavailable | unknown
    message: str       # safe to show the user; never contains secrets
    retryable: bool = False
    status: int | None = None
    retry_after: float | None = None

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def from_http_status(status: int, retry_after: float | None = None) -> ProviderError:
    if status in (401, 403):
        return ProviderError("auth", "The provider rejected the credentials. Check the API key and its permissions.", False, status)
    if status == 429:
        return ProviderError("rate_limited", "The provider rate limit was reached. Try again shortly.", True, status, retry_after)
    if status in (400, 404, 422):
        return ProviderError("bad_request", "The provider rejected the request (check the model ID and parameters).", False, status)
    if status == 408:
        return ProviderError("timeout", "The provider request timed out.", True, status)
    if 500 <= status < 600:
        return ProviderError("unavailable", "The provider is temporarily unavailable.", True, status)
    return ProviderError("unknown", f"Unexpected provider response (HTTP {status}).", False, status)


def backoff_delay(attempt: int, retry_after: float | None = None, base: float = 0.5, cap: float = 8.0, jitter: float = 0.0) -> float:
    """Delay before retry number `attempt` (0-based). Honors Retry-After, bounded by cap."""
    if retry_after is not None:
        return min(max(retry_after, 0.0), cap)
    return min(base * (2 ** attempt), cap) + jitter
