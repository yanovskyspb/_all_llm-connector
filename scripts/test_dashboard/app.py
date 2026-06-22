# -*- coding: utf-8 -*-
"""FastAPI dev server: routes matrix + script-level complete() tests."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

_log = logging.getLogger("uvicorn.error")
_DOTENV_WARNED = False
_ENV_ROOT = Path(__file__).resolve().parents[2]


def _load_env() -> None:
    """Load .env from repo root. Called on import and before API reads keys."""
    global _DOTENV_WARNED
    try:
        from dotenv import load_dotenv
    except ImportError:
        if not _DOTENV_WARNED:
            _log.warning(
                'python-dotenv not installed — .env is ignored. '
                'Run: pip install -e ".[web]"'
            )
            _DOTENV_WARNED = True
        return
    for name in (".env", ".env.local"):
        path = _ENV_ROOT / name
        if path.is_file():
            load_dotenv(path, override=True)


_load_env()

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from llm_connector import MysqlLlmAdapter, complete, get_cursor
from llm_connector.db_config import get_llm_db_config
from llm_connector.exceptions import (
    LlmConnectorError,
    MissingApiKeyError,
    RouteNotFoundError,
    RouteSuspendedError,
)
from llm_connector.key_display import resolve_key_display
from llm_connector.models import RouteRow, RouteStageRow

STATIC_DIR = Path(__file__).resolve().parent / "static"
TEST_MESSAGE = [{"role": "user", "content": "Reply with exactly: OK"}]

app = FastAPI(title="LLM Connector Test Dashboard", docs_url="/api/docs")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_adapter = MysqlLlmAdapter()


def _db_unavailable_detail() -> str:
    cfg = get_llm_db_config()
    return (
        f"MySQL connection failed ({cfg['host']}/{cfg['database']}). "
        "Set LLM_DB_HOST, LLM_DB_USER, LLM_DB_PASSWORD in .env or environment."
    )


def _route_column_key(route: RouteRow) -> str:
    return f"{route.function_key}::{route.model_slot}"


def _stage_to_dict(route: RouteRow, stage: RouteStageRow) -> Dict[str, Any]:
    key_info = resolve_key_display(route, stage.provider)
    return {
        "stage": stage.stage,
        "provider_code": stage.provider.code,
        "model": stage.model,
        "provider_enabled": stage.provider.is_enabled,
        "key": key_info,
    }


def _route_to_dict(route: RouteRow) -> Dict[str, Any]:
    stages = route.stages or []
    key_info = resolve_key_display(route, route.provider)

    return {
        "id": route.id,
        "caller_script": route.caller_script,
        "function_key": route.function_key,
        "model_slot": route.model_slot,
        "column_key": _route_column_key(route),
        "primary": {
            "provider_code": route.provider.code,
            "model": route.primary_model,
        },
        "stages": [_stage_to_dict(route, s) for s in stages],
        "key": key_info,
        "is_suspended": route.is_suspended,
        "is_active": route.is_active,
        "failure_count": route.failure_count,
        "max_failures": route.max_failures,
        "timeout_sec": route.timeout_sec,
        "comment": route.comment,
    }


def _build_table_payload(routes: List[RouteRow]) -> Dict[str, Any]:
    column_keys: List[str] = []
    seen_cols: set[str] = set()
    for route in routes:
        ck = _route_column_key(route)
        if ck not in seen_cols:
            seen_cols.add(ck)
            column_keys.append(ck)

    scripts: Dict[str, List[Dict[str, Any]]] = {}
    for route in routes:
        scripts.setdefault(route.caller_script, []).append(_route_to_dict(route))

    script_rows = []
    for caller_script in sorted(scripts.keys()):
        by_col = {r["column_key"]: r for r in scripts[caller_script]}
        script_rows.append(
            {
                "caller_script": caller_script,
                "routes_by_column": by_col,
            }
        )

    return {
        "columns": column_keys,
        "scripts": script_rows,
        "route_count": len(routes),
    }


class TestScriptRequest(BaseModel):
    project_code: str
    caller_script: str


class TestRouteResult(BaseModel):
    route_id: int
    function_key: str
    model_slot: int
    status: str
    provider_code: Optional[str] = None
    model: Optional[str] = None
    route_stage: Optional[str] = None
    api_key_source: Optional[str] = None
    latency_ms: Optional[int] = None
    content_preview: Optional[str] = None
    error: Optional[str] = None


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/projects")
def list_projects() -> List[Dict[str, Any]]:
    cur = get_cursor()
    if cur is None:
        raise HTTPException(503, _db_unavailable_detail())
    try:
        return _adapter.load_projects(cur)
    finally:
        cur.close()


@app.get("/api/routes")
def list_routes(
    project_code: str = Query("ailenta_parser"),
) -> Dict[str, Any]:
    _load_env()
    cur = get_cursor()
    if cur is None:
        raise HTTPException(503, _db_unavailable_detail())
    try:
        routes = _adapter.load_routes_overview(cur, project_code=project_code)
        payload = _build_table_payload(routes)
        payload["project_code"] = project_code
        return payload
    finally:
        cur.close()


@app.post("/api/test-script")
def test_script(body: TestScriptRequest) -> Dict[str, Any]:
    _load_env()
    cur = get_cursor()
    if cur is None:
        raise HTTPException(503, _db_unavailable_detail())

    prev_deployment = os.environ.get("LLM_DEPLOYMENT_CODE")
    os.environ["LLM_DEPLOYMENT_CODE"] = "test_dashboard"

    results: List[TestRouteResult] = []
    try:
        routes = _adapter.load_routes_overview(cur, project_code=body.project_code)
        script_routes = [
            r
            for r in routes
            if r.caller_script == body.caller_script and r.is_active and not r.is_suspended
        ]
        if not script_routes:
            raise HTTPException(
                404,
                f"No active routes for script {body.caller_script!r}",
            )

        for route in script_routes:
            results.append(_test_single_route(route, body.project_code, cur))
    finally:
        if prev_deployment is None:
            os.environ.pop("LLM_DEPLOYMENT_CODE", None)
        else:
            os.environ["LLM_DEPLOYMENT_CODE"] = prev_deployment
        cur.close()

    return {
        "project_code": body.project_code,
        "caller_script": body.caller_script,
        "results": [r.model_dump() for r in results],
    }


def _test_single_route(
    route: RouteRow,
    project_code: str,
    cur: Any,
) -> TestRouteResult:
    base = {
        "route_id": route.id,
        "function_key": route.function_key,
        "model_slot": route.model_slot,
    }
    try:
        result = complete(
            _adapter,
            cur,
            project_code=project_code,
            caller_script=route.caller_script,
            function_key=route.function_key,
            model_slot=route.model_slot,
            messages=TEST_MESSAGE,
            entity_id=None,
            recovery_root=None,
            commit=True,
        )
        if result is None:
            return TestRouteResult(
                **base,
                status="error",
                error="All fallback stages failed",
            )
        preview = (result.content or "")[:120]
        return TestRouteResult(
            **base,
            status="success",
            provider_code=result.provider_code,
            model=result.model,
            route_stage=result.route_stage,
            api_key_source=result.api_key_source,
            latency_ms=result.latency_ms,
            content_preview=preview,
        )
    except RouteSuspendedError as e:
        return TestRouteResult(**base, status="suspended", error=str(e))
    except MissingApiKeyError as e:
        return TestRouteResult(**base, status="missing_key", error=str(e))
    except RouteNotFoundError as e:
        return TestRouteResult(**base, status="not_found", error=str(e))
    except LlmConnectorError as e:
        return TestRouteResult(**base, status="error", error=str(e))
    except Exception as e:
        return TestRouteResult(**base, status="error", error=f"{type(e).__name__}: {e}")
