# -*- coding: utf-8 -*-
"""Physical MySQL table names for the LLM connector layer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LlmTableNames:
    projects: str = "llm_projects"
    providers: str = "llm_providers"
    routes: str = "llm_routes"
    request_logs: str = "llm_request_logs"
