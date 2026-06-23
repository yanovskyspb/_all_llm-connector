# -*- coding: utf-8 -*-
"""API key display helpers for admin UI (masked values, source labels)."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional, TypedDict

from llm_connector.env import ensure_env_loaded
from llm_connector.keys import _env_candidates

if TYPE_CHECKING:
    from llm_connector.models import ProviderRow, RouteRow


class KeyDisplayInfo(TypedDict):
    source: str
    label: str
    env_name: Optional[str]
    masked_value: Optional[str]
    is_set: bool


def mask_key(value: str) -> str:
    if not value:
        return "—"
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}…{value[-4:]}"


def resolve_key_display(
    route: "RouteRow",
    provider: "ProviderRow",
    *,
    stage_api_key_env: Optional[str] = None,
) -> KeyDisplayInfo:
    """
    Resolve which key would be used and return display metadata without exposing
    the full secret. Uses the same candidate order as resolve_api_key().
    """
    ensure_env_loaded()

    for source, env_name in _env_candidates(
        route, provider, stage_api_key_env=stage_api_key_env
    ):
        val = os.getenv(env_name, "").strip()
        if not val:
            continue
        label = "персональный" if source == "route_env" else "общий"
        return KeyDisplayInfo(
            source=source,
            label=label,
            env_name=env_name,
            masked_value=mask_key(val),
            is_set=True,
        )
    return KeyDisplayInfo(
        source="shared_env",
        label="общий",
        env_name=None,
        masked_value=None,
        is_set=False,
    )
