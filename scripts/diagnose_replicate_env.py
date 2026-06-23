#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose Replicate + llm_connector in THIS Python (same as ailenta_parser venv).

    P:\\ailenta_parser\\venv\\Scripts\\python.exe P:\\_all_llm-connector\\scripts\\diagnose_replicate_env.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        out = (r.stdout or "") + (r.stderr or "")
        return out.strip() or f"(exit {r.returncode}, no output)"
    except Exception as e:
        return f"ERROR: {e}"


def main() -> int:
    print("=== Python ===")
    print("executable:", sys.executable)
    print("version:   ", sys.version.replace("\n", " "))
    print()

    print("=== import llm_connector ===")
    try:
        import llm_connector
        from llm_connector.replicate_client import model_predictions_url, run_replicate_prediction

        root = Path(llm_connector.__file__).resolve().parent
        print("OK  llm_connector at", root)
        print("    predictions URL example:", model_predictions_url("openai/gpt-5-mini"))
    except ImportError as e:
        print("FAIL", e)
        return 1
    print()

    print("=== pip show llm-connector ===")
    print(_run([sys.executable, "-m", "pip", "show", "llm-connector"]))
    print()

    print("Replicate uses httpx HTTP API — package 'replicate' is NOT required.")
    print("Run: python P:\\_all_llm-connector\\scripts\\test_replicate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
