# -*- coding: utf-8 -*-
"""MySQL primary storage for llm_* tables (MVP internal mode)."""

from __future__ import annotations

import json
from typing import Any, List, Optional

from llm_connector.exceptions import RouteNotFoundError
from llm_connector.models import LogInsert, ProviderRow, RouteRow
from llm_connector.tables import LlmTableNames


def _row_provider(row: dict, prefix: str = "") -> ProviderRow:
    p = prefix
    extra = row.get(f"{p}extra_json")
    if isinstance(extra, str) and extra.strip():
        try:
            extra = json.loads(extra)
        except json.JSONDecodeError:
            extra = None
    return ProviderRow(
        id=int(row[f"{p}provider_id"]),
        code=str(row[f"{p}provider_code"]),
        base_url=str(row[f"{p}provider_base_url"]),
        shared_api_key_env=str(row.get(f"{p}provider_shared_api_key_env") or ""),
        default_verify_ssl=bool(row.get(f"{p}provider_default_verify_ssl", 1)),
        extra_json=extra if isinstance(extra, dict) else None,
    )


def _row_to_route(row: dict) -> RouteRow:
    fb_provider = None
    if row.get("fallback_provider_id"):
        fb_provider = ProviderRow(
            id=int(row["fallback_provider_id"]),
            code=str(row["fb_provider_code"]),
            base_url=str(row["fb_provider_base_url"]),
            shared_api_key_env=str(row.get("fb_provider_shared_api_key_env") or ""),
            default_verify_ssl=bool(row.get("fb_provider_default_verify_ssl", 1)),
            extra_json=None,
        )
    return RouteRow(
        id=int(row["id"]),
        project_id=int(row["project_id"]),
        caller_script=str(row["caller_script"]),
        function_key=str(row["function_key"] or "default"),
        model_slot=int(row["model_slot"]),
        primary_provider_id=int(row["primary_provider_id"]),
        primary_model=str(row["primary_model"]),
        same_provider_fallback_model=row.get("same_provider_fallback_model"),
        fallback_provider_id=row.get("fallback_provider_id"),
        fallback_model=row.get("fallback_model"),
        error_streak_threshold=int(row.get("error_streak_threshold") or 1),
        max_failures=int(row.get("max_failures") or 3),
        failure_count=int(row.get("failure_count") or 0),
        is_suspended=bool(row.get("is_suspended")),
        temperature=float(row.get("temperature") if row.get("temperature") is not None else 0.0),
        max_tokens=row.get("max_tokens"),
        timeout_sec=int(row.get("timeout_sec") or 120),
        max_retries=int(row.get("max_retries") or 3),
        retry_delay_sec=int(row.get("retry_delay_sec") or 5),
        response_format=row.get("response_format"),
        verify_ssl=row.get("verify_ssl"),
        api_key_env=row.get("api_key_env"),
        is_active=bool(row.get("is_active", 1)),
        provider=_row_provider(row),
        fallback_provider=fb_provider,
    )


_ROUTE_SELECT = """
SELECT
  r.id, r.project_id, r.caller_script, r.function_key, r.model_slot,
  r.primary_provider_id, r.primary_model, r.same_provider_fallback_model,
  r.fallback_provider_id, r.fallback_model, r.error_streak_threshold,
  r.max_failures, r.failure_count, r.is_suspended, r.temperature, r.max_tokens,
  r.timeout_sec, r.max_retries, r.retry_delay_sec, r.response_format,
  r.verify_ssl, r.api_key_env, r.is_active,
  p.id AS provider_id,
  p.code AS provider_code,
  p.base_url AS provider_base_url,
  p.shared_api_key_env AS provider_shared_api_key_env,
  p.default_verify_ssl AS provider_default_verify_ssl,
  p.extra_json AS provider_extra_json,
  fp.code AS fb_provider_code,
  fp.base_url AS fb_provider_base_url,
  fp.shared_api_key_env AS fb_provider_shared_api_key_env,
  fp.default_verify_ssl AS fb_provider_default_verify_ssl
FROM `{routes}` r
JOIN `{projects}` pr ON pr.id = r.project_id
JOIN `{providers}` p ON p.id = r.primary_provider_id
LEFT JOIN `{providers}` fp ON fp.id = r.fallback_provider_id
WHERE pr.code = %s
  AND r.caller_script = %s
  AND r.function_key = %s
  AND r.model_slot = %s
  AND r.is_active = 1
LIMIT 1
"""

_ROUTE_LIST_SELECT = """
SELECT
  r.id, r.project_id, r.caller_script, r.function_key, r.model_slot,
  r.primary_provider_id, r.primary_model, r.same_provider_fallback_model,
  r.fallback_provider_id, r.fallback_model, r.error_streak_threshold,
  r.max_failures, r.failure_count, r.is_suspended, r.temperature, r.max_tokens,
  r.timeout_sec, r.max_retries, r.retry_delay_sec, r.response_format,
  r.verify_ssl, r.api_key_env, r.is_active,
  p.id AS provider_id,
  p.code AS provider_code,
  p.base_url AS provider_base_url,
  p.shared_api_key_env AS provider_shared_api_key_env,
  p.default_verify_ssl AS provider_default_verify_ssl,
  p.extra_json AS provider_extra_json,
  fp.code AS fb_provider_code,
  fp.base_url AS fb_provider_base_url,
  fp.shared_api_key_env AS fb_provider_shared_api_key_env,
  fp.default_verify_ssl AS fb_provider_default_verify_ssl
FROM `{routes}` r
JOIN `{projects}` pr ON pr.id = r.project_id
JOIN `{providers}` p ON p.id = r.primary_provider_id
LEFT JOIN `{providers}` fp ON fp.id = r.fallback_provider_id
WHERE pr.code = %s
  AND r.caller_script = %s
  AND r.function_key = %s
  AND r.is_active = 1
ORDER BY r.model_slot ASC, r.sort_order ASC, r.id ASC
"""

_ROUTE_OVERVIEW_SELECT = """
SELECT
  r.id, r.project_id, r.caller_script, r.function_key, r.model_slot,
  r.primary_provider_id, r.primary_model, r.same_provider_fallback_model,
  r.fallback_provider_id, r.fallback_model, r.error_streak_threshold,
  r.max_failures, r.failure_count, r.is_suspended, r.temperature, r.max_tokens,
  r.timeout_sec, r.max_retries, r.retry_delay_sec, r.response_format,
  r.verify_ssl, r.api_key_env, r.is_active,
  p.id AS provider_id,
  p.code AS provider_code,
  p.base_url AS provider_base_url,
  p.shared_api_key_env AS provider_shared_api_key_env,
  p.default_verify_ssl AS provider_default_verify_ssl,
  p.extra_json AS provider_extra_json,
  fp.code AS fb_provider_code,
  fp.base_url AS fb_provider_base_url,
  fp.shared_api_key_env AS fb_provider_shared_api_key_env,
  fp.default_verify_ssl AS fb_provider_default_verify_ssl
FROM `{routes}` r
JOIN `{projects}` pr ON pr.id = r.project_id
JOIN `{providers}` p ON p.id = r.primary_provider_id
LEFT JOIN `{providers}` fp ON fp.id = r.fallback_provider_id
WHERE pr.code = %s
  AND r.is_active = 1
ORDER BY r.caller_script ASC, r.function_key ASC, r.model_slot ASC, r.sort_order ASC, r.id ASC
"""


class MysqlPrimaryStorage:
    def __init__(self, tables: LlmTableNames | None = None):
        self.tables = tables or LlmTableNames()

    def load_route(
        self,
        cursor: Any,
        *,
        project_code: str,
        caller_script: str,
        function_key: str,
        model_slot: int = 1,
    ) -> RouteRow:
        fk = function_key or "default"
        sql = _ROUTE_SELECT.format(
            routes=self.tables.routes,
            projects=self.tables.projects,
            providers=self.tables.providers,
        )
        cursor.execute(sql, (project_code, caller_script, fk, model_slot))
        row = cursor.fetchone()
        if not row:
            raise RouteNotFoundError(
                f"No route for {project_code=!r} {caller_script=!r} {fk=!r} slot={model_slot}"
            )
        return _row_to_route(row)

    def load_routes_for_caller(
        self,
        cursor: Any,
        *,
        project_code: str,
        caller_script: str,
        function_key: str,
    ) -> List[RouteRow]:
        fk = function_key or "default"
        sql = _ROUTE_LIST_SELECT.format(
            routes=self.tables.routes,
            projects=self.tables.projects,
            providers=self.tables.providers,
        )
        cursor.execute(sql, (project_code, caller_script, fk))
        rows = cursor.fetchall() or []
        return [_row_to_route(r) for r in rows]

    def load_routes_overview(
        self,
        cursor: Any,
        *,
        project_code: str,
    ) -> List[RouteRow]:
        sql = _ROUTE_OVERVIEW_SELECT.format(
            routes=self.tables.routes,
            projects=self.tables.projects,
            providers=self.tables.providers,
        )
        cursor.execute(sql, (project_code,))
        rows = cursor.fetchall() or []
        return [_row_to_route(r) for r in rows]

    def load_projects(self, cursor: Any) -> List[dict]:
        t = self.tables.projects
        cursor.execute(
            f"SELECT id, code, name FROM `{t}` ORDER BY code ASC",
        )
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
