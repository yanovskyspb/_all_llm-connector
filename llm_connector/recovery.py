# -*- coding: utf-8 -*-
"""File-based recovery for multi-slot LLM batches."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

RECOVERY_TTL_SEC = 72 * 3600
MAX_FILE_BYTES = 256 * 1024
MAX_DIR_BYTES = 2 * 1024 * 1024 * 1024
_CLEANUP_EVERY_N = 100
_call_counter = 0

_SLOT_SUCCESS = "success"
_SLOT_MISSING = "missing"
_SLOT_ERROR = "error"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def prompt_fingerprint(text: str) -> str:
    digest = hashlib.sha256((text or "").encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _caller_stem(caller_script: str) -> str:
    name = os.path.basename(caller_script)
    stem, _ = os.path.splitext(name)
    return stem or "caller"


def _safe_key(value: str) -> str:
    return re.sub(r"[^\w\-.]+", "_", value)[:120]


def recovery_path(
    recovery_root: str,
    project_code: str,
    caller_script: str,
    function_key: str,
    entity_id: str,
) -> Path:
    stem = _caller_stem(caller_script)
    fname = f"{stem}__{_safe_key(entity_id)}__{_safe_key(function_key)}.json"
    return Path(recovery_root) / project_code / stem / fname


def load_recovery(path: Path, expected_fingerprint: str) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if data.get("prompt_fingerprint") != expected_fingerprint:
        return None
    updated = data.get("updated_at")
    if updated:
        try:
            ts = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - ts
            if age.total_seconds() > RECOVERY_TTL_SEC:
                return None
        except ValueError:
            pass
    return data


def get_slot_content(data: Optional[Dict[str, Any]], model_slot: int) -> Optional[str]:
    if not data:
        return None
    slots = data.get("slots") or {}
    slot = slots.get(str(model_slot)) or {}
    if slot.get("status") == _SLOT_SUCCESS:
        content = slot.get("content")
        return str(content) if content is not None else None
    return None


def write_slot_success(
    path: Path,
    *,
    project_code: str,
    caller_script: str,
    function_key: str,
    entity_id: str,
    prompt_fingerprint_value: str,
    model_slot: int,
    provider: str,
    model: str,
    request_id: Optional[str],
    content: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (OSError, json.JSONDecodeError):
            existing = {}
    if not isinstance(existing, dict):
        existing = {}
    slots = existing.get("slots") if isinstance(existing.get("slots"), dict) else {}
    slots[str(model_slot)] = {
        "status": _SLOT_SUCCESS,
        "provider": provider,
        "model": model,
        "request_id": request_id,
        "created_at": _utc_now_iso(),
        "content": content,
    }
    doc = {
        "project_code": project_code,
        "caller_script": caller_script,
        "function_key": function_key,
        "entity_id": entity_id,
        "prompt_fingerprint": prompt_fingerprint_value,
        "updated_at": _utc_now_iso(),
        "slots": slots,
    }
    _atomic_write_json(path, doc)


def write_slot_error(
    path: Path,
    *,
    project_code: str,
    caller_script: str,
    function_key: str,
    entity_id: str,
    prompt_fingerprint_value: str,
    model_slot: int,
    error_class: str,
    error_message: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (OSError, json.JSONDecodeError):
            existing = {}
    slots = existing.get("slots") if isinstance(existing.get("slots"), dict) else {}
    slots[str(model_slot)] = {
        "status": _SLOT_ERROR,
        "error_class": error_class,
        "error_message": error_message[:500],
        "failed_at": _utc_now_iso(),
    }
    doc = {
        "project_code": project_code,
        "caller_script": caller_script,
        "function_key": function_key,
        "entity_id": entity_id,
        "prompt_fingerprint": prompt_fingerprint_value,
        "updated_at": _utc_now_iso(),
        "slots": slots,
    }
    _atomic_write_json(path, doc)


def delete_recovery(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def required_slots_ready(data: Optional[Dict[str, Any]], required_slots: List[int]) -> bool:
    if not data:
        return False
    slots = data.get("slots") or {}
    for slot in required_slots:
        entry = slots.get(str(slot)) or {}
        if entry.get("status") != _SLOT_SUCCESS:
            return False
    return True


def _atomic_write_json(path: Path, doc: Dict[str, Any]) -> None:
    payload = json.dumps(doc, ensure_ascii=False, indent=2)
    if len(payload.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValueError("recovery file exceeds size limit")
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(payload)
    os.replace(tmp, path)


def maybe_cleanup_recovery_root(recovery_root: str) -> None:
    global _call_counter
    _call_counter += 1
    if _call_counter % _CLEANUP_EVERY_N != 0:
        return
    root = Path(recovery_root)
    if not root.is_dir():
        return
    now = time.time()
    total = 0
    for p in sorted(root.rglob("*.json"), key=lambda x: x.stat().st_mtime):
        try:
            st = p.stat()
            if now - st.st_mtime > RECOVERY_TTL_SEC:
                p.unlink(missing_ok=True)
                continue
            total += st.st_size
            if total > MAX_DIR_BYTES:
                p.unlink(missing_ok=True)
        except OSError:
            continue
