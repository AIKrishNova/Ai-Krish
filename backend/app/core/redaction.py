"""Secret redaction for logs and error payloads. Pure stdlib."""
import re

_PATTERNS = [
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-~+/=]+"), r"\1[REDACTED]"),
    (re.compile(r"nvapi-[A-Za-z0-9_\-]+"), "[REDACTED]"),
    (re.compile(r"(?i)((?:api[_-]?key|token|secret|password|authorization)\"?\s*[:=]\s*\"?)[^\s\",;]+"), r"\1[REDACTED]"),
]
SENSITIVE_KEYS = {"authorization", "api_key", "apikey", "x-api-key", "password", "secret", "token", "cookie", "set-cookie"}


def redact_text(text: str) -> str:
    for pattern, repl in _PATTERNS:
        text = pattern.sub(repl, text)
    return text


def redact_mapping(data):
    """Recursively redact values of sensitive keys and secret-looking strings."""
    if isinstance(data, dict):
        return {k: ("[REDACTED]" if str(k).lower() in SENSITIVE_KEYS else redact_mapping(v)) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [redact_mapping(v) for v in data]
    if isinstance(data, str):
        return redact_text(data)
    return data
