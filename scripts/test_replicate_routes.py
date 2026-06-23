#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test every distinct model used on replicate stages in llm_routes.

    pip install -e .
    python scripts/test_replicate_routes.py

Shows which DB models work with native Replicate API (same as complete() stage replicate).
"""
from __future__ import annotations

import argparse
import os
import sys
import time

from llm_connector.db_connection import connect_with_retries
from llm_connector.env import ensure_env_loaded
from llm_connector.replicate_client import run_replicate_prediction

TEST_MSG = [{"role": "user", "content": "Reply with exactly: OK"}]


def main() -> int:
    parser = argparse.ArgumentParser(description="Test all replicate models from llm_routes")
    parser.add_argument(
        "--delay",
        type=float,
        default=12.0,
        help="Seconds between models (Replicate rate limit ~6/min if balance < $5)",
    )
    args = parser.parse_args()

    ensure_env_loaded(override=True, force=True)
    key = os.getenv("API_REPLICATE_KEY", "").strip()
    if not key:
        print("FAIL: API_REPLICATE_KEY not set")
        return 1

    conn = connect_with_retries()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT r.primary_model AS model,
               COUNT(*) AS routes,
               MAX(r.response_format) AS response_format,
               MAX(r.max_tokens) AS max_tokens
        FROM llm_routes r
        JOIN llm_providers p ON p.id = r.primary_provider_id
        WHERE p.code = 'replicate' AND r.is_active = 1
        GROUP BY r.primary_model
        ORDER BY r.primary_model
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("No active replicate routes in DB.")
        return 1

    print(f"Testing {len(rows)} distinct replicate model(s) from llm_routes\n")
    failed = 0
    for i, row in enumerate(rows):
        if i > 0 and args.delay > 0:
            time.sleep(args.delay)
        model = row["model"]
        rf = row["response_format"]
        mt = row["max_tokens"] or 64
        label = f"{model} (routes={row['routes']}, json={rf or '-'})"
        t0 = time.perf_counter()
        try:
            text, _ = run_replicate_prediction(
                model=model,
                api_key=key,
                messages=TEST_MSG,
                max_tokens=int(mt) if mt else 64,
                response_format=rf,
                timeout_sec=120,
            )
            ms = int((time.perf_counter() - t0) * 1000)
            if not text:
                print(f"FAIL {label} — empty response ({ms} ms)")
                failed += 1
            else:
                preview = text[:80] + ("…" if len(text) > 80 else "")
                print(f"OK   {label} — {preview!r} ({ms} ms)")
        except Exception as e:
            ms = int((time.perf_counter() - t0) * 1000)
            print(f"FAIL {label} — {type(e).__name__}: {e} ({ms} ms)")
            failed += 1

    print()
    if failed:
        print(f"{failed}/{len(rows)} model(s) failed. Errors in llm_request_logs are expected for these models.")
        return 1
    print("All replicate route models OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
