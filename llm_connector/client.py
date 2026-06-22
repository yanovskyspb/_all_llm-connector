# -*- coding: utf-8 -*-
"""Core LLM completion with DB routing, fallback chain, logging, recovery."""

from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

import httpx
from openai import OpenAI

from llm_connector.adapter.mysql import MysqlLlmAdapter
from llm_connector.exceptions import (
    MissingApiKeyError,
    RouteNotFoundError,
    RouteSuspendedError,
)
from llm_connector.keys import resolve_api_key
from llm_connector.models import (
    STAGE_CROSS_PROVIDER,
    STAGE_PRIMARY,
    STAGE_SAME_PROVIDER,
    CompleteResult,
    LogInsert,
    ProviderRow,
    RouteRow,
)
from llm_connector.recovery import (
    get_slot_content,
    load_recovery,
    maybe_cleanup_recovery_root,
    prompt_fingerprint,
    recovery_path,
    write_slot_error,
    write_slot_success,
)
from llm_connector.usage import parse_usage, response_to_raw_json

# In-process consecutive failure streak per route_id (MVP).
_streak: Dict[int, int] = {}

_AUTH_ERROR_MARKERS = (
    "401",
    "403",
    "invalid_api_key",
    "incorrect api key",
    "authentication",
    "insufficient_quota",
    "billing",
)


def get_routes_for_caller(
    adapter: MysqlLlmAdapter,
    cursor: Any,
    *,
    project_code: str,
    caller_script: str,
    function_key: str,
) -> List[RouteRow]:
    return adapter.load_routes_for_caller(
        cursor,
        project_code=project_code,
        caller_script=caller_script,
        function_key=function_key,
    )


def assert_bundle_not_suspended(routes: List[RouteRow]) -> None:
    suspended = [r for r in routes if r.is_suspended]
    if suspended:
        slots = ", ".join(str(r.model_slot) for r in suspended)
        raise RouteSuspendedError(f"Suspended model_slot(s): {slots}")


def complete(
    adapter: MysqlLlmAdapter,
    cursor: Any,
    *,
    project_code: str,
    caller_script: str,
    function_key: str,
    messages: List[Dict[str, str]],
    model_slot: int = 1,
    api_key: Optional[str] = None,
    entity_id: Optional[str] = None,
    recovery_root: Optional[str] = None,
    prompt_text_for_fingerprint: Optional[str] = None,
    max_tokens_override: Optional[int] = None,
    temperature_override: Optional[float] = None,
    commit: bool = True,
) -> Optional[CompleteResult]:
    """
    Run one LLM completion for a configured route.

    Returns None if all retries/stages fail. Raises RouteSuspendedError if route suspended.
    """
    route = adapter.load_route(
        cursor,
        project_code=project_code,
        caller_script=caller_script,
        function_key=function_key,
        model_slot=model_slot,
    )
    if route.is_suspended:
        raise RouteSuspendedError(
            f"Route {route.id} suspended: {caller_script} slot={model_slot}"
        )

    fk = function_key or "default"
    fingerprint = prompt_fingerprint(
        prompt_text_for_fingerprint
        if prompt_text_for_fingerprint is not None
        else _messages_to_text(messages)
    )
    rec_path = None
    if entity_id and recovery_root:
        maybe_cleanup_recovery_root(recovery_root)
        rec_path = recovery_path(recovery_root, project_code, caller_script, fk, str(entity_id))
        cached = load_recovery(rec_path, fingerprint)
        cached_content = get_slot_content(cached, model_slot)
        if cached_content is not None:
            return CompleteResult(
                content=cached_content,
                route_id=route.id,
                provider_code=route.provider.code,
                model=route.primary_model,
                route_stage=STAGE_PRIMARY,
                is_fallback=False,
                request_uuid=str(uuid.uuid4()),
                from_recovery_cache=True,
                api_key_source="explicit" if api_key else "shared_env",
            )

    request_uuid = str(uuid.uuid4())
    deployment_code = os.getenv("LLM_DEPLOYMENT_CODE", "internal")
    explicit_key = api_key.strip() if api_key and api_key.strip() else None

    stages = _build_stages(route)
    streak = _streak.get(route.id, 0)
    if streak >= route.error_streak_threshold and len(stages) > 1:
        stages_to_try = stages[1:]
    else:
        stages_to_try = stages[:1]

    last_error: Optional[Exception] = None
    for stage_name, provider, model, is_fallback in stages_to_try:
        try:
            key, key_source = resolve_api_key(explicit_key, route, provider)
        except MissingApiKeyError as e:
            last_error = e
            _record_failure(adapter, cursor, route, str(e), commit=commit)
            continue

        result = _call_stage(
            adapter=adapter,
            cursor=cursor,
            route=route,
            provider=provider,
            model=model,
            messages=messages,
            api_key=key,
            api_key_source=key_source,
            explicit_key=explicit_key,
            stage_name=stage_name,
            is_fallback=is_fallback,
            request_uuid=request_uuid,
            deployment_code=deployment_code,
            function_key=fk,
            max_tokens_override=max_tokens_override,
            temperature_override=temperature_override,
            commit=commit,
        )
        if result is not None:
            _streak[route.id] = 0
            adapter.reset_route_failure(cursor, route.id)
            if commit:
                cursor.connection.commit()
            if rec_path is not None and entity_id:
                write_slot_success(
                    rec_path,
                    project_code=project_code,
                    caller_script=caller_script,
                    function_key=fk,
                    entity_id=str(entity_id),
                    prompt_fingerprint_value=fingerprint,
                    model_slot=model_slot,
                    provider=result.provider_code,
                    model=result.model,
                    request_id=result.external_request_id,
                    content=result.content,
                )
            return result
        last_error = RuntimeError(f"stage {stage_name} failed")

    streak = _streak.get(route.id, 0) + 1
    _streak[route.id] = streak

    if rec_path is not None and entity_id and last_error:
        write_slot_error(
            rec_path,
            project_code=project_code,
            caller_script=caller_script,
            function_key=fk,
            entity_id=str(entity_id),
            prompt_fingerprint_value=fingerprint,
            model_slot=model_slot,
            error_class=type(last_error).__name__,
            error_message=str(last_error),
        )
    return None


def _messages_to_text(messages: List[Dict[str, str]]) -> str:
    return "\n".join(f"{m.get('role','user')}: {m.get('content','')}" for m in messages)


def _build_stages(
    route: RouteRow,
) -> List[Tuple[str, ProviderRow, str, bool]]:
    stages: List[Tuple[str, ProviderRow, str, bool]] = [
        (STAGE_PRIMARY, route.provider, route.primary_model, False),
    ]
    if route.same_provider_fallback_model:
        stages.append(
            (STAGE_SAME_PROVIDER, route.provider, route.same_provider_fallback_model, True)
        )
    if route.fallback_provider and route.fallback_model:
        stages.append(
            (STAGE_CROSS_PROVIDER, route.fallback_provider, route.fallback_model, True)
        )
    return stages


def _verify_ssl(route: RouteRow, provider: ProviderRow) -> bool:
    if route.verify_ssl is not None:
        return bool(route.verify_ssl)
    return bool(provider.default_verify_ssl)


def _call_stage(
    *,
    adapter: MysqlLlmAdapter,
    cursor: Any,
    route: RouteRow,
    provider: ProviderRow,
    model: str,
    messages: List[Dict[str, str]],
    api_key: str,
    api_key_source: str,
    explicit_key: Optional[str],
    stage_name: str,
    is_fallback: bool,
    request_uuid: str,
    deployment_code: str,
    function_key: str,
    max_tokens_override: Optional[int],
    temperature_override: Optional[float],
    commit: bool,
) -> Optional[CompleteResult]:
    verify = _verify_ssl(route, provider)
    max_tokens = max_tokens_override if max_tokens_override is not None else route.max_tokens
    temperature = (
        temperature_override if temperature_override is not None else route.temperature
    )
    http_client = httpx.Client(verify=verify)
    client = OpenAI(api_key=api_key, base_url=provider.base_url, http_client=http_client)

    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "timeout": route.timeout_sec,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if route.response_format == "json_object":
        kwargs["response_format"] = {"type": "json_object"}

    last_exc: Optional[Exception] = None
    for attempt in range(1, route.max_retries + 1):
        t0 = time.perf_counter()
        try:
            response = client.chat.completions.create(**kwargs)
            latency_ms = int((time.perf_counter() - t0) * 1000)
            text = (response.choices[0].message.content or "").strip()
            if not text:
                raise ValueError("Empty content from provider")
            pt, ct, tt, cost = parse_usage(response)
            ext_id = getattr(response, "id", None)
            raw_json = response_to_raw_json(response)
            adapter.insert_log(
                cursor,
                LogInsert(
                    project_id=route.project_id,
                    function_key=function_key,
                    route_id=route.id,
                    provider_id=provider.id,
                    model=model,
                    is_fallback=is_fallback,
                    latency_ms=latency_ms,
                    deployment_code=deployment_code,
                    api_key_source=api_key_source,
                    status="success",
                    http_status=200,
                    error_class=None,
                    error_message=None,
                    route_suspended_skip=False,
                    from_recovery_cache=False,
                    route_stage=stage_name,
                    external_request_id=ext_id,
                    prompt_tokens=pt,
                    completion_tokens=ct,
                    total_tokens=tt,
                    cost=cost,
                    provider_raw_json=raw_json,
                    request_uuid=request_uuid,
                ),
            )
            if commit:
                cursor.connection.commit()
            return CompleteResult(
                content=text,
                route_id=route.id,
                provider_code=provider.code,
                model=model,
                route_stage=stage_name,
                is_fallback=is_fallback,
                request_uuid=request_uuid,
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=tt,
                cost=cost,
                latency_ms=latency_ms,
                api_key_source=api_key_source,
                external_request_id=ext_id,
                raw_response=response,
            )
        except Exception as e:
            last_exc = e
            latency_ms = int((time.perf_counter() - t0) * 1000)
            if explicit_key and _is_auth_error(e):
                _log_error(
                    adapter,
                    cursor,
                    route,
                    provider,
                    model,
                    is_fallback,
                    stage_name,
                    request_uuid,
                    deployment_code,
                    function_key,
                    api_key_source,
                    latency_ms,
                    e,
                    commit,
                )
                raise  # no downgrade to shared key
            if attempt < route.max_retries:
                time.sleep(route.retry_delay_sec)
                continue
            _log_error(
                adapter,
                cursor,
                route,
                provider,
                model,
                is_fallback,
                stage_name,
                request_uuid,
                deployment_code,
                function_key,
                api_key_source,
                latency_ms,
                e,
                commit,
            )
            _record_failure(adapter, cursor, route, str(e), commit=commit)
            return None
    return None


def _is_auth_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(m in msg for m in _AUTH_ERROR_MARKERS)


def _log_error(
    adapter: MysqlLlmAdapter,
    cursor: Any,
    route: RouteRow,
    provider: ProviderRow,
    model: str,
    is_fallback: bool,
    stage_name: str,
    request_uuid: str,
    deployment_code: str,
    function_key: str,
    api_key_source: str,
    latency_ms: int,
    exc: Exception,
    commit: bool,
) -> None:
    http_status = getattr(exc, "status_code", None)
    adapter.insert_log(
        cursor,
        LogInsert(
            project_id=route.project_id,
            function_key=function_key,
            route_id=route.id,
            provider_id=provider.id,
            model=model,
            is_fallback=is_fallback,
            latency_ms=latency_ms,
            deployment_code=deployment_code,
            api_key_source=api_key_source,
            status="error",
            http_status=http_status,
            error_class=type(exc).__name__,
            error_message=str(exc)[:500],
            route_suspended_skip=False,
            from_recovery_cache=False,
            route_stage=stage_name,
            external_request_id=None,
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            cost=None,
            provider_raw_json=None,
            request_uuid=request_uuid,
        ),
    )
    if commit:
        cursor.connection.commit()


def _record_failure(
    adapter: MysqlLlmAdapter,
    cursor: Any,
    route: RouteRow,
    reason: str,
    *,
    commit: bool,
) -> None:
    count = adapter.increment_route_failure(cursor, route.id)
    if count >= route.max_failures:
        adapter.suspend_route(cursor, route.id, reason[:255])
    if commit:
        cursor.connection.commit()
