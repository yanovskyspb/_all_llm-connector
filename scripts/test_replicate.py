#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke-test Replicate (native Predictions API).

Usage (from repo root, after deploy):

    pip install -e .
    python scripts/test_replicate.py

Optional:

    python scripts/test_replicate.py --model openai/gpt-5-nano
    python scripts/test_replicate.py --timeout 180

Requires API_REPLICATE_KEY in .env at repo root (or environment).
"""
from __future__ import annotations

import argparse
import os
import sys
import time


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}…{key[-4:]}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Test Replicate API connectivity")
    parser.add_argument(
        "--model",
        default="openai/gpt-5-mini",
        help="Replicate model id (default: openai/gpt-5-mini)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Request timeout in seconds (default: 120)",
    )
    parser.add_argument(
        "--prompt",
        default="Reply with exactly: OK",
        help="Test user message",
    )
    args = parser.parse_args()

    from llm_connector.env import ensure_env_loaded

    ensure_env_loaded(override=True, force=True)

    key = os.getenv("API_REPLICATE_KEY", "").strip()
    if not key:
        print("FAIL: API_REPLICATE_KEY is not set.")
        print("Add it to .env in the llm-connector repo root.")
        return 1

    print("Replicate connectivity test")
    print(f"  model:   {args.model}")
    print(f"  key:     {_mask_key(key)}")
    print(f"  timeout: {args.timeout}s")
    print()

    # Optional: account endpoint (auth only, fast)
    try:
        import httpx

        t0 = time.perf_counter()
        r = httpx.get(
            "https://api.replicate.com/v1/account",
            headers={"Authorization": f"Bearer {key}"},
            timeout=30,
        )
        ms = int((time.perf_counter() - t0) * 1000)
        if r.status_code == 200:
            print(f"OK  account API ({ms} ms)")
        else:
            print(f"WARN account API ({ms} ms): HTTP {r.status_code}")
            print(f"     {r.text[:200]}")
    except Exception as e:
        print(f"WARN account API: {type(e).__name__}: {e}")

    print()
    print("Calling replicate.run() (same path as llm_connector provider 'replicate')...")

    t0 = time.perf_counter()
    try:
        from llm_connector.replicate_client import run_replicate_prediction

        text, raw = run_replicate_prediction(
            model=args.model,
            api_key=key,
            messages=[{"role": "user", "content": args.prompt}],
            max_tokens=64,
            response_format=None,
            timeout_sec=args.timeout,
        )
        ms = int((time.perf_counter() - t0) * 1000)
    except Exception as e:
        ms = int((time.perf_counter() - t0) * 1000)
        print(f"FAIL prediction ({ms} ms): {type(e).__name__}: {e}")
        return 1

    if not text:
        print(f"FAIL prediction ({ms} ms): empty response")
        print(f"     raw keys: {list(raw.keys())}")
        return 1

    preview = text if len(text) <= 200 else text[:200] + "…"
    print(f"OK  prediction ({ms} ms)")
    print(f"     reply: {preview!r}")
    print()
    print("Replicate is configured correctly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
