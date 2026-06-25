from __future__ import annotations

from app.schemas import CheckoutConfirmRequest, CheckoutLineItem
from app.services.checkout_service import resolve_bq_customer_name


def _items():
    return [CheckoutLineItem(product="Kopi", qty=2, unit_price=15000)]


def test_resolve_name_qr_wins():
    req = CheckoutConfirmRequest(items=_items(), customer="walk-in")
    assert resolve_bq_customer_name(req, "Budi") == "Budi"


def test_resolve_name_fallback_request_when_no_qr():
    req = CheckoutConfirmRequest(items=_items(), customer="walk-in")
    assert resolve_bq_customer_name(req, None) == "walk-in"


def test_resolve_name_empty_when_nothing():
    req = CheckoutConfirmRequest(items=_items(), customer="")
    assert resolve_bq_customer_name(req, None) == ""
