#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply llm_connector SQL migrations to a MySQL database."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import mysql.connector


def _split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    buf: list[str] = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        buf.append(line)
        if line.rstrip().endswith(";"):
            stmt = "\n".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
    tail = "\n".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def _run_sql_file(cur, sql: str) -> None:
    for stmt in _split_sql_statements(sql):
        cur.execute(stmt)


def main() -> int:
    p = argparse.ArgumentParser(description="Apply llm_connector migrations")
    p.add_argument("--host", default=os.getenv("DB_HOST", "127.0.0.1"))
    p.add_argument("--user", default=os.getenv("DB_USER", "root"))
    p.add_argument("--password", default=os.getenv("DB_PASSWORD", ""))
    p.add_argument("--database", default=os.getenv("DB_DATABASE", "ailenta_parser"))
    args = p.parse_args()

    root = Path(__file__).resolve().parents[1] / "docs" / "migrations"
    files = sorted(root.glob("*.sql"))
    if not files:
        print("No migration files found")
        return 1

    conn = mysql.connector.connect(
        host=args.host,
        user=args.user,
        password=args.password,
        database=args.database,
        charset="utf8mb4",
        use_pure=True,
    )
    cur = conn.cursor()
    try:
        for path in files:
            sql = path.read_text(encoding="utf-8")
            _run_sql_file(cur, sql)
            conn.commit()
            print(f"applied {path.name}")
    finally:
        cur.close()
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
