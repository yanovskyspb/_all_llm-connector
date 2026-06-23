# -*- coding: utf-8 -*-
import os
from pathlib import Path

import pytest

from llm_connector.env import ensure_env_loaded
from llm_connector.exceptions import MissingApiKeyError
from llm_connector.keys import resolve_api_key
from llm_connector.models import ProviderRow, RouteRow


def _provider(
    code: str = "routerai",
    *,
    shared: str = "API_ROUTERAI_KEY",
    legacy: str | None = None,
) -> ProviderRow:
    return ProviderRow(
        id=4,
        code=code,
        base_url=f"https://{code}.example/v1",
        shared_api_key_env=shared,
        default_verify_ssl=True,
        legacy_api_key_env=legacy,
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
        primary_model="openai/gpt-4o-mini",
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


def _reset_env_loader(monkeypatch, tmp_path: Path) -> None:
    import llm_connector.env as env_mod

    env_mod._LOADED = False
    monkeypatch.delenv("API_ROUTERAI_KEY", raising=False)
    monkeypatch.delenv("API_VSEGPT_KEY", raising=False)
    monkeypatch.setattr(env_mod, "package_root", lambda: tmp_path)


def test_stage_api_key_env_before_head(monkeypatch, tmp_path):
    _reset_env_loader(monkeypatch, tmp_path)
    monkeypatch.setenv("STAGE_ROUTERAI_KEY", "sk-stage")
    route = _route(api_key_env="HEAD_KEY")
    key, src = resolve_api_key(
        None,
        route,
        _provider(),
        stage_api_key_env="STAGE_ROUTERAI_KEY",
    )
    assert key == "sk-stage"
    assert src == "route_env"


def test_stage_api_key_env_falls_back_to_shared(monkeypatch, tmp_path):
    _reset_env_loader(monkeypatch, tmp_path)
    monkeypatch.setenv("API_ROUTERAI_KEY", "sk-shared")
    key, src = resolve_api_key(None, _route(), _provider(), stage_api_key_env=None)
    assert key == "sk-shared"
    assert src == "shared_env"


def test_legacy_provider_api_key_env(monkeypatch, tmp_path):
    _reset_env_loader(monkeypatch, tmp_path)
    monkeypatch.setenv("LEGACY_ROUTERAI", "sk-legacy")
    provider = _provider(shared="", legacy="LEGACY_ROUTERAI")
    route = _route()
    route = RouteRow(**{**route.__dict__, "provider": provider})
    key, src = resolve_api_key(None, route, provider)
    assert key == "sk-legacy"
    assert src == "shared_env"


def test_vsegpt_shared_while_routerai_missing(monkeypatch, tmp_path):
    """Same process: one provider key in env, another not — matches prod log pattern."""
    _reset_env_loader(monkeypatch, tmp_path)
    monkeypatch.setenv("API_VSEGPT_KEY", "sk-vsegpt")
    with pytest.raises(MissingApiKeyError):
        resolve_api_key(None, _route(), _provider())
    vsg = _provider(code="vsegpt", shared="API_VSEGPT_KEY")
    key, src = resolve_api_key(None, _route(), vsg)
    assert key == "sk-vsegpt"
    assert src == "shared_env"


def test_ensure_env_loaded_reads_dotenv(monkeypatch, tmp_path):
    import llm_connector.env as env_mod

    env_mod._LOADED = False
    monkeypatch.delenv("API_ROUTERAI_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("API_ROUTERAI_KEY=sk-from-dotenv\n", encoding="utf-8")
    monkeypatch.setattr(env_mod, "package_root", lambda: tmp_path)

    assert ensure_env_loaded(force=True) is True
    key, src = resolve_api_key(None, _route(), _provider())
    assert key == "sk-from-dotenv"
    assert src == "shared_env"


def test_consumer_cwd_env_is_ignored(monkeypatch, tmp_path):
    """Keys come from llm-connector .env only, not from consumer project cwd."""
    import llm_connector.env as env_mod

    pkg = tmp_path / "llm-connector"
    pkg.mkdir()
    (pkg / ".env").write_text("API_ROUTERAI_KEY=sk-from-connector\n", encoding="utf-8")

    consumer = tmp_path / "consumer"
    consumer.mkdir()
    (consumer / ".env").write_text(
        "API_ROUTERAI_KEY=sk-from-consumer\nAPI_VSEGPT_KEY=sk-vsegpt\n",
        encoding="utf-8",
    )

    env_mod._LOADED = False
    monkeypatch.chdir(consumer)
    monkeypatch.setattr(env_mod, "package_root", lambda: pkg)
    monkeypatch.delenv("API_ROUTERAI_KEY", raising=False)
    monkeypatch.delenv("API_VSEGPT_KEY", raising=False)

    ensure_env_loaded(force=True)
    assert os.getenv("API_ROUTERAI_KEY") == "sk-from-connector"
    assert os.getenv("API_VSEGPT_KEY", "") == ""


def test_missing_key_after_env_load(monkeypatch, tmp_path):
    import llm_connector.env as env_mod

    _reset_env_loader(monkeypatch, tmp_path)
    env_mod._LOADED = False
    ensure_env_loaded(force=True)
    with pytest.raises(MissingApiKeyError):
        resolve_api_key(None, _route(), _provider())
