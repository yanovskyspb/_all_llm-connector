# -*- coding: utf-8 -*-
"""Parse token usage and cost from OpenAI-compatible responses."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple


def parse_usage(response: Any) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[float]]:
    usage = getattr(response, "usage", None)
    if usage is None and isinstance(response, dict):
        usage = response.get("usage")
    if usage is None:
        return None, None, None, None

    def _get(obj: Any, key: str) -> Optional[int]:
        if obj is None:
            return None
        if isinstance(obj, dict):
            val = obj.get(key)
        else:
            val = getattr(obj, key, None)
        try:
            return int(val) if val is not None else None
        except (TypeError, ValueError):
            return None

    prompt = _get(usage, "prompt_tokens")
    completion = _get(usage, "completion_tokens")
    total = _get(usage, "total_tokens")
    if total is None and prompt is not None and completion is not None:
        total = prompt + completion

    cost = None
    if isinstance(usage, dict):
        cost = usage.get("cost")
    else:
        cost = getattr(usage, "cost", None)
    try:
        cost_f = float(cost) if cost is not None else None
    except (TypeError, ValueError):
        cost_f = None

    return prompt, completion, total, cost_f


def response_to_raw_json(response: Any) -> Optional[str]:
    try:
        if hasattr(response, "model_dump"):
            return json.dumps(response.model_dump(), ensure_ascii=False, default=str)
        if hasattr(response, "to_dict"):
            return json.dumps(response.to_dict(), ensure_ascii=False, default=str)
        return json.dumps(response, ensure_ascii=False, default=str)
    except Exception:
        return None
