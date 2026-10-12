"""Offline tests for the NVIDIA provider helpers. No network and no API key needed."""
import pytest

from app.core.config import Settings
from app.providers.errors import ProviderError
from app.providers.nvidia import error_from_status, parse_completion


def test_parse_reads_answer_and_reasoning():
    data = {
        "choices": [{"message": {"content": "NEXUS is online", "reasoning_content": "thinking"}, "finish_reason": "stop"}],
        "usage": {"total_tokens": 5},
    }
    out = parse_completion(data)
    assert out["content"] == "NEXUS is online"
    assert out["reasoning"] == "thinking"
    assert out["warning"] is None


def test_parse_accepts_alternative_reasoning_field_name():
    data = {"choices": [{"message": {"content": "ok", "reasoning": "alt"}, "finish_reason": "stop"}]}
    assert parse_completion(data)["reasoning"] == "alt"


def test_parse_warns_when_thinking_used_all_tokens():
    data = {"choices": [{"message": {"content": None, "reasoning_content": "long"}, "finish_reason": "length"}]}
    out = parse_completion(data)
    assert out["content"] == ""
    assert out["warning"]


def test_parse_without_choices_raises():
    with pytest.raises(ProviderError):
        parse_completion({"choices": []})


def test_retired_model_gives_clear_error():
    err = error_from_status(410)
    assert err.code == "bad_request"
    assert "retired" in err.message


def test_model_not_on_account_gives_clear_error():
    err = error_from_status(404)
    assert err.code == "bad_request"
    assert "not available" in err.message


def test_server_error_is_retryable():
    assert error_from_status(503).retryable is True


def test_settings_repr_hides_the_key():
    assert "nvapi-secret-test" not in repr(Settings(nvidia_api_key="nvapi-secret-test"))
