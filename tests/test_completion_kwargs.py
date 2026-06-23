# -*- coding: utf-8 -*-
from llm_connector.completion_params import build_chat_completion_kwargs
from llm_connector.models import ProviderRow
from llm_connector.replicate_client import messages_to_replicate_input


def _provider(code: str) -> ProviderRow:
    return ProviderRow(
        id=1,
        code=code,
        base_url="https://example.com/v1",
        shared_api_key_env="KEY",
        default_verify_ssl=True,
        is_enabled=True,
    )


def test_gpt5_on_replicate_uses_max_completion_tokens_and_no_temperature():
    kwargs = build_chat_completion_kwargs(
        provider=_provider("replicate"),
        model="openai/gpt-5-mini",
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.7,
        timeout_sec=60,
        max_tokens=512,
        response_format=None,
    )
    assert kwargs["max_completion_tokens"] == 512
    assert "max_tokens" not in kwargs
    assert "temperature" not in kwargs


def test_replicate_native_input_from_messages():
    inp = messages_to_replicate_input(
        [
            {"role": "system", "content": "Be brief"},
            {"role": "user", "content": "OK"},
        ],
        model="openai/gpt-5-mini",
        max_tokens=64,
        response_format="json_object",
    )
    assert inp["prompt"] == "user: OK"
    assert "JSON" in inp["system_prompt"]
    assert inp["max_completion_tokens"] == 64
    assert inp["reasoning_effort"] == "minimal"
