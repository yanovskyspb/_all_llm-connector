# -*- coding: utf-8 -*-
"""Resolve LLM connector MySQL DSN from environment."""

from __future__ import annotations

import os


def get_llm_db_config() -> dict:
    """
    Dedicated LLM connector database (separate from consumer app DB).

    Env: LLM_DB_HOST, LLM_DB_USER, LLM_DB_PASSWORD, LLM_DB_DATABASE (default _llm_connector).
    Falls back to DB_HOST / DB_USER / DB_PASSWORD only for host/credentials, never database name.
    """
    return {
        "host": os.getenv("LLM_DB_HOST", os.getenv("DB_HOST", "192.168.170.221")),
        "user": os.getenv("LLM_DB_USER", os.getenv("DB_USER", "root")),
        "password": os.getenv("LLM_DB_PASSWORD", os.getenv("DB_PASSWORD", "")),
        "database": os.getenv("LLM_DB_DATABASE", "_llm_connector"),
    }
