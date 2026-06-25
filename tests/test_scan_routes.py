"""Scan QR (UMKM-auth): valid/replay/expired/tampered/unknown + silang principal. App minimal."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import auth, customer, scan
from app.services import qr_service

_BOOT = {"firebase_id_token": "xxxxxxxxxx", "username": "Budi", "birth_date": "1995-08-17"}


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(customer.router)
    app.include_router(scan.router)
    return TestClient(app)


def _umkm_token(c) -> str:
    r = c.post("/auth/register",
               json={"email": "owner@toko.com", "password": "rahasia123", "business_name": "Toko A"})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _customer_token(c, monkeypatch) -> str:
    monkeypatch.setattr(customer, "verify_firebase_token",
                        lambda _t: {"firebase_uid": "fb1", "phone_number": "+628"})
    return c.post("/customer/auth/bootstrap", json=_BOOT).json()["access_token"]


def _qr(c, ctoken) -> str:
    return c.post("/customer/qr/session",
                  headers={"Authorization": f"Bearer {ctoken}"}).json()["qr_token"]


def test_scan_valid_creates_member(monkeypatch):
    c = _client()
    u, ct = _umkm_token(c), _customer_token(c, monkeypatch)
    r = c.post("/umkm/customer/scan/validate", headers={"Authorization": f"Bearer {u}"},
               json={"customer_qr_token": _qr(c, ct)})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["valid"] is True and b["is_new_member"] is True
    assert b["username"] == "Budi" and b["member_since"]


def test_scan_replay(monkeypatch):
    c = _client()
    u, ct = _umkm_token(c), _customer_token(c, monkeypatch)
    h = {"Authorization": f"Bearer {u}"}
    qr = _qr(c, ct)
    c.post("/umkm/customer/scan/validate", headers=h, json={"customer_qr_token": qr})
    r = c.post("/umkm/customer/scan/validate", headers=h, json={"customer_qr_token": qr})
    assert r.json()["valid"] is False and r.json()["reason"] == "replayed"


def test_scan_same_store_again_not_new(monkeypatch):
    c = _client()
    u, ct = _umkm_token(c), _customer_token(c, monkeypatch)
    h = {"Authorization": f"Bearer {u}"}
    c.post("/umkm/customer/scan/validate", headers=h, json={"customer_qr_token": _qr(c, ct)})
    r = c.post("/umkm/customer/scan/validate", headers=h, json={"customer_qr_token": _qr(c, ct)})
    assert r.json()["valid"] is True and r.json()["is_new_member"] is False


def test_scan_expired(monkeypatch):
    c = _client()
    u, ct = _umkm_token(c), _customer_token(c, monkeypatch)
    monkeypatch.setattr(qr_service, "QR_TTL_SECONDS", -1)
    r = c.post("/umkm/customer/scan/validate", headers={"Authorization": f"Bearer {u}"},
               json={"customer_qr_token": _qr(c, ct)})
    assert r.json()["reason"] == "expired"


def test_scan_tampered(monkeypatch):
    c = _client()
    u, ct = _umkm_token(c), _customer_token(c, monkeypatch)
    r = c.post("/umkm/customer/scan/validate", headers={"Authorization": f"Bearer {u}"},
               json={"customer_qr_token": _qr(c, ct) + "x"})
    assert r.json()["reason"] == "tampered"


def test_scan_unknown_customer(monkeypatch):
    c = _client()
    u = _umkm_token(c)
    ghost = qr_service.issue_qr("cu_ghost")["qr_token"]
    r = c.post("/umkm/customer/scan/validate", headers={"Authorization": f"Bearer {u}"},
               json={"customer_qr_token": ghost})
    assert r.json()["reason"] == "tampered"


def test_cross_principal_rejected(monkeypatch):
    c = _client()
    u, ct = _umkm_token(c), _customer_token(c, monkeypatch)
    # customer token di endpoint UMKM scan → 401
    r1 = c.post("/umkm/customer/scan/validate", headers={"Authorization": f"Bearer {ct}"},
                json={"customer_qr_token": "xxxxxxxxxx"})
    assert r1.status_code == 401
    # UMKM token di endpoint customer qr/session → 401
    r2 = c.post("/customer/qr/session", headers={"Authorization": f"Bearer {u}"})
    assert r2.status_code == 401
