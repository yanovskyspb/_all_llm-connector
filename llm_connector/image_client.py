# -*- coding: utf-8 -*-
"""Image generation with DB routing and fallback chain (OpenRouter Images API)."""

from __future__ import annotations

import base64
import json
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

import httpx

from llm_connector.adapter.mysql import MysqlLlmAdapter
from llm_connector.client import (
    _build_stages,
    _is_auth_error,
    _log_error,
    _log_skip,
    _record_failure,
    _run_db,
    _stages_for_attempt,
    _streak,
    _verify_ssl,
)
from llm_connector.db_connection import commit_conn, fresh_cursor
from llm_connector.exceptions import MissingApiKeyError, RouteSuspendedError
from llm_connector.keys import resolve_api_key
from llm_connector.models import (
    STATUS_SKIPPED_NO_KEY,
    STATUS_SKIPPED_PROVIDER_DISABLED,
    CompleteImageResult,
    LogInsert,
    ProviderRow,
    RouteChain,
    RouteStageRow,
)

logger = logging.getLogger("llm_connector.image_client")

_DEFAULT_IMAGE_SIZE = "1344x768"
StageTuple = Tuple[str, ProviderRow, str, bool, RouteStageRow]


def complete_image(
    adapter: MysqlLlmAdapter,
    cursor: Any,
    *,
    project_code: str,
    caller_script: str,
    function_key: str,
    prompt: str,
    model_slot: int = 1,
    api_key: Optional[str] = None,
    entity_id: Optional[str] = None,
    recovery_root: Optional[str] = None,
    commit: bool = True,
) -> Optional[CompleteImageResult]:
    """
    Run one image generation for a configured route chain.

    Returns None if all retries/stages fail. Raises RouteSuspendedError if route suspended.
    Recovery cache is not used for binary image payloads.
    """
    del entity_id, recovery_root  # reserved for future file-based image recovery

    chain = adapter.load_route_chain(
        cursor,
        project_code=project_code,
        caller_script=caller_script,
        function_key=function_key,
        model_slot=model_slot,
    )
    if chain.is_suspended:
        raise RouteSuspendedError(
            f"Route {chain.head_route_id} suspended: {caller_script} slot={model_slot}"
        )

    fk = function_key or "default"
    deployment_code = os.getenv("LLM_DEPLOYMENT_CODE", "internal")
    explicit_key = api_key.strip() if api_key and api_key.strip() else None

    stages = _build_stages(chain)
    streak = _streak.get(chain.head_route_id, 0)
    stages_to_try = _stages_for_attempt(stages, streak, chain.error_streak_threshold)

    last_error: Optional[Exception] = None
    for stage_name, provider, model, is_fallback, stage_row in stages_to_try:
        if not provider.is_enabled:
            _log_skip(
                adapter,
                cursor,
                chain,
                stage_row,
                provider,
                model,
                is_fallback,
                stage_name,
                deployment_code,
                fk,
                STATUS_SKIPPED_PROVIDER_DISABLED,
                "Provider disabled in database",
                commit=commit,
            )
            continue

        try:
            key, key_source = resolve_api_key(
                explicit_key,
                chain,
                provider,
                stage_api_key_env=stage_row.api_key_env,
            )
        except MissingApiKeyError as e:
            last_error = e
            _log_skip(
                adapter,
                cursor,
                chain,
                stage_row,
                provider,
                model,
                is_fallback,
                stage_name,
                deployment_code,
                fk,
                STATUS_SKIPPED_NO_KEY,
                str(e),
                commit=commit,
            )
            continue

        result = _call_image_stage(
            adapter=adapter,
            cursor=cursor,
            chain=chain,
            stage_row=stage_row,
            provider=provider,
            model=model,
            prompt=prompt,
            api_key=key,
            api_key_source=key_source,
            explicit_key=explicit_key,
            stage_name=stage_name,
            is_fallback=is_fallback,
            deployment_code=deployment_code,
            function_key=fk,
            commit=commit,
        )
        if result is not None:
            _streak[chain.head_route_id] = 0
            _run_db(
                cursor,
                commit,
                lambda cur: adapter.reset_route_failure(cur, chain.head_route_id),
            )
            return result
        last_error = RuntimeError(f"stage {stage_name} failed")

    streak = _streak.get(chain.head_route_id, 0) + 1
    _streak[chain.head_route_id] = streak
    if last_error:
        logger.debug("complete_image failed: %s", last_error)
    return None


def _openrouter_images_url(provider: ProviderRow) -> str:
    base = (provider.base_url or "").rstrip("/")
    if base.endswith("/images"):
        return base
    return f"{base}/images"


def _openrouter_image_payload(model: str, prompt: str) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"model": model, "prompt": prompt, "n": 1}
    if model.startswith("sourceful/"):
        payload["resolution"] = "1K"
        payload["aspect_ratio"] = "16:9"
    else:
        payload["size"] = _DEFAULT_IMAGE_SIZE
        if model.startswith("black-forest-labs/"):
            payload["output_format"] = "png"
    return payload


def _download_url(url: str, *, verify: bool, timeout_sec: int) -> bytes:
    timeout = httpx.Timeout(timeout_sec, connect=30.0)
    with httpx.Client(timeout=timeout, verify=verify, follow_redirects=True) as client:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            return b"".join(resp.iter_bytes())


def _parse_openrouter_image_response(
    data: Dict[str, Any],
    *,
    verify: bool,
    timeout_sec: int,
) -> Tuple[bytes, Optional[float], Optional[str]]:
    items = data.get("data") or []
    if not items:
        raise ValueError(f"OpenRouter image response missing data: {data!r}")

    item = items[0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"]), None, None
    if item.get("url"):
        return _download_url(str(item["url"]), verify=verify, timeout_sec=timeout_sec), None, None
    raise ValueError(f"OpenRouter image item missing b64_json/url: {item!r}")


def _call_image_stage(
    *,
    adapter: MysqlLlmAdapter,
    cursor: Any,
    chain: RouteChain,
    stage_row: RouteStageRow,
    provider: ProviderRow,
    model: str,
    prompt: str,
    api_key: str,
    api_key_source: str,
    explicit_key: Optional[str],
    stage_name: str,
    is_fallback: bool,
    deployment_code: str,
    function_key: str,
    commit: bool,
) -> Optional[CompleteImageResult]:
    if provider.code not in ("openrouter", "openrouter_usa"):
        _log_skip(
            adapter,
            cursor,
            chain,
            stage_row,
            provider,
            model,
            is_fallback,
            stage_name,
            deployment_code,
            function_key,
            STATUS_SKIPPED_PROVIDER_DISABLED,
            f"Image generation not implemented for provider {provider.code!r}",
            commit=commit,
        )
        return None

    verify = _verify_ssl(chain, provider)
    url = _openrouter_images_url(provider)
    payload = _openrouter_image_payload(model, prompt)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ailenta.local/generate-images",
        "X-Title": "llm_connector complete_image",
    }
    timeout = httpx.Timeout(chain.timeout_sec, connect=30.0)

    last_exc: Optional[Exception] = None
    for attempt in range(1, chain.max_retries + 1):
        t0 = time.perf_counter()
        try:
            with httpx.Client(timeout=timeout, verify=verify) as client:
                resp = client.post(url, headers=headers, json=payload)
            latency_ms = int((time.perf_counter() - t0) * 1000)
            if resp.status_code >= 400:
                raise RuntimeError(f"OpenRouter HTTP {resp.status_code}: {resp.text[:500]}")
            data = resp.json()
            image_bytes, _, _ = _parse_openrouter_image_response(
                data,
                verify=verify,
                timeout_sec=chain.timeout_sec,
            )
            if not image_bytes:
                raise ValueError("Empty image bytes from provider")

            usage = data.get("usage") or {}
            cost = usage.get("cost")
            if cost is not None:
                try:
                    cost = float(cost)
                except (TypeError, ValueError):
                    cost = None

            ext_id = data.get("id")
            raw_json = json.dumps(data, ensure_ascii=False, default=str)
            log_uuid = str(uuid.uuid4())
            log_row = LogInsert(
                project_id=chain.project_id,
                function_key=function_key,
                route_id=stage_row.id,
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
                prompt_tokens=None,
                completion_tokens=None,
                total_tokens=None,
                cost=cost,
                provider_raw_json=raw_json,
                request_uuid=log_uuid,
            )
            _run_db(cursor, commit, lambda cur: adapter.insert_log(cur, log_row))
            return CompleteImageResult(
                image_bytes=image_bytes,
                route_id=stage_row.id,
                provider_code=provider.code,
                model=model,
                route_stage=stage_name,
                is_fallback=is_fallback,
                request_uuid=log_uuid,
                cost=cost,
                latency_ms=latency_ms,
                api_key_source=api_key_source,
                external_request_id=ext_id,
                raw_response=data,
            )
        except Exception as e:
            last_exc = e
            latency_ms = int((time.perf_counter() - t0) * 1000)
            if explicit_key and _is_auth_error(e):
                _log_error(
                    adapter,
                    cursor,
                    chain,
                    stage_row,
                    provider,
                    model,
                    is_fallback,
                    stage_name,
                    deployment_code,
                    function_key,
                    api_key_source,
                    latency_ms,
                    e,
                    commit,
                )
                raise
            if attempt < chain.max_retries:
                time.sleep(chain.retry_delay_sec)
                continue
            _log_error(
                adapter,
                cursor,
                chain,
                stage_row,
                provider,
                model,
                is_fallback,
                stage_name,
                deployment_code,
                function_key,
                api_key_source,
                latency_ms,
                e,
                commit,
            )
            _record_failure(adapter, cursor, chain, str(e), commit=commit)
            return None
    return None
