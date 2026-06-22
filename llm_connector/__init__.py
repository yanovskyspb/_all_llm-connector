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
from llm_connector.db_config import get_llm_db_config
from llm_connector.db_connection import close_conn, get_conn, get_cursor
from llm_connector.tables import LlmTableNames

__all__ = [
    "CompleteResult",
    "close_conn",
    "get_cursor",
    "get_llm_db_config",
    "get_conn",
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
