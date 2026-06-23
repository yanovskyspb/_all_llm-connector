# -*- coding: utf-8 -*-
"""Load .env into os.environ before API key / DB config reads."""

from __future__ import annotations

import logging
import os
from pathlib import Path

_log = logging.getLogger("llm_connector.env")
_LOADED = False
_WARNED = False


def _search_bases() -> list[Path]:
    bases: list[Path] = []
    explicit = os.getenv("LLM_ENV_FILE", "").strip()
    if explicit:
        bases.append(Path(explicit))
    bases.append(Path(__file__).resolve().parent.parent)
    bases.append(Path.cwd())
    return bases


def ensure_env_loaded(*, override: bool = False, force: bool = False) -> bool:
    """
    Load the first existing .env / .env.local among LLM_ENV_FILE, package root, cwd.

    Idempotent per process unless force=True (used by test dashboard on each request).
    With override=False (default), variables already in os.environ are kept.
    """
    global _LOADED, _WARNED
    if _LOADED and not force:
        return False

    try:
        from dotenv import load_dotenv
    except ImportError:
        if not _WARNED:
            _log.debug("python-dotenv not installed; .env files are not loaded")
            _WARNED = True
        if not force:
            _LOADED = True
        return False

    names = (".env", ".env.local")
    for base in _search_bases():
        if base.is_file():
            load_dotenv(base, override=override)
            if not force:
                _LOADED = True
            return True
        if base.is_dir():
            for name in names:
                path = base / name
                if path.is_file():
                    load_dotenv(path, override=override)
                    if not force:
                        _LOADED = True
                    return True

    if not force:
        _LOADED = True
    return False
