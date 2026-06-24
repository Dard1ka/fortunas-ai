"""TDD untuk kontrak Pydantic v5.0 MVP. Uji PERILAKU VALIDASI, bukan endpoint."""
from __future__ import annotations

import datetime as dt

import pytest
from pydantic import ValidationError

from app.schemas import (
    CustomerBootstrapRequest,
    CustomerProfile,
    CustomerProfileUpdate,
    QRSessionResponse,
    QRValidateRequest,
    QRValidateResponse,
)


def test_bootstrap_accepts_valid_payload():
    req = CustomerBootstrapRequest(
        firebase_id_token="x" * 20, username="  Budi  ", birth_date="1995-08-17"
    )
    assert req.username == "Budi"  # di-trim
    assert req.birth_date == "1995-08-17"


def test_bootstrap_rejects_short_username():
    with pytest.raises(ValidationError):
        CustomerBootstrapRequest(
            firebase_id_token="x" * 20, username="A", birth_date="1995-08-17"
        )


def test_bootstrap_rejects_garbage_birth_date():
    with pytest.raises(ValidationError):
        CustomerBootstrapRequest(
            firebase_id_token="x" * 20, username="Budi", birth_date="17 Agustus"
        )


def test_bootstrap_rejects_future_birth_date():
    future = (dt.date.today() + dt.timedelta(days=1)).isoformat()
    with pytest.raises(ValidationError):
        CustomerBootstrapRequest(
            firebase_id_token="x" * 20, username="Budi", birth_date=future
        )


def test_bootstrap_rejects_short_token():
    with pytest.raises(ValidationError):
        CustomerBootstrapRequest(
            firebase_id_token="short", username="Budi", birth_date="1995-08-17"
        )


def test_profile_update_allows_all_none():
    upd = CustomerProfileUpdate()
    assert upd.username is None and upd.birth_date is None


def test_profile_update_rejects_short_username():
    with pytest.raises(ValidationError):
        CustomerProfileUpdate(username="A")


def test_profile_dump_uses_snake_case():
    p = CustomerProfile(customer_user_id="cu_1", username="Budi")
    assert "customer_user_id" in p.model_dump()


def test_qr_session_defaults_ttl_90():
    s = QRSessionResponse(
        qr_token="t" * 20, nonce="n1", issued_at="2026-06-24T10:00:00+07:00",
        expires_at="2026-06-24T10:01:30+07:00",
    )
    assert s.ttl_seconds == 90


def test_qr_validate_request_rejects_short_token():
    with pytest.raises(ValidationError):
        QRValidateRequest(customer_qr_token="x")


def test_qr_validate_response_invalid_carries_reason():
    r = QRValidateResponse(valid=False, reason="expired")
    assert r.valid is False and r.customer_user_id is None and r.reason == "expired"
