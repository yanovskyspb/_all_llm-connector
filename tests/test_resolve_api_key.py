# -*- coding: utf-8 -*-
import os
from unittest.mock import MagicMock

import pytest

from llm_connector.exceptions import MissingApiKeyError
from llm_connector.keys import resolve_api_key
from llm_connector.models import ProviderRow, RouteRow


def _provider() -> ProviderRow:
    return ProviderRow(
        id=1,
        code="openrouter",
        base_url="https://openrouter.ai/api/v1",
        shared_api_key_env="API_OPENROUTER_KEY",
        default_verify_ssl=True,
    )


def _route(api_key_env=None) -> RouteRow:
    p = _provider()
    return RouteRow(
        id=1,
        project_id=1,
        caller_script="test.py",
        function_key="default",
        model_slot=1,
        stage=0,
        primary_provider_id=1,
        primary_model="test/model",
        same_provider_fallback_model=None,
        fallback_provider_id=None,
        fallback_model=None,
        error_streak_threshold=1,
        max_failures=3,
        failure_count=0,
        is_suspended=False,
        temperature=0,
        max_tokens=None,
        timeout_sec=60,
        max_retries=1,
        retry_delay_sec=1,
        response_format=None,
        verify_ssl=None,
        api_key_env=api_key_env,
        is_active=True,
        provider=p,
    )


def test_explicit_key_wins(monkeypatch):
    monkeypatch.delenv("API_OPENROUTER_KEY", raising=False)
    key, src = resolve_api_key("sk-explicit", _route(), _provider())
    assert key == "sk-explicit"
    assert src == "explicit"


def test_route_env_before_shared(monkeypatch):
    monkeypatch.setenv("ROUTE_KEY", "sk-route")
    monkeypatch.delenv("API_OPENROUTER_KEY", raising=False)
    key, src = resolve_api_key(None, _route(api_key_env="ROUTE_KEY"), _provider())
    assert key == "sk-route"
    assert src == "route_env"


def test_shared_env_when_no_explicit(monkeypatch):
    monkeypatch.setenv("API_OPENROUTER_KEY", "sk-shared")
    key, src = resolve_api_key(None, _route(), _provider())
    assert key == "sk-shared"
    assert src == "shared_env"


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("API_OPENROUTER_KEY", raising=False)
    with pytest.raises(MissingApiKeyError):
        resolve_api_key(None, _route(), _provider())
