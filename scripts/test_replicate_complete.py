#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Replicate through production complete() — same path as ailenta_parser.

    pip install -e .
    pip install replicate
    python scripts/test_replicate_complete.py

Use the SAME python executable that runs ailenta_parser (prod venv), e.g.:

    cd P:\\ailenta_parser
    pip install -e P:\\_all_llm-connector
    python P:\\_all_llm-connector\\scripts\\test_replicate_complete.py
"""
from __future__ import annotations

import sys
from pathlib import Path

TEST_MSG = [{"role": "user", "content": "Reply with exactly: OK"}]


def main() -> int:
    print("Python:", sys.executable)
    print("llm_connector:", Path(__import__("llm_connector").__file__).parent)

    try:
        import replicate  # noqa: F401

        print("replicate package: OK", replicate.__version__ if hasattr(replicate, "__version__") else "")
    except ImportError:
        print("FAIL: package 'replicate' not installed in THIS python.")
        print("Fix:  pip install replicate")
        print("      or pip install -e P:\\_all_llm-connector")
        return 1

    from llm_connector import MysqlLlmAdapter, complete, get_cursor
    from llm_connector.env import ensure_env_loaded

    ensure_env_loaded(override=True, force=True)

    # Route with replicate stage 2 + openai/gpt-5-nano (exists on Replicate)
    project = "ailenta_parser"
    caller = "prompt_llm_check.py"
    function_key = "default"

    adapter = MysqlLlmAdapter()
    cur = get_cursor()
    if cur is None:
        print("FAIL: no DB connection (check LLM_DB_* in .env)")
        return 1

    print(f"\nCalling complete({caller!r}, replicate is stage 2)...")
    print("(Stages 0–1 may run first if OpenRouter is up.)\n")

    try:
        result = complete(
            adapter,
            cur,
            project_code=project,
            caller_script=caller,
            function_key=function_key,
            model_slot=1,
            messages=TEST_MSG,
            entity_id=None,
            recovery_root=None,
            commit=True,
        )
    finally:
        cur.close()

    if result is None:
        print("FAIL: complete() returned None — check llm_request_logs for replicate stage.")
        print("      SELECT error_message FROM llm_request_logs")
        print("      WHERE route_stage LIKE '%replicate%' ORDER BY id DESC LIMIT 5;")
        return 1

    print(f"OK  provider={result.provider_code!r} model={result.model!r}")
    print(f"    stage={result.route_stage!r} latency={result.latency_ms}ms")
    print(f"    content={result.content[:120]!r}")
    if result.provider_code != "replicate":
        print("\nNote: success via another provider, not replicate.")
        print("Replicate stage was skipped or not reached.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
