"""QR service pure: issue/verify. Expired diuji via patch QR_TTL_SECONDS=-1."""
from __future__ import annotations

import jwt

from app.core.auth import JWT_ALGORITHM, JWT_SECRET
from app.services import qr_service
from app.services.qr_service import issue_qr, verify_qr


def test_issue_qr_shape_and_claims():
    out = issue_qr("cu_abc")
    assert out["ttl_seconds"] == 90
    assert out["nonce"] and out["qr_token"] and out["expires_at"]
    payload = jwt.decode(out["qr_token"], JWT_SECRET, algorithms=[JWT_ALGORITHM])
    assert payload["typ"] == "qr"
    assert payload["customer_user_id"] == "cu_abc"
    assert payload["nonce"] == out["nonce"]


def test_verify_qr_valid():
    out = issue_qr("cu_abc")
    r = verify_qr(out["qr_token"])
    assert r["valid"] is True
    assert r["customer_user_id"] == "cu_abc"
    assert r["nonce"] == out["nonce"]
    assert r["expires_at"]


def test_verify_qr_tampered():
    out = issue_qr("cu_abc")
    r = verify_qr(out["qr_token"] + "x")
    assert r["valid"] is False
    assert r["reason"] == "tampered"


def test_verify_qr_wrong_typ():
    token = jwt.encode({"customer_user_id": "cu_x", "nonce": "n", "typ": "auth"},
                       JWT_SECRET, algorithm=JWT_ALGORITHM)
    assert verify_qr(token)["reason"] == "tampered"


def test_verify_qr_expired(monkeypatch):
    monkeypatch.setattr(qr_service, "QR_TTL_SECONDS", -1)
    out = issue_qr("cu_abc")
    r = verify_qr(out["qr_token"])
    assert r["valid"] is False
    assert r["reason"] == "expired"
