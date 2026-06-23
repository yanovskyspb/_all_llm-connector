# -*- coding: utf-8 -*-
"""Load .env into os.environ before API key / DB config reads."""

from __future__ import annotations

import logging
import os
from pathlib import Path

_log = logging.getLogger("llm_connector.env")
_LOADED = False
_WARNED = False

_ENV_NAMES = (".env", ".env.local")


def package_root() -> Path:
    """Repository root of llm-connector (where API keys .env lives)."""
    return Path(__file__).resolve().parent.parent


def _env_files_to_load() -> list[tuple[Path, bool]]:
    """
    (path, override) in load order.

    Only this package's .env files are used — never consumer app cwd.
    Optional LLM_ENV_FILE may override values after the package files.
    """
    files: list[tuple[Path, bool]] = []
    root = package_root()
    for name in _ENV_NAMES:
        path = root / name
        if path.is_file():
            files.append((path, False))

    explicit = os.getenv("LLM_ENV_FILE", "").strip()
    if explicit:
        p = Path(explicit)
        if p.is_file():
            files.append((p, True))
        elif p.is_dir():
            for name in _ENV_NAMES:
                path = p / name
                if path.is_file():
                    files.append((path, True))
    return files


def ensure_env_loaded(*, override: bool = False, force: bool = False) -> bool:
    """
    Load .env / .env.local from the llm-connector package root only.

    Consumer projects (ailenta_parser, etc.) are intentionally excluded: all
    provider API keys and LLM_DB_* settings belong in this repo's .env.

    Idempotent per process unless force=True (test dashboard reloads on each request).
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

    loaded_any = False
    for path, file_override in _env_files_to_load():
        load_dotenv(path, override=override or file_override)
        loaded_any = True

    if not force:
        _LOADED = True
    return loaded_any
