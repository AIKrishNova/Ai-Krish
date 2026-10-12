"""Pure-logic tests (no third-party deps). Pytest-compatible; also run by scripts/run_pure_tests.py."""
import json

from app.core.redaction import redact_mapping, redact_text
from app.core.security import hash_password, verify_password
from app.core.urlguard import UnsafeURLError, validate_provider_url
from app.providers.errors import backoff_delay, from_http_status
from app.providers.parsing import parse_stream_lines, sse_event

ALLOWED = [".nvidia.com"]


def _raises(fn, exc):
    try:
        fn()
    except exc:
        return True
    return False


def test_redacts_bearer_and_nvapi_keys():
    out = redact_text("Authorization: Bearer abc.def-123 key=nvapi-SECRETVALUE_1")
    assert "abc.def-123" not in out and "SECRETVALUE" not in out


def test_redact_mapping_hides_sensitive_keys():
    out = redact_mapping({"Authorization": "Bearer x", "nested": {"api_key": "k", "ok": "fine"}})
    assert out["Authorization"] == "[REDACTED]" and out["nested"]["api_key"] == "[REDACTED]" and out["nested"]["ok"] == "fine"


def test_urlguard_rejects_unsafe_urls():
    for bad in ["http://integrate.api.nvidia.com/v1", "https://evil.example.com/v1", "https://127.0.0.1/v1",
                "https://169.254.169.254/latest", "https://user:pw@api.nvidia.com/v1", "ftp://api.nvidia.com", "https://nvidia.com.evil.io"]:
        assert _raises(lambda b=bad: validate_provider_url(b, ALLOWED, resolve=False), UnsafeURLError), bad


def test_urlguard_accepts_allowed_host_without_dns():
    assert validate_provider_url("https://integrate.api.nvidia.com/v1/", ALLOWED, resolve=False) == "https://integrate.api.nvidia.com/v1"


def test_urlguard_localhost_only_when_explicitly_allowed():
    assert _raises(lambda: validate_provider_url("http://localhost:8000", ALLOWED), UnsafeURLError)
    assert validate_provider_url("http://localhost:8000", ALLOWED, allow_http_localhost=True)


def test_password_hash_roundtrip_and_policy():
    h = hash_password("correct horse battery")
    assert verify_password("correct horse battery", h) and not verify_password("wrong password!!", h)
    assert "correct horse" not in h and not verify_password("x", "garbage")
    assert _raises(lambda: hash_password("short"), ValueError)


def test_error_normalization():
    assert from_http_status(401).code == "auth" and not from_http_status(401).retryable
    e = from_http_status(429, 2.0)
    assert e.code == "rate_limited" and e.retryable and e.retry_after == 2.0
    assert from_http_status(503).retryable and from_http_status(404).code == "bad_request"


def test_backoff_bounded_and_honors_retry_after():
    assert [backoff_delay(i) for i in range(5)] == [0.5, 1.0, 2.0, 4.0, 8.0]
    assert backoff_delay(10) == 8.0 and backoff_delay(0, retry_after=3) == 3 and backoff_delay(0, retry_after=999) == 8.0


def test_stream_parser_text_usage_done_and_garbage():
    lines = [": keepalive", 'data: {"choices":[{"delta":{"content":"Hel"}}]}', "data: not-json",
             'data: {"choices":[{"delta":{"content":"lo"},"finish_reason":"stop"}],"usage":{"total_tokens":7}}',
             "data: [DONE]", 'data: {"choices":[{"delta":{"content":"IGNORED"}}]}']
    chunks = list(parse_stream_lines(lines))
    assert "".join(c.text for c in chunks) == "Hello"
    assert chunks[-1].finish_reason == "stop" and chunks[-1].usage == {"total_tokens": 7}


def test_sse_framing_escapes_newlines_and_validates_event():
    frame = sse_event("token", {"text": "a\nb"})
    assert frame.endswith("\n\n") and frame.count("\n") == 3
    assert json.loads(frame.split("data: ", 1)[1])["text"] == "a\nb"
    assert _raises(lambda: sse_event("bad\nevent", {}), ValueError)
