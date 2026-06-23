# -*- coding: utf-8 -*-
"""Native Replicate Predictions API (official models, e.g. openai/gpt-5-mini)."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from llm_connector.completion_params import model_requires_max_completion_tokens


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
    Call Replicate Predictions API. Returns (text, raw_payload dict for logging).
    """
    try:
        import replicate
    except ImportError as e:
        raise RuntimeError(
            "Provider 'replicate' requires the replicate package: pip install replicate"
        ) from e

    inp = messages_to_replicate_input(
        messages,
        model=model,
        max_tokens=max_tokens,
        response_format=response_format,
    )
    prev = os.environ.get("REPLICATE_API_TOKEN")
    os.environ["REPLICATE_API_TOKEN"] = api_key
    try:
        client = replicate.Client(api_token=api_key, timeout=timeout_sec)
        output = client.run(model, input=inp)
    finally:
        if prev is None:
            os.environ.pop("REPLICATE_API_TOKEN", None)
        else:
            os.environ["REPLICATE_API_TOKEN"] = prev

    text = collect_replicate_output(output).strip()
    raw: Dict[str, Any] = {"input": inp, "output": text}
    try:
        raw["output_repr"] = json.loads(
            json.dumps(output, ensure_ascii=False, default=str)
        )
    except Exception:
        raw["output_repr"] = str(output)
    return text, raw
