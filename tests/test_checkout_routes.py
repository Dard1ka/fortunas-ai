# tests/test_checkout_routes.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import auth, checkout, customer
from app.services import checkout_service
from app.services import qr_service

_BOOT = {"firebase_id_token": "xxxxxxxxxx", "username": "Budi", "birth_date": "1995-08-17"}
_ITEMS = [{"product": "Kopi Susu", "qty": 2, "unit_price": 15000},
          {"product": "Roti", "qty": 1, "unit_price": 12000}]


class _FakeBQ:
    """Pengganti persist_basket: catat argumen, balikan status terprogram."""

    def __init__(self, status="ok", invoice="10001"):
        self.status = status
        self.invoice = invoice
        self.calls = []

    def __call__(self, items, customer_name, country, invoice, tx_table, customers_table):
        self.calls.append({"customer_name": customer_name, "items": items, "invoice": invoice})
        inv = (invoice or "").strip() or self.invoice
        if self.status == "ok":
            return {"invoice": inv, "inserted": len(items), "errors": [], "status": "ok"}
        if self.status == "bq_error":
            return {"invoice": inv, "inserted": 0, "errors": ["boom"], "status": "bq_error"}
        if self.status == "duplicate":
            return {"invoice": inv, "inserted": 0, "errors": [], "status": "duplicate"}
        return {"invoice": inv, "inserted": 0, "errors": ["bad"], "status": self.status}


def _client():
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(customer.router)
    app.include_router(checkout.router)
    return TestClient(app)


def _umkm_token(c):
    r = c.post("/auth/register",
               json={"email": "owner@toko.com", "password": "rahasia123", "business_name": "Toko A"})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _customer_token(c, monkeypatch):
    monkeypatch.setattr(customer, "verify_firebase_token",
                        lambda _t: {"firebase_uid": "fb1", "phone_number": "+628"})
    return c.post("/customer/auth/bootstrap", json=_BOOT).json()["access_token"]


def _qr(c, ctoken):
    return c.post("/customer/qr/session",
                  headers={"Authorization": f"Bearer {ctoken}"}).json()["qr_token"]


def test_multi_item_totals(monkeypatch):
    c = _client()
    u = _umkm_token(c)
    monkeypatch.setattr(checkout_service, "persist_basket", _FakeBQ())
    r = c.post("/checkout/confirm", headers={"Authorization": f"Bearer {u}"}, json={"items": _ITEMS})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["ok"] is True and b["status"] == "ok"
    assert b["item_count"] == 2 and b["grand_total"] == 42000
    assert b["customer_user_id"] is None
    assert b["points_earned"] is None and b["promo_redeemed"] is None


def test_dry_run_skips_persist(monkeypatch):
    c = _client()
    u = _umkm_token(c)
    fake = _FakeBQ()
    monkeypatch.setattr(checkout_service, "persist_basket", fake)
    monkeypatch.setenv("CHECKOUT_DRY_RUN", "true")
    r = c.post("/checkout/confirm", headers={"Authorization": f"Bearer {u}"}, json={"items": _ITEMS})
    assert r.json()["status"] == "dry_run" and r.json()["ok"] is True
    assert fake.calls == []


def test_bq_error_returns_not_ok(monkeypatch):
    c = _client()
    u = _umkm_token(c)
    monkeypatch.setattr(checkout_service, "persist_basket", _FakeBQ(status="bq_error"))
    r = c.post("/checkout/confirm", headers={"Authorization": f"Bearer {u}"}, json={"items": _ITEMS})
    assert r.json()["ok"] is False and r.json()["status"] == "bq_error"


def test_explicit_invoice_duplicate(monkeypatch):
    c = _client()
    u = _umkm_token(c)
    monkeypatch.setattr(checkout_service, "persist_basket", _FakeBQ(status="duplicate"))
    r = c.post("/checkout/confirm", headers={"Authorization": f"Bearer {u}"},
               json={"items": _ITEMS, "invoice": "555"})
    b = r.json()
    assert b["ok"] is False and b["status"] == "duplicate" and b["invoice"] == "555"


def test_customer_token_rejected(monkeypatch):
    c = _client()
    ct = _customer_token(c, monkeypatch)
    r = c.post("/checkout/confirm", headers={"Authorization": f"Bearer {ct}"}, json={"items": _ITEMS})
    assert r.status_code == 401


def test_qr_valid_links_membership_and_name_wins(monkeypatch):
    c = _client()
    u = _umkm_token(c)
    ct = _customer_token(c, monkeypatch)
    fake = _FakeBQ()
    monkeypatch.setattr(checkout_service, "persist_basket", fake)
    r = c.post("/checkout/confirm", headers={"Authorization": f"Bearer {u}"},
               json={"items": _ITEMS, "customer": "walk-in", "customer_qr_token": _qr(c, ct)})
    b = r.json()
    assert b["ok"] is True and b["customer_user_id"] is not None
    assert b["is_new_member"] is True and b["member_since"]
    assert fake.calls[-1]["customer_name"] == "Budi"  # QR username menang atas "walk-in"


def test_qr_expired_sale_proceeds_link_skipped(monkeypatch):
    c = _client()
    u = _umkm_token(c)
    ct = _customer_token(c, monkeypatch)
    fake = _FakeBQ()
    monkeypatch.setattr(checkout_service, "persist_basket", fake)
    monkeypatch.setattr(qr_service, "QR_TTL_SECONDS", -1)
    r = c.post("/checkout/confirm", headers={"Authorization": f"Bearer {u}"},
               json={"items": _ITEMS, "customer": "walk-in", "customer_qr_token": _qr(c, ct)})
    b = r.json()
    assert b["ok"] is True and b["status"] == "ok" and b["customer_user_id"] is None
    assert fake.calls[-1]["customer_name"] == "walk-in"  # fallback ke nama request


def test_qr_tampered_sale_proceeds(monkeypatch):
    c = _client()
    u = _umkm_token(c)
    ct = _customer_token(c, monkeypatch)
    monkeypatch.setattr(checkout_service, "persist_basket", _FakeBQ())
    r = c.post("/checkout/confirm", headers={"Authorization": f"Bearer {u}"},
               json={"items": _ITEMS, "customer_qr_token": _qr(c, ct) + "x"})
    assert r.json()["ok"] is True and r.json()["customer_user_id"] is None


def test_qr_replay_second_checkout_link_skipped(monkeypatch):
    c = _client()
    u = _umkm_token(c)
    ct = _customer_token(c, monkeypatch)
    monkeypatch.setattr(checkout_service, "persist_basket", _FakeBQ())
    h = {"Authorization": f"Bearer {u}"}
    qr = _qr(c, ct)
    r1 = c.post("/checkout/confirm", headers=h, json={"items": _ITEMS, "customer_qr_token": qr})
    r2 = c.post("/checkout/confirm", headers=h, json={"items": _ITEMS, "customer_qr_token": qr})
    assert r1.json()["customer_user_id"] is not None
    assert r2.json()["ok"] is True and r2.json()["customer_user_id"] is None


def test_bq_error_does_not_burn_qr(monkeypatch):
    """Invariant write-ordering: sale gagal → nonce TIDAK dikonsumsi → QR masih reusable."""
    c = _client()
    u = _umkm_token(c)
    ct = _customer_token(c, monkeypatch)
    h = {"Authorization": f"Bearer {u}"}
    qr = _qr(c, ct)
    monkeypatch.setattr(checkout_service, "persist_basket", _FakeBQ(status="bq_error"))
    r1 = c.post("/checkout/confirm", headers=h, json={"items": _ITEMS, "customer_qr_token": qr})
    assert r1.json()["status"] == "bq_error"
    monkeypatch.setattr(checkout_service, "persist_basket", _FakeBQ())
    r2 = c.post("/checkout/confirm", headers=h, json={"items": _ITEMS, "customer_qr_token": qr})
    assert r2.json()["ok"] is True and r2.json()["customer_user_id"] is not None
