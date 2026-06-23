# -*- coding: utf-8 -*-
"""OpenAI-compatible chat request parameters."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from llm_connector.models import ProviderRow


def model_requires_max_completion_tokens(model: str) -> bool:
    """GPT-5 / o-series reject max_tokens; need max_completion_tokens."""
    lower = model.lower()
    if lower.endswith(":free"):
        lower = lower.rsplit(":", 1)[0]
    return any(
        marker in lower
        for marker in (
            "gpt-5",
            "/o1",
            "/o3",
            "/o4",
            "o1-preview",
            "o1-mini",
            "o3-mini",
        )
    )


def omit_temperature_for_provider(provider: ProviderRow, model: str) -> bool:
    """Replicate GPT-5/o chat schema has no temperature."""
    return provider.code == "replicate" and model_requires_max_completion_tokens(model)


def build_chat_completion_kwargs(
    *,
    provider: ProviderRow,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    timeout_sec: int,
    max_tokens: Optional[int],
    response_format: Optional[str],
) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "timeout": timeout_sec,
    }
    if not omit_temperature_for_provider(provider, model):
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        if model_requires_max_completion_tokens(model):
            kwargs["max_completion_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = max_tokens
    if response_format == "json_object":
        kwargs["response_format"] = {"type": "json_object"}
    return kwargs
