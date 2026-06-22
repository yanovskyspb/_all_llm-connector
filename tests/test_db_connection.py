# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from llm_connector.db_connection import commit_conn


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
