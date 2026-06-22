# -*- coding: utf-8 -*-
"""API key display helpers for admin UI (masked values, source labels)."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional, TypedDict

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


def resolve_key_display(route: "RouteRow", provider: "ProviderRow") -> KeyDisplayInfo:
    """
    Resolve which key would be used (route_env beats shared_env) and return
    display metadata without exposing the full secret.
    """
    if route.api_key_env:
        val = os.getenv(route.api_key_env, "").strip()
        return KeyDisplayInfo(
            source="route_env",
            label="персональный",
            env_name=route.api_key_env,
            masked_value=mask_key(val) if val else None,
            is_set=bool(val),
        )
    env_name = provider.shared_api_key_env or ""
    val = os.getenv(env_name, "").strip() if env_name else ""
    return KeyDisplayInfo(
        source="shared_env",
        label="общий",
        env_name=env_name or None,
        masked_value=mask_key(val) if val else None,
        is_set=bool(val),
    )
