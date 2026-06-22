# -*- coding: utf-8 -*-
"""
Phase 2 placeholder: resilient storage for external VPS (replica read + outbox write).

MVP uses MysqlPrimaryStorage only. This module documents the future contract.
"""

from __future__ import annotations

import os
from typing import Any

from llm_connector.storage.mysql_primary import MysqlPrimaryStorage


class ResilientStorage(MysqlPrimaryStorage):
    """
    Future wrapper: LLM_DB_MODE=auto|normal|degraded|offline.

    - normal: delegate to primary (MysqlPrimaryStorage)
    - degraded: read routes from replica, write logs to SQLite outbox
    - offline: fail fast or in-memory cache with TTL

    Not implemented in MVP — external deployment uses normal via Tailscale first.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.db_mode = os.getenv("LLM_DB_MODE", "normal")

    @property
    def is_external_phase2(self) -> bool:
        return os.getenv("LLM_DEPLOYMENT_CODE", "internal") == "external"
