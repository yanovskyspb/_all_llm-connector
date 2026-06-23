# -*- coding: utf-8 -*-
"""FastAPI dev server: routes matrix + script-level complete() tests."""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Generator, List, Optional

import mysql.connector
from mysql.connector import Error as MySQLError

_log = logging.getLogger("uvicorn.error")


def _load_env() -> None:
    """Reload .env from llm-connector package root (see llm_connector.env)."""
    from llm_connector.env import ensure_env_loaded

    ensure_env_loaded(override=True, force=True)


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


@contextmanager
def _dashboard_cursor() -> Generator[Any, None, None]:
    """Separate MySQL connection per HTTP request (safe under FastAPI thread pool)."""
    cfg = get_llm_db_config()
    kwargs = dict(cfg)
    kwargs["charset"] = "utf8mb4"
    kwargs["use_pure"] = True
    kwargs["connection_timeout"] = int(os.getenv("LLM_DB_CONNECT_TIMEOUT", "10"))
    conn = None
    cur = None
    try:
        conn = mysql.connector.connect(**kwargs)
        cur = conn.cursor(buffered=True, dictionary=True)
        yield cur
    except MySQLError as e:
        raise HTTPException(503, f"{_db_unavailable_detail()} ({e})") from e
    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _db_unavailable_detail() -> str:
    cfg = get_llm_db_config()
    return (
        f"MySQL connection failed ({cfg['host']}/{cfg['database']}). "
        "Set LLM_DB_HOST, LLM_DB_USER, LLM_DB_PASSWORD in .env or environment."
    )


def _route_column_key(route: RouteRow) -> str:
    return f"{route.function_key}::{route.model_slot}"


def _stage_to_dict(route: RouteRow, stage: RouteStageRow) -> Dict[str, Any]:
    key_info = resolve_key_display(
        route,
        stage.provider,
        stage_api_key_env=stage.api_key_env,
    )
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


def _serialize_log_row(row: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, (datetime, date)):
            out[key] = value.isoformat(sep=" ", timespec="seconds")
        elif isinstance(value, Decimal):
            out[key] = float(value)
        else:
            out[key] = value
    return out


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
    with _dashboard_cursor() as cur:
        return _adapter.load_projects(cur)


@app.get("/api/log-scripts")
def list_log_scripts(
    project_code: Optional[str] = Query(None),
) -> List[Dict[str, Any]]:
    with _dashboard_cursor() as cur:
        rows = _adapter.load_log_scripts(cur, project_code=project_code or None)
        out: List[Dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            last_at = item.get("last_at")
            if isinstance(last_at, (datetime, date)):
                item["last_at"] = last_at.isoformat(sep=" ", timespec="seconds")
            out.append(item)
        return out


@app.get("/api/logs")
def list_logs(
    project_code: Optional[str] = Query(None),
    caller_script: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    since_id: Optional[int] = Query(None, ge=1),
) -> Dict[str, Any]:
    with _dashboard_cursor() as cur:
        rows = _adapter.load_request_logs(
            cur,
            project_code=project_code or None,
            caller_script=caller_script or None,
            limit=limit,
            since_id=since_id,
        )
        items = [_serialize_log_row(r) for r in rows]
        max_id = max((int(r["id"]) for r in items), default=since_id or 0)
        newest_at = items[0]["created_at"] if items else None
        return {
            "items": items,
            "count": len(items),
            "max_id": max_id,
            "newest_at": newest_at,
            "project_code": project_code,
            "caller_script": caller_script,
            "fetched_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
        }


@app.get("/api/routes")
def list_routes(
    project_code: str = Query("ailenta_parser"),
) -> Dict[str, Any]:
    _load_env()
    with _dashboard_cursor() as cur:
        routes = _adapter.load_routes_overview(cur, project_code=project_code)
        payload = _build_table_payload(routes)
        payload["project_code"] = project_code
        return payload


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
