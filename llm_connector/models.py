# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from llm_connector.exceptions import LlmConnectorError


@dataclass
class ProviderRow:
    id: int
    code: str
    base_url: str
    shared_api_key_env: str
    default_verify_ssl: bool
    is_enabled: bool = True
    extra_json: Optional[Dict[str, Any]] = None
    legacy_api_key_env: Optional[str] = None


@dataclass
class RouteStageRow:
    id: int
    stage: int
    provider: ProviderRow
    model: str
    api_key_env: Optional[str] = None


@dataclass
class RouteChain:
    """Logical route: ordered fallback stages for (script, function_key, model_slot)."""

    head_route_id: int
    project_id: int
    caller_script: str
    function_key: str
    model_slot: int
    stages: List[RouteStageRow]
    error_streak_threshold: int
    max_failures: int
    failure_count: int
    is_suspended: bool
    temperature: float
    max_tokens: Optional[int]
    timeout_sec: int
    max_retries: int
    retry_delay_sec: int
    response_format: Optional[str]
    verify_ssl: Optional[bool]
    api_key_env: Optional[str]
    is_active: bool
    sort_order: int = 0
    comment: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.stages:
            raise ValueError(
                f"RouteChain requires at least one stage: "
                f"{self.caller_script!r} {self.function_key!r} slot={self.model_slot}"
            )

    @property
    def id(self) -> int:
        return self.head_route_id

    @property
    def head_stage(self) -> RouteStageRow:
        if not self.stages:
            raise LlmConnectorError(
                f"RouteChain has no stages: "
                f"{self.caller_script!r} {self.function_key!r} slot={self.model_slot}"
            )
        return self.stages[0]

    @property
    def provider(self) -> ProviderRow:
        return self.head_stage.provider

    @property
    def primary_model(self) -> str:
        return self.head_stage.model


@dataclass
class RouteRow:
    """Backward-compatible view: chain head + legacy fallback columns (deprecated)."""

    id: int
    project_id: int
    caller_script: str
    function_key: str
    model_slot: int
    stage: int
    primary_provider_id: int
    primary_model: str
    same_provider_fallback_model: Optional[str]
    fallback_provider_id: Optional[int]
    fallback_model: Optional[str]
    error_streak_threshold: int
    max_failures: int
    failure_count: int
    is_suspended: bool
    temperature: float
    max_tokens: Optional[int]
    timeout_sec: int
    max_retries: int
    retry_delay_sec: int
    response_format: Optional[str]
    verify_ssl: Optional[bool]
    api_key_env: Optional[str]
    is_active: bool
    provider: ProviderRow
    fallback_provider: Optional[ProviderRow] = None
    stages: List[RouteStageRow] = field(default_factory=list)
    comment: Optional[str] = None


@dataclass
class CompleteImageResult:
    image_bytes: bytes
    route_id: int
    provider_code: str
    model: str
    route_stage: str
    is_fallback: bool
    request_uuid: str
    from_recovery_cache: bool = False
    cost: Optional[float] = None
    latency_ms: Optional[int] = None
    api_key_source: str = "shared_env"
    external_request_id: Optional[str] = None
    raw_response: Any = None


@dataclass
class CompleteResult:
    content: str
    route_id: int
    provider_code: str
    model: str
    route_stage: str
    is_fallback: bool
    request_uuid: str
    from_recovery_cache: bool = False
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost: Optional[float] = None
    latency_ms: Optional[int] = None
    api_key_source: str = "shared_env"
    external_request_id: Optional[str] = None
    raw_response: Any = None


@dataclass
class LogInsert:
    project_id: int
    function_key: str
    route_id: int
    provider_id: int
    model: str
    is_fallback: bool
    latency_ms: int
    deployment_code: str
    api_key_source: str
    status: str
    http_status: Optional[int]
    error_class: Optional[str]
    error_message: Optional[str]
    route_suspended_skip: bool
    from_recovery_cache: bool
    route_stage: str
    external_request_id: Optional[str]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    cost: Optional[float]
    provider_raw_json: Optional[str]
    request_uuid: str


RouteStage = str

STAGE_PRIMARY: RouteStage = "primary"
STAGE_SAME_PROVIDER: RouteStage = "same_provider_fallback"
STAGE_CROSS_PROVIDER: RouteStage = "cross_provider_fallback"

STATUS_SKIPPED_NO_KEY = "skipped_no_key"
STATUS_SKIPPED_PROVIDER_DISABLED = "skipped_provider_disabled"
