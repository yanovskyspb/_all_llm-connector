# -*- coding: utf-8 -*-
from llm_connector.client import _build_stages, _stages_for_attempt
from llm_connector.models import ProviderRow, RouteChain, RouteStageRow, STAGE_PRIMARY


def _provider(code: str, pid: int, enabled: bool = True) -> ProviderRow:
    return ProviderRow(
        id=pid,
        code=code,
        base_url=f"https://{code}.example/v1",
        shared_api_key_env=f"API_{code.upper()}_KEY",
        default_verify_ssl=True,
        is_enabled=enabled,
    )


def _chain(stages_specs) -> RouteChain:
    stages = [
        RouteStageRow(id=100 + i, stage=i, provider=p, model=m)
        for i, (p, m) in enumerate(stages_specs)
    ]
    return RouteChain(
        head_route_id=stages[0].id,
        project_id=1,
        caller_script="test.py",
        function_key="default",
        model_slot=1,
        stages=stages,
        error_streak_threshold=1,
        max_failures=3,
        failure_count=0,
        is_suspended=False,
        temperature=0.0,
        max_tokens=None,
        timeout_sec=60,
        max_retries=1,
        retry_delay_sec=1,
        response_format=None,
        verify_ssl=None,
        api_key_env=None,
        is_active=True,
    )


def test_build_stages_meta_extract_two_stages():
    or_p = _provider("openrouter", 1)
    chain = _chain([(or_p, "glm:free"), (or_p, "openrouter/free")])
    stages = _build_stages(chain)
    assert len(stages) == 2
    assert stages[0][0] == STAGE_PRIMARY
    assert stages[0][2] == "glm:free"
    assert stages[1][0] == "stage_1_openrouter"
    assert stages[1][3] is True


def test_build_stages_full_five_provider_chain():
    providers = [
        _provider("openrouter", 1),
        _provider("openrouter_usa", 2),
        _provider("replicate", 3),
        _provider("routerai", 4),
        _provider("vsegpt", 5),
    ]
    model = "openai/gpt-5-mini"
    chain = _chain([(p, model) for p in providers])
    stages = _build_stages(chain)
    assert len(stages) == 5
    assert stages[0][1].code == "openrouter"
    assert stages[4][1].code == "vsegpt"
    assert all(s[2] == model for s in stages)


def test_stages_for_attempt_skips_primary_when_degraded():
    chain = _chain(
        [
            (_provider("openrouter", 1), "a"),
            (_provider("vsegpt", 2), "a"),
        ]
    )
    stages = _build_stages(chain)
    assert _stages_for_attempt(stages, streak=1, error_streak_threshold=1) == stages[1:]
