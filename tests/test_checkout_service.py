from __future__ import annotations

from app.schemas import CheckoutConfirmRequest, CheckoutLineItem
from app.services import checkout_service as cs
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


# ── Task 2: persist_basket seam ──

from app.services.checkout_service import CheckoutValidationError, persist_basket  # noqa: E402


def _patch_bq(monkeypatch, *, dup=False, insert=(1, []), raise_validation=False, max_invoice=10):
    monkeypatch.setattr(cs, "_bq_next_invoice", lambda tx: max_invoice + 1)
    monkeypatch.setattr(cs, "_bq_resolve_customer_id", lambda name, ct, tx: 7)

    def _row(structured):
        if raise_validation:
            raise CheckoutValidationError("Quantity melebihi batas wajar")
        return {
            "Invoice": int(structured["invoice"]),
            "StockCode": str(structured["product"])[:3].upper(),
            "Quantity": structured["qty"],
            "Price": float(structured["unit_price"]),
        }

    monkeypatch.setattr(cs, "_bq_validate_row", _row)
    monkeypatch.setattr(cs, "_bq_check_duplicate", lambda inv, sc, tx: dup)
    monkeypatch.setattr(cs, "_bq_insert", lambda rows, tx: insert)


def test_persist_allocates_invoice_when_none(monkeypatch):
    _patch_bq(monkeypatch, insert=(1, []), max_invoice=99)
    res = persist_basket(_items(), "Budi", "Indonesia", None, "t.tx", "t.cust")
    assert res["status"] == "ok" and res["invoice"] == "100"


def test_persist_uses_explicit_invoice(monkeypatch):
    _patch_bq(monkeypatch, insert=(1, []))
    res = persist_basket(_items(), "Budi", "Indonesia", "555", "t.tx", "t.cust")
    assert res["invoice"] == "555" and res["status"] == "ok"


def test_persist_duplicate_only_when_explicit(monkeypatch):
    _patch_bq(monkeypatch, dup=True)
    res = persist_basket(_items(), "Budi", "Indonesia", "555", "t.tx", "t.cust")
    assert res["status"] == "duplicate"


def test_persist_no_dupcheck_when_auto_invoice(monkeypatch):
    _patch_bq(monkeypatch, dup=True, insert=(1, []))  # dup=True diabaikan krn invoice auto
    res = persist_basket(_items(), "Budi", "Indonesia", None, "t.tx", "t.cust")
    assert res["status"] == "ok"


def test_persist_bq_error_on_short_insert(monkeypatch):
    _patch_bq(monkeypatch, insert=(0, ["boom"]))
    res = persist_basket(_items(), "Budi", "Indonesia", None, "t.tx", "t.cust")
    assert res["status"] == "bq_error"


def test_persist_validation_error(monkeypatch):
    _patch_bq(monkeypatch, raise_validation=True)
    res = persist_basket(_items(), "Budi", "Indonesia", None, "t.tx", "t.cust")
    assert res["status"] == "validation_error"
