"""Single-use nonce: consume atomik + purge. SQLite in-memory (conftest)."""
from __future__ import annotations

from app.qr_nonce_repo import consume_nonce, purge_expired


def test_consume_then_replay():
    assert consume_nonce("n1", "2999-01-01T00:00:00+00:00") is True
    assert consume_nonce("n1", "2999-01-01T00:00:00+00:00") is False


def test_purge_expired():
    consume_nonce("old", "2000-01-01T00:00:00+00:00")
    consume_nonce("new", "2999-01-01T00:00:00+00:00")
    assert purge_expired("2026-06-25T00:00:00+00:00") == 1
    assert consume_nonce("new", "2999-01-01T00:00:00+00:00") is False  # 'new' masih ada
