# -*- coding: utf-8 -*-
"""MySQL adapter — route loading and log writes (injected cursor)."""

from __future__ import annotations

from typing import Any, List, Optional

from llm_connector.models import LogInsert, RouteRow
from llm_connector.storage.mysql_primary import MysqlPrimaryStorage
from llm_connector.tables import LlmTableNames


class MysqlLlmAdapter:
    """High-level adapter; consumer passes an open MySQL cursor."""

    def __init__(
        self,
        tables: LlmTableNames | None = None,
        storage: Optional[MysqlPrimaryStorage] = None,
    ):
        self.tables = tables or LlmTableNames()
        self._storage = storage or MysqlPrimaryStorage(self.tables)

    def load_route(
        self,
        cursor: Any,
        *,
        project_code: str,
        caller_script: str,
        function_key: str,
        model_slot: int = 1,
    ) -> RouteRow:
        return self._storage.load_route(
            cursor,
            project_code=project_code,
            caller_script=caller_script,
            function_key=function_key,
            model_slot=model_slot,
        )

    def load_routes_for_caller(
        self,
        cursor: Any,
        *,
        project_code: str,
        caller_script: str,
        function_key: str,
    ) -> List[RouteRow]:
        return self._storage.load_routes_for_caller(
            cursor,
            project_code=project_code,
            caller_script=caller_script,
            function_key=function_key,
        )

    def load_routes_overview(
        self,
        cursor: Any,
        *,
        project_code: str,
    ) -> List[RouteRow]:
        return self._storage.load_routes_overview(
            cursor,
            project_code=project_code,
        )

    def load_projects(self, cursor: Any) -> List[dict]:
        return self._storage.load_projects(cursor)

    def insert_log(self, cursor: Any, log: LogInsert) -> None:
        self._storage.insert_log(cursor, log)

    def reset_route_failure(self, cursor: Any, route_id: int) -> None:
        self._storage.reset_route_failure(cursor, route_id)

    def increment_route_failure(self, cursor: Any, route_id: int) -> int:
        return self._storage.increment_route_failure(cursor, route_id)

    def suspend_route(self, cursor: Any, route_id: int, reason: str) -> None:
        self._storage.suspend_route(cursor, route_id, reason)
