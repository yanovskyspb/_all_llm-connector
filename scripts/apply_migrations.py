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
    p.add_argument("--host", default=os.getenv("LLM_DB_HOST", os.getenv("DB_HOST", "127.0.0.1")))
    p.add_argument("--user", default=os.getenv("LLM_DB_USER", os.getenv("DB_USER", "root")))
    p.add_argument("--password", default=os.getenv("LLM_DB_PASSWORD", os.getenv("DB_PASSWORD", "")))
    p.add_argument(
        "--database",
        default=os.getenv("LLM_DB_DATABASE", "_llm_connector"),
        help="Target database (default: _llm_connector)",
    )
    p.add_argument(
        "--create-database",
        action="store_true",
        default=True,
        help="Run 000_create_database.sql first (default: on)",
    )
    p.add_argument(
        "--no-create-database",
        action="store_false",
        dest="create_database",
        help="Skip CREATE DATABASE step",
    )
    args = p.parse_args()

    root = Path(__file__).resolve().parents[1] / "docs" / "migrations"
    files = sorted(root.glob("*.sql"))
    files = [f for f in files if not f.name.startswith("999_")]
    if not files:
        print("No migration files found")
        return 1

    conn = mysql.connector.connect(
        host=args.host,
        user=args.user,
        password=args.password,
        charset="utf8mb4",
        use_pure=True,
    )
    cur = conn.cursor()
    try:
        if args.create_database:
            create_sql = (root / "000_create_database.sql").read_text(encoding="utf-8")
            _run_sql_file(cur, create_sql)
            conn.commit()
            print("applied 000_create_database.sql")

        cur.execute(f"USE `{args.database}`")
        for path in files:
            if path.name == "000_create_database.sql":
                continue
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
