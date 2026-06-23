#!/usr/bin/env python3
"""Apply a single migration file by name."""
import argparse
import os
from pathlib import Path

import mysql.connector


def _run_sql_file(cur, sql: str) -> None:
    buf = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        buf.append(line)
        if line.rstrip().endswith(";"):
            stmt = "\n".join(buf).strip()
            if stmt:
                cur.execute(stmt)
            buf = []
    tail = "\n".join(buf).strip()
    if tail:
        cur.execute(tail)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("filename", help="e.g. 007_seed_pre_list_funnel_routes.sql")
    p.add_argument("--host", default=os.getenv("LLM_DB_HOST", os.getenv("DB_HOST", "127.0.0.1")))
    p.add_argument("--user", default=os.getenv("LLM_DB_USER", os.getenv("DB_USER", "root")))
    p.add_argument("--password", default=os.getenv("LLM_DB_PASSWORD", os.getenv("DB_PASSWORD", "")))
    p.add_argument("--database", default=os.getenv("LLM_DB_DATABASE", "_llm_connector"))
    args = p.parse_args()

    path = Path(__file__).resolve().parents[1] / "docs" / "migrations" / args.filename
    conn = mysql.connector.connect(
        host=args.host,
        user=args.user,
        password=args.password,
        database=args.database,
        charset="utf8mb4",
    )
    cur = conn.cursor()
    try:
        _run_sql_file(cur, path.read_text(encoding="utf-8"))
        conn.commit()
        print(f"applied {args.filename}")
    finally:
        cur.close()
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
