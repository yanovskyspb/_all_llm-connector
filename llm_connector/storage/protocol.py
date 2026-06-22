# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, List, Optional, Protocol

from llm_connector.models import LogInsert, RouteRow


class LlmStorage(Protocol):
    """Thin storage layer — MVP: MysqlPrimaryStorage; phase 2: ResilientStorage."""

    def load_route_chain(
        self,
        cursor: Any,
        *,
        project_code: str,
        caller_script: str,
        function_key: str,
        model_slot: int = 1,
    ): ...

    def load_route(
        self,
        cursor: Any,
        *,
        project_code: str,
        caller_script: str,
        function_key: str,
        model_slot: int = 1,
    ) -> RouteRow: ...

    def load_routes_for_caller(
        self,
        cursor: Any,
        *,
        project_code: str,
        caller_script: str,
        function_key: str,
    ) -> List[RouteRow]: ...

    def insert_log(self, cursor: Any, log: LogInsert) -> None: ...

    def reset_route_failure(self, cursor: Any, route_id: int) -> None: ...

    def increment_route_failure(self, cursor: Any, route_id: int) -> int: ...

    def suspend_route(self, cursor: Any, route_id: int, reason: str) -> None: ...
