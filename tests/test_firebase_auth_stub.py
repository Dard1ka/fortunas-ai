"""Seam Firebase: dev stub opt-in, else not-configured. Real path tak diuji (butuh creds)."""
from __future__ import annotations

import pytest

from app.core import firebase_auth
from app.core.firebase_auth import (
    FirebaseAuthError,
    FirebaseNotConfigured,
    verify_firebase_token,
)


def test_dev_mode_parses_token(monkeypatch):
    monkeypatch.setenv("FORTUNAS_DEV_AUTH", "1")
    monkeypatch.setattr(firebase_auth, "_creds_path", lambda: None)
    assert verify_firebase_token("dev:uid123:+628111") == {
        "firebase_uid": "uid123", "phone_number": "+628111"}


def test_dev_mode_bad_format_raises(monkeypatch):
    monkeypatch.setenv("FORTUNAS_DEV_AUTH", "1")
    monkeypatch.setattr(firebase_auth, "_creds_path", lambda: None)
    with pytest.raises(FirebaseAuthError):
        verify_firebase_token("garbage")


def test_not_configured_raises(monkeypatch):
    monkeypatch.delenv("FORTUNAS_DEV_AUTH", raising=False)
    monkeypatch.setattr(firebase_auth, "_creds_path", lambda: None)
    with pytest.raises(FirebaseNotConfigured):
        verify_firebase_token("dev:uid:+628")
