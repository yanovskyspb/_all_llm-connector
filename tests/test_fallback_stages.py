# -*- coding: utf-8 -*-
from llm_connector.client import _stages_for_attempt


def test_stages_for_attempt_runs_full_chain_when_healthy():
    stages = [("primary", None, "a", False, None), ("fb", None, "b", True, None)]
    assert _stages_for_attempt(stages, streak=0, error_streak_threshold=1) == stages


def test_stages_for_attempt_skips_primary_when_degraded():
    stages = [("primary", None, "a", False, None), ("fb", None, "b", True, None)]
    assert _stages_for_attempt(stages, streak=1, error_streak_threshold=1) == stages[1:]
