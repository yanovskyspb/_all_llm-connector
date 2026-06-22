#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL connection to the dedicated _llm_connector database.
Owned by the llm_connector package (not the consumer app config).
"""

from __future__ import annotations

import logging
import os
import time

import mysql.connector
from mysql.connector import Error as MySQLError

from llm_connector.db_config import get_llm_db_config

logger = logging.getLogger("llm_connector.db")

_conn = None
MAX_RETRIES = 5
RETRY_DELAYS = [3, 5, 7, 10, 10]


def _get_connect_kwargs():
    cfg = get_llm_db_config()
    kwargs = dict(cfg)
    kwargs["charset"] = "utf8mb4"
    kwargs["use_pure"] = True
    kwargs["connection_timeout"] = int(os.getenv("LLM_DB_CONNECT_TIMEOUT", "10"))
    return kwargs


def _is_conn_alive(conn):
    if conn is None:
        return False
    try:
        return conn.is_connected()
    except Exception:
        return False


def connect_with_retries():
    global _conn
    close_conn()
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            _conn = mysql.connector.connect(**_get_connect_kwargs())
            logger.info("LLM MySQL connected (attempt %d)", attempt)
            return _conn
        except (MySQLError, OSError) as e:
            last_error = e
            logger.warning(
                "LLM MySQL connect failed (attempt %d/%d): %s",
                attempt,
                MAX_RETRIES,
                e,
            )
            if _conn:
                try:
                    _conn.close()
                except Exception:
                    pass
                _conn = None
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                time.sleep(delay)
    logger.error("LLM MySQL connect failed after %d attempts: %s", MAX_RETRIES, last_error)
    return None


def get_conn():
    global _conn
    if not _is_conn_alive(_conn):
        connect_with_retries()
    elif _conn is not None:
        try:
            _conn.ping(reconnect=True, attempts=3, delay=1)
        except MySQLError:
            connect_with_retries()
    return _conn


def fresh_cursor(cursor=None):
    """Return a cursor backed by a live connection (reconnect after idle LLM calls)."""
    conn = get_conn()
    if conn is None:
        return cursor
    if cursor is not None:
        cur_conn = getattr(cursor, "_connection", None)
        if cur_conn is conn:
            try:
                conn.ping(reconnect=True, attempts=3, delay=1)
                return cursor
            except MySQLError:
                pass
        try:
            cursor.close()
        except Exception:
            pass
    return get_cursor()


def get_cursor():
    conn = get_conn()
    if conn is None:
        return None
    return conn.cursor(buffered=True, dictionary=True)


def commit_conn(cursor=None) -> None:
    """Commit LLM DB transaction (mysql.connector cursors expose _connection, not connection)."""
    conn = None
    if cursor is not None:
        conn = getattr(cursor, "connection", None) or getattr(cursor, "_connection", None)
    if conn is None:
        conn = get_conn()
    if conn is not None:
        conn.commit()


def close_conn():
    global _conn
    if _conn:
        try:
            _conn.close()
        except Exception as e:
            logger.warning("Error closing LLM connection: %s", e)
        _conn = None
