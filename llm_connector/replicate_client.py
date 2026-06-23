# -*- coding: utf-8 -*-
"""Replicate Predictions HTTP API (no replicate SDK — works on Python 3.14+)."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import httpx

from llm_connector.completion_params import model_requires_max_completion_tokens

REPLICATE_API_BASE = "https://api.replicate.com/v1"
_POLL_STATUSES = frozenset({"starting", "processing"})


def model_predictions_url(model: str) -> str:
    """Official/community model: owner/name → POST /v1/models/{owner}/{name}/predictions."""
    slug = model.strip()
    if slug.endswith(":free"):
        slug = slug.rsplit(":", 1)[0]
    if "/" not in slug:
        raise ValueError(f"Invalid Replicate model id: {model!r}")
    owner, name = slug.split("/", 1)
    return f"{REPLICATE_API_BASE}/models/{quote(owner, safe='')}/{quote(name, safe='')}/predictions"


def messages_to_replicate_input(
    messages: List[Dict[str, str]],
    *,
    model: str,
    max_tokens: Optional[int],
    response_format: Optional[str],
) -> Dict[str, Any]:
    """Map chat messages to Replicate model input (prompt / system_prompt)."""
    system_parts: List[str] = []
    conv_parts: List[str] = []
    for msg in messages:
        role = (msg.get("role") or "user").strip()
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        if role == "system":
            system_parts.append(content)
        else:
            conv_parts.append(f"{role}: {content}")

    if response_format == "json_object":
        system_parts.append("Respond with valid JSON only.")

    inp: Dict[str, Any] = {"prompt": "\n".join(conv_parts) if conv_parts else "Hello"}
    if system_parts:
        inp["system_prompt"] = "\n".join(system_parts)
    if max_tokens is not None:
        inp["max_completion_tokens"] = max_tokens
    elif model_requires_max_completion_tokens(model):
        inp["max_completion_tokens"] = 4096
    if model_requires_max_completion_tokens(model):
        inp["reasoning_effort"] = "low"
    return inp


def collect_replicate_output(output: Any) -> str:
    if output is None:
        return ""
    if isinstance(output, str):
        return output
    if isinstance(output, (list, tuple)):
        return "".join(collect_replicate_output(part) for part in output)
    if hasattr(output, "__iter__") and not isinstance(output, (dict, bytes)):
        return "".join(collect_replicate_output(part) for part in output)
    return str(output)


def _poll_prediction(
    client: httpx.Client,
    *,
    api_key: str,
    data: Dict[str, Any],
    deadline: float,
) -> Dict[str, Any]:
    poll_url = (data.get("urls") or {}).get("get")
    if not poll_url:
        return data
    headers = {"Authorization": f"Bearer {api_key}"}
    while data.get("status") in _POLL_STATUSES:
        if time.time() >= deadline:
            raise TimeoutError(
                f"Replicate prediction {data.get('id')!r} timed out (status={data.get('status')!r})"
            )
        time.sleep(1.0)
        resp = client.get(poll_url, headers=headers)
        if resp.status_code >= 400:
            raise RuntimeError(f"Replicate poll HTTP {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
    return data


def run_replicate_prediction(
    *,
    model: str,
    api_key: str,
    messages: List[Dict[str, str]],
    max_tokens: Optional[int],
    response_format: Optional[str],
    timeout_sec: int,
) -> Tuple[str, Dict[str, Any]]:
    """
    Call Replicate Predictions API via HTTP. Returns (text, raw_payload dict for logging).
    """
    inp = messages_to_replicate_input(
        messages,
        model=model,
        max_tokens=max_tokens,
        response_format=response_format,
    )
    url = model_predictions_url(model)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Prefer": "wait",
    }
    deadline = time.monotonic() + timeout_sec
    timeout = httpx.Timeout(timeout_sec, connect=30.0)

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, headers=headers, json={"input": inp})
        if resp.status_code >= 400:
            raise RuntimeError(f"Replicate HTTP {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        if data.get("status") in _POLL_STATUSES:
            data = _poll_prediction(
                client, api_key=api_key, data=data, deadline=deadline
            )

    status = data.get("status")
    if status == "failed":
        err = data.get("error") or "prediction failed"
        raise RuntimeError(f"Replicate prediction failed: {err}")
    if status != "succeeded":
        raise RuntimeError(f"Replicate prediction ended with status={status!r}")

    text = collect_replicate_output(data.get("output")).strip()
    raw: Dict[str, Any] = {
        "input": inp,
        "output": text,
        "prediction_id": data.get("id"),
        "status": status,
    }
    try:
        raw["prediction"] = json.loads(json.dumps(data, ensure_ascii=False, default=str))
    except Exception:
        raw["prediction"] = str(data)
    return text, raw
