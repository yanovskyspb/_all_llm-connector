# -*- coding: utf-8 -*-
"""API key resolution — explicit keys never downgrade to shared on HTTP error."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Iterator, Optional, Tuple, Union

from llm_connector.env import ensure_env_loaded
from llm_connector.exceptions import MissingApiKeyError

if TYPE_CHECKING:
    from llm_connector.models import ProviderRow, RouteChain, RouteRow

RouteKeySource = Union["RouteRow", "RouteChain"]


def _env_candidates(
    route: RouteKeySource,
    provider: "ProviderRow",
    *,
    stage_api_key_env: Optional[str] = None,
) -> Iterator[Tuple[str, str]]:
    """(source_label, env_var_name) in resolution order."""
    if stage_api_key_env:
        yield "route_env", stage_api_key_env
    if route.api_key_env:
        yield "route_env", route.api_key_env
    if provider.shared_api_key_env:
        yield "shared_env", provider.shared_api_key_env
    legacy = provider.legacy_api_key_env
    if legacy and legacy != provider.shared_api_key_env:
        yield "shared_env", legacy


def resolve_api_key(
    explicit: Optional[str],
    route: RouteKeySource,
    provider: "ProviderRow",
    *,
    stage_api_key_env: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Resolve API key before the first HTTP request.

    Order: explicit → stage route env → chain head route env → provider shared env
    (incl. legacy llm_providers.api_key_env alias).
    Returns (key, source) where source is explicit | route_env | shared_env.
    """
    ensure_env_loaded()

    if explicit and explicit.strip():
        return explicit.strip(), "explicit"
    for source, env_name in _env_candidates(
        route, provider, stage_api_key_env=stage_api_key_env
    ):
        val = os.getenv(env_name, "").strip()
        if val:
            return val, source
    raise MissingApiKeyError(f"No API key for provider {provider.code!r}")
