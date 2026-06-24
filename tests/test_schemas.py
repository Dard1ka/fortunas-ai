"""TDD untuk kontrak Pydantic v5.0 MVP. Uji PERILAKU VALIDASI, bukan endpoint."""
from __future__ import annotations

import datetime as dt

import pytest
from pydantic import ValidationError

from app.schemas import (
    CheckoutConfirmRequest,
    CheckoutConfirmResponse,
    CheckoutLineItem,
    CustomerBootstrapRequest,
    CustomerProfile,
    CustomerProfileUpdate,
    DeviceTokenRequest,
    DPAPayload,
    DPAUpdateRequest,
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


def test_line_item_autofills_total():
    it = CheckoutLineItem(product="Kopi", qty=3, unit_price=15000)
    assert it.total == 45000


def test_line_item_rejects_zero_qty():
    with pytest.raises(ValidationError):
        CheckoutLineItem(product="Kopi", qty=0, unit_price=15000)


def test_line_item_rejects_empty_product():
    with pytest.raises(ValidationError):
        CheckoutLineItem(product="", qty=1, unit_price=1000)


def test_checkout_requires_at_least_one_item():
    with pytest.raises(ValidationError):
        CheckoutConfirmRequest(items=[])


def test_checkout_grand_total_sums_items():
    req = CheckoutConfirmRequest(
        items=[
            CheckoutLineItem(product="Kopi", qty=2, unit_price=15000),
            CheckoutLineItem(product="Roti", qty=1, unit_price=12000),
        ]
    )
    assert req.grand_total == 42000
    assert req.country == "Indonesia"  # default
    assert req.customer_qr_token is None  # opt-in scan


def test_checkout_response_optional_loyalty_fields_default_none():
    resp = CheckoutConfirmResponse(ok=True, status="ok", reply="sip")
    assert resp.points_earned is None and resp.promo_redeemed is None


def test_dpa_payload_defaults_empty():
    d = DPAPayload()
    assert d.raw_text == "" and d.allowed_rules == [] and d.version == 0


def test_dpa_update_requires_raw_text():
    with pytest.raises(ValidationError):
        DPAUpdateRequest(raw_text="", password="rahasia")


def test_dpa_update_requires_password():
    with pytest.raises(ValidationError):
        DPAUpdateRequest(raw_text="Tidak jual rokok", password="")


def test_dpa_update_valid():
    d = DPAUpdateRequest(
        raw_text="Tidak menjual produk tembakau.",
        forbidden_rules=["rokok", "tembakau"],
        password="rahasia",
    )
    assert "rokok" in d.forbidden_rules


def test_device_token_valid():
    t = DeviceTokenRequest(fcm_token="f" * 20, platform="android")
    assert t.platform == "android" and t.user_type is None


def test_device_token_rejects_bad_platform():
    with pytest.raises(ValidationError):
        DeviceTokenRequest(fcm_token="f" * 20, platform="symbian")


def test_device_token_rejects_short_token():
    with pytest.raises(ValidationError):
        DeviceTokenRequest(fcm_token="x", platform="ios")
