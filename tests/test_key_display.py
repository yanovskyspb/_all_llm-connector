# -*- coding: utf-8 -*-
"""Tests for API key display helpers."""

from llm_connector.key_display import mask_key, resolve_key_display
from llm_connector.models import ProviderRow, RouteRow


def _route(**kwargs) -> RouteRow:
    provider = ProviderRow(
        id=1,
        code="openrouter",
        base_url="https://openrouter.ai/api/v1",
        shared_api_key_env="API_OPENROUTER_KEY",
        default_verify_ssl=True,
    )
    defaults = dict(
        id=1,
        project_id=1,
        caller_script="test.py",
        function_key="default",
        model_slot=1,
        primary_provider_id=1,
        primary_model="test/model",
        same_provider_fallback_model=None,
        fallback_provider_id=None,
        fallback_model=None,
        error_streak_threshold=1,
        max_failures=3,
        failure_count=0,
        is_suspended=False,
        temperature=0.0,
        max_tokens=None,
        timeout_sec=60,
        max_retries=3,
        retry_delay_sec=5,
        response_format=None,
        verify_ssl=None,
        api_key_env=None,
        is_active=True,
        provider=provider,
        fallback_provider=None,
    )
    defaults.update(kwargs)
    return RouteRow(**defaults)


def test_mask_key_short():
    assert mask_key("abc") == "****"


def test_mask_key_long():
    assert mask_key("sk-or-v1-abcdefghijklmnop") == "sk-o…mnop"


def test_resolve_shared_key(monkeypatch):
    monkeypatch.setenv("API_OPENROUTER_KEY", "sk-or-v1-testkey123456")
    info = resolve_key_display(_route(), _route().provider)
    assert info["source"] == "shared_env"
    assert info["label"] == "общий"
    assert info["is_set"] is True
    assert "…" in info["masked_value"]


def test_resolve_route_key(monkeypatch):
    monkeypatch.delenv("API_OPENROUTER_KEY", raising=False)
    monkeypatch.setenv("MY_ROUTE_KEY", "route-secret-key-value")
    route = _route(api_key_env="MY_ROUTE_KEY")
    info = resolve_key_display(route, route.provider)
    assert info["source"] == "route_env"
    assert info["label"] == "персональный"
    assert info["env_name"] == "MY_ROUTE_KEY"
