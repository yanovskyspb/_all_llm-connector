# -*- coding: utf-8 -*-
"""API key resolution — explicit keys never downgrade to shared on HTTP error."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional, Tuple

from llm_connector.exceptions import MissingApiKeyError

if TYPE_CHECKING:
    from llm_connector.models import ProviderRow, RouteRow


def resolve_api_key(
    explicit: Optional[str],
    route: "RouteRow",
    provider: "ProviderRow",
) -> Tuple[str, str]:
    """
    Resolve API key before the first HTTP request.

    Returns (key, source) where source is explicit | route_env | shared_env.
  """
    if explicit and explicit.strip():
        return explicit.strip(), "explicit"
    if route.api_key_env:
        val = os.getenv(route.api_key_env, "").strip()
        if val:
            return val, "route_env"
    env_name = provider.shared_api_key_env or ""
    if env_name:
        val = os.getenv(env_name, "").strip()
        if val:
            return val, "shared_env"
    raise MissingApiKeyError(f"No API key for provider {provider.code!r}")
