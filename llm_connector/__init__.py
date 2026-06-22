# -*- coding: utf-8 -*-
"""LLM connector: DB-backed routing, logging, recovery."""

from llm_connector.adapter.mysql import MysqlLlmAdapter
from llm_connector.client import complete, get_routes_for_caller, assert_bundle_not_suspended
from llm_connector.exceptions import (
    LlmConnectorError,
    MissingApiKeyError,
    RouteNotFoundError,
    RouteSuspendedError,
)
from llm_connector.keys import resolve_api_key
from llm_connector.models import CompleteResult
from llm_connector.tables import LlmTableNames

__all__ = [
    "CompleteResult",
    "LlmConnectorError",
    "LlmTableNames",
    "MissingApiKeyError",
    "MysqlLlmAdapter",
    "RouteNotFoundError",
    "RouteSuspendedError",
    "assert_bundle_not_suspended",
    "complete",
    "get_routes_for_caller",
    "resolve_api_key",
]
