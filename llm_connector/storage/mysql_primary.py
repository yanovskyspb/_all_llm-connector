# -*- coding: utf-8 -*-
"""MySQL primary storage for llm_* tables (MVP internal mode)."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from llm_connector.exceptions import RouteNotFoundError
from llm_connector.models import LogInsert, ProviderRow, RouteChain, RouteRow, RouteStageRow
from llm_connector.tables import LlmTableNames


def _row_provider(row: dict, prefix: str = "") -> ProviderRow:
    p = prefix
    extra = row.get(f"{p}extra_json")
    if isinstance(extra, str) and extra.strip():
        try:
            extra = json.loads(extra)
        except json.JSONDecodeError:
            extra = None
    enabled = row.get(f"{p}provider_is_enabled")
    if enabled is None:
        enabled = row.get("provider_is_enabled", 1)
    return ProviderRow(
        id=int(row[f"{p}provider_id"]),
        code=str(row[f"{p}provider_code"]),
        base_url=str(row[f"{p}provider_base_url"]),
        shared_api_key_env=str(row.get(f"{p}provider_shared_api_key_env") or ""),
        default_verify_ssl=bool(row.get(f"{p}provider_default_verify_ssl", 1)),
        is_enabled=bool(enabled),
        extra_json=extra if isinstance(extra, dict) else None,
        legacy_api_key_env=row.get(f"{p}provider_legacy_api_key_env"),
    )


def _row_to_stage(row: dict) -> RouteStageRow:
    return RouteStageRow(
        id=int(row["id"]),
        stage=int(row.get("stage") or 0),
        provider=_row_provider(row),
        model=str(row["primary_model"]),
        api_key_env=row.get("api_key_env"),
    )


def _rows_to_chain(rows: List[dict]) -> RouteChain:
    if not rows:
        raise ValueError("empty chain rows")
    rows = sorted(rows, key=lambda r: int(r.get("stage") or 0))
    head = rows[0]
    stages = [_row_to_stage(r) for r in rows]
    return RouteChain(
        head_route_id=int(head["id"]),
        project_id=int(head["project_id"]),
        caller_script=str(head["caller_script"]),
        function_key=str(head["function_key"] or "default"),
        model_slot=int(head["model_slot"]),
        stages=stages,
        error_streak_threshold=int(head.get("error_streak_threshold") or 1),
        max_failures=int(head.get("max_failures") or 3),
        failure_count=int(head.get("failure_count") or 0),
        is_suspended=bool(head.get("is_suspended")),
        temperature=float(head.get("temperature") if head.get("temperature") is not None else 0.0),
        max_tokens=head.get("max_tokens"),
        timeout_sec=int(head.get("timeout_sec") or 120),
        max_retries=int(head.get("max_retries") or 3),
        retry_delay_sec=int(head.get("retry_delay_sec") or 5),
        response_format=head.get("response_format"),
        verify_ssl=head.get("verify_ssl"),
        api_key_env=head.get("api_key_env"),
        is_active=bool(head.get("is_active", 1)),
        sort_order=int(head.get("sort_order") or 0),
        comment=head.get("comment"),
    )


def _chain_to_route_row(chain: RouteChain) -> RouteRow:
    head = chain.head_stage
    return RouteRow(
        id=chain.head_route_id,
        project_id=chain.project_id,
        caller_script=chain.caller_script,
        function_key=chain.function_key,
        model_slot=chain.model_slot,
        stage=0,
        primary_provider_id=head.provider.id,
        primary_model=head.model,
        same_provider_fallback_model=None,
        fallback_provider_id=None,
        fallback_model=None,
        error_streak_threshold=chain.error_streak_threshold,
        max_failures=chain.max_failures,
        failure_count=chain.failure_count,
        is_suspended=chain.is_suspended,
        temperature=chain.temperature,
        max_tokens=chain.max_tokens,
        timeout_sec=chain.timeout_sec,
        max_retries=chain.max_retries,
        retry_delay_sec=chain.retry_delay_sec,
        response_format=chain.response_format,
        verify_ssl=chain.verify_ssl,
        api_key_env=chain.api_key_env,
        is_active=chain.is_active,
        provider=head.provider,
        fallback_provider=None,
        stages=list(chain.stages),
        comment=chain.comment,
    )


_ROUTE_STAGE_SELECT = """
SELECT
  r.id, r.project_id, r.caller_script, r.function_key, r.model_slot, r.stage,
  r.primary_provider_id, r.primary_model, r.same_provider_fallback_model,
  r.fallback_provider_id, r.fallback_model, r.error_streak_threshold,
  r.max_failures, r.failure_count, r.is_suspended, r.temperature, r.max_tokens,
  r.timeout_sec, r.max_retries, r.retry_delay_sec, r.response_format,
  r.verify_ssl, r.api_key_env, r.is_active, r.sort_order, r.comment,
  p.id AS provider_id,
  p.code AS provider_code,
  p.base_url AS provider_base_url,
  p.shared_api_key_env AS provider_shared_api_key_env,
  p.api_key_env AS provider_legacy_api_key_env,
  p.default_verify_ssl AS provider_default_verify_ssl,
  p.is_enabled AS provider_is_enabled,
  p.extra_json AS provider_extra_json
FROM `{routes}` r
JOIN `{projects}` pr ON pr.id = r.project_id
JOIN `{providers}` p ON p.id = r.primary_provider_id
WHERE pr.code = %s
  AND r.is_active = 1
"""


class MysqlPrimaryStorage:
    def __init__(self, tables: LlmTableNames | None = None):
        self.tables = tables or LlmTableNames()

    def _fetch_stage_rows(
        self,
        cursor: Any,
        project_code: str,
        *,
        caller_script: Optional[str] = None,
        function_key: Optional[str] = None,
        model_slot: Optional[int] = None,
    ) -> List[dict]:
        sql = _ROUTE_STAGE_SELECT.format(
            routes=self.tables.routes,
            projects=self.tables.projects,
            providers=self.tables.providers,
        )
        params: List[Any] = [project_code]
        if caller_script is not None:
            sql += " AND r.caller_script = %s"
            params.append(caller_script)
        if function_key is not None:
            sql += " AND r.function_key = %s"
            params.append(function_key or "default")
        if model_slot is not None:
            sql += " AND r.model_slot = %s"
            params.append(model_slot)
        sql += " ORDER BY r.caller_script ASC, r.function_key ASC, r.model_slot ASC, r.stage ASC, r.id ASC"
        cursor.execute(sql, tuple(params))
        return list(cursor.fetchall() or [])

    def _group_chains(self, rows: List[dict]) -> List[RouteChain]:
        groups: Dict[Tuple[str, str, int], List[dict]] = {}
        for row in rows:
            key = (
                str(row["caller_script"]),
                str(row["function_key"] or "default"),
                int(row["model_slot"]),
            )
            groups.setdefault(key, []).append(row)
        chains = [_rows_to_chain(g) for g in groups.values()]
        chains.sort(
            key=lambda c: (c.caller_script, c.function_key, c.model_slot, c.sort_order),
        )
        return chains

    def load_route_chain(
        self,
        cursor: Any,
        *,
        project_code: str,
        caller_script: str,
        function_key: str,
        model_slot: int = 1,
    ) -> RouteChain:
        fk = function_key or "default"
        rows = self._fetch_stage_rows(
            cursor,
            project_code,
            caller_script=caller_script,
            function_key=fk,
            model_slot=model_slot,
        )
        if not rows:
            raise RouteNotFoundError(
                f"No route for {project_code=!r} {caller_script=!r} {fk=!r} slot={model_slot}"
            )
        return _rows_to_chain(rows)

    def load_route(
        self,
        cursor: Any,
        *,
        project_code: str,
        caller_script: str,
        function_key: str,
        model_slot: int = 1,
    ) -> RouteRow:
        chain = self.load_route_chain(
            cursor,
            project_code=project_code,
            caller_script=caller_script,
            function_key=function_key,
            model_slot=model_slot,
        )
        return _chain_to_route_row(chain)

    def load_routes_for_caller(
        self,
        cursor: Any,
        *,
        project_code: str,
        caller_script: str,
        function_key: str,
    ) -> List[RouteRow]:
        fk = function_key or "default"
        rows = self._fetch_stage_rows(
            cursor,
            project_code,
            caller_script=caller_script,
            function_key=fk,
        )
        return [_chain_to_route_row(c) for c in self._group_chains(rows)]

    def load_route_chains_overview(
        self,
        cursor: Any,
        *,
        project_code: str,
    ) -> List[RouteChain]:
        rows = self._fetch_stage_rows(cursor, project_code)
        return self._group_chains(rows)

    def load_routes_overview(
        self,
        cursor: Any,
        *,
        project_code: str,
    ) -> List[RouteRow]:
        return [
            _chain_to_route_row(c)
            for c in self.load_route_chains_overview(cursor, project_code=project_code)
        ]

    def load_projects(self, cursor: Any) -> List[dict]:
        t = self.tables.projects
        cursor.execute(
            f"SELECT id, code, name FROM `{t}` ORDER BY code ASC",
        )
        return list(cursor.fetchall() or [])

    def load_request_logs(
        self,
        cursor: Any,
        *,
        project_code: Optional[str] = None,
        caller_script: Optional[str] = None,
        limit: int = 100,
        since_id: Optional[int] = None,
    ) -> List[dict]:
        """Recent LLM request logs with project/script/provider names (not raw ids)."""
        t_logs = self.tables.request_logs
        t_projects = self.tables.projects
        t_routes = self.tables.routes
        t_providers = self.tables.providers

        sql = f"""
        SELECT
          l.id,
          l.created_at,
          p.code AS project_code,
          p.name AS project_name,
          r.caller_script,
          l.function_key,
          r.model_slot,
          prov.code AS provider_code,
          l.model,
          l.status,
          l.latency_ms,
          l.route_stage,
          l.is_fallback,
          l.deployment_code,
          l.api_key_source,
          l.http_status,
          l.error_class,
          l.error_message,
          l.route_suspended_skip,
          l.from_recovery_cache,
          l.prompt_tokens,
          l.completion_tokens,
          l.total_tokens,
          l.cost
        FROM `{t_logs}` l
        JOIN `{t_projects}` p ON p.id = l.project_id
        JOIN `{t_routes}` r ON r.id = l.route_id
        JOIN `{t_providers}` prov ON prov.id = l.provider_id
        WHERE 1=1
        """
        params: List[Any] = []
        if project_code:
            sql += " AND p.code = %s"
            params.append(project_code)
        if caller_script:
            sql += " AND r.caller_script = %s"
            params.append(caller_script)
        if since_id is not None:
            sql += " AND l.id > %s"
            params.append(since_id)
            sql += " ORDER BY l.id ASC"
        else:
            sql += " ORDER BY l.id DESC"
        sql += " LIMIT %s"
        params.append(max(1, min(int(limit), 500)))

        cursor.execute(sql, tuple(params))
        rows = list(cursor.fetchall() or [])
        if since_id is None:
            return rows
        rows.reverse()
        return rows

    def load_log_scripts(
        self,
        cursor: Any,
        *,
        project_code: Optional[str] = None,
    ) -> List[dict]:
        """Distinct caller_script values seen in request logs (with last activity)."""
        t_logs = self.tables.request_logs
        t_projects = self.tables.projects
        t_routes = self.tables.routes

        sql = f"""
        SELECT
          r.caller_script,
          MAX(l.id) AS last_id,
          MAX(l.created_at) AS last_at,
          COUNT(*) AS log_count
        FROM `{t_logs}` l
        JOIN `{t_projects}` p ON p.id = l.project_id
        JOIN `{t_routes}` r ON r.id = l.route_id
        WHERE 1=1
        """
        params: List[Any] = []
        if project_code:
            sql += " AND p.code = %s"
            params.append(project_code)
        sql += " GROUP BY r.caller_script ORDER BY last_id DESC"
        cursor.execute(sql, tuple(params))
        return list(cursor.fetchall() or [])

    def insert_log(self, cursor: Any, log: LogInsert) -> None:
        t = self.tables.request_logs
        cursor.execute(
            f"""
            INSERT INTO `{t}` (
              created_at, project_id, function_key, route_id,
              provider_id, model, is_fallback, latency_ms, deployment_code,
              api_key_source, status, http_status, error_class, error_message,
              route_suspended_skip, from_recovery_cache, route_stage,
              external_request_id, prompt_tokens, completion_tokens, total_tokens,
              cost, provider_raw_json, request_uuid
            ) VALUES (
              NOW(), %s, %s, %s,
              %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s,
              %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s
            )
            """,
            (
                log.project_id,
                log.function_key,
                log.route_id,
                log.provider_id,
                log.model,
                int(log.is_fallback),
                log.latency_ms,
                log.deployment_code,
                log.api_key_source,
                log.status,
                log.http_status,
                log.error_class,
                (log.error_message or "")[:500] if log.error_message else None,
                int(log.route_suspended_skip),
                int(log.from_recovery_cache),
                log.route_stage,
                log.external_request_id,
                log.prompt_tokens,
                log.completion_tokens,
                log.total_tokens,
                log.cost,
                log.provider_raw_json,
                log.request_uuid,
            ),
        )

    def reset_route_failure(self, cursor: Any, route_id: int) -> None:
        t = self.tables.routes
        cursor.execute(
            f"UPDATE `{t}` SET failure_count = 0, updated_at = NOW() WHERE id = %s",
            (route_id,),
        )

    def increment_route_failure(self, cursor: Any, route_id: int) -> int:
        t = self.tables.routes
        cursor.execute(
            f"UPDATE `{t}` SET failure_count = failure_count + 1, updated_at = NOW() WHERE id = %s",
            (route_id,),
        )
        cursor.execute(f"SELECT failure_count FROM `{t}` WHERE id = %s", (route_id,))
        row = cursor.fetchone()
        return int(row["failure_count"] if row else 0)

    def suspend_route(self, cursor: Any, route_id: int, reason: str) -> None:
        t = self.tables.routes
        cursor.execute(
            f"""
            UPDATE `{t}`
            SET is_suspended = 1,
                suspended_at = NOW(),
                suspend_reason = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (reason[:255], route_id),
        )
