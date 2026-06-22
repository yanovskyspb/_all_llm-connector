#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2: replay outbox_logs from external VPS to primary internal MySQL.

MVP internal does not use outbox. Run on external only when LLM_DB_MODE=degraded.

Usage (future):
  LLM_DB_WRITE_DSN=mysql://... LLM_DB_OUTBOX_PATH=runtime/llm_outbox.db \\
    python scripts/sync_outbox_to_primary.py
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    if os.getenv("LLM_DEPLOYMENT_CODE", "internal") != "external":
        print("sync_outbox_to_primary: skipped (not external deployment)")
        return 0
    print(
        "Phase 2 not implemented: SQLite outbox replay to primary. "
        "See docs/ARCHITECTURE.md",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
