# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from mysql.connector import Error as MySQLError

from llm_connector.client import _log_error
from llm_connector.db_connection import commit_conn, fresh_cursor, get_conn


def test_commit_conn_uses_cursor_private_connection():
    conn = MagicMock()
    cursor = MagicMock(spec=[])
    cursor._connection = conn
    commit_conn(cursor)
    conn.commit.assert_called_once()


def test_commit_conn_falls_back_to_get_conn(monkeypatch):
    conn = MagicMock()
    monkeypatch.setattr("llm_connector.db_connection.get_conn", lambda: conn)
    commit_conn(None)
    conn.commit.assert_called_once()


def test_get_conn_pings_live_connection(monkeypatch):
    conn = MagicMock()
    conn.is_connected.return_value = True
    monkeypatch.setattr("llm_connector.db_connection._conn", conn)
    assert get_conn() is conn
    conn.ping.assert_called_once_with(reconnect=True, attempts=3, delay=1)


def test_fresh_cursor_reuses_cursor_after_ping(monkeypatch):
    conn = MagicMock()
    cursor = MagicMock()
    cursor._connection = conn
    monkeypatch.setattr("llm_connector.db_connection.get_conn", lambda: conn)
    assert fresh_cursor(cursor) is cursor
    conn.ping.assert_called()


def test_fresh_cursor_replaces_cursor_when_ping_fails(monkeypatch):
    conn = MagicMock()
    conn.ping.side_effect = MySQLError("gone")
    cursor = MagicMock()
    cursor._connection = conn
    new_cursor = MagicMock()
    monkeypatch.setattr("llm_connector.db_connection.get_conn", lambda: conn)
    monkeypatch.setattr("llm_connector.db_connection.get_cursor", lambda: new_cursor)
    assert fresh_cursor(cursor) is new_cursor
    cursor.close.assert_called_once()


def test_log_error_swallows_db_failure(monkeypatch):
    adapter = MagicMock()
    adapter.insert_log.side_effect = RuntimeError("db down")
    chain = MagicMock(project_id=1)
    stage_row = MagicMock(id=1)
    provider = MagicMock(id=1)
    monkeypatch.setattr("llm_connector.client.fresh_cursor", lambda c: c)

    _log_error(
        adapter,
        MagicMock(),
        chain,
        stage_row,
        provider,
        "m",
        False,
        "primary",
        "internal",
        "default",
        "shared_env",
        10,
        ValueError("api fail"),
        True,
    )
