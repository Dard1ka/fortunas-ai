"""Route customer: bootstrap (seam di-monkeypatch) + me + qr/session. App minimal."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import customer
from app.core.firebase_auth import FirebaseAuthError, FirebaseNotConfigured

_BOOT = {"firebase_id_token": "xxxxxxxxxx", "username": "Budi", "birth_date": "1995-08-17"}


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(customer.router)
    return TestClient(app)


def _patch(monkeypatch, claims=None, exc=None):
    def fake(_token):
        if exc:
            raise exc
        return claims or {"firebase_uid": "fb1", "phone_number": "+628111"}
    monkeypatch.setattr(customer, "verify_firebase_token", fake)


def test_bootstrap_new_then_existing_and_me(monkeypatch):
    _patch(monkeypatch)
    c = _client()
    r = c.post("/customer/auth/bootstrap", json=_BOOT)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == "customer" and body["is_new_user"] is True
    assert body["profile"]["username"] == "Budi"
    token = body["access_token"]

    r2 = c.post("/customer/auth/bootstrap",
                json={**_BOOT, "username": "Lain", "birth_date": "1990-01-01"})
    assert r2.json()["is_new_user"] is False

    me = c.get("/customer/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["username"] == "Budi"


def test_put_me(monkeypatch):
    _patch(monkeypatch)
    c = _client()
    token = c.post("/customer/auth/bootstrap", json=_BOOT).json()["access_token"]
    r = c.put("/customer/me", headers={"Authorization": f"Bearer {token}"},
              json={"username": "Budi S"})
    assert r.status_code == 200 and r.json()["username"] == "Budi S"


def test_qr_session(monkeypatch):
    _patch(monkeypatch)
    c = _client()
    token = c.post("/customer/auth/bootstrap", json=_BOOT).json()["access_token"]
    r = c.post("/customer/qr/session", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["ttl_seconds"] == 90 and r.json()["nonce"] and r.json()["qr_token"]


def test_bootstrap_not_configured_503(monkeypatch):
    _patch(monkeypatch, exc=FirebaseNotConfigured("x"))
    assert _client().post("/customer/auth/bootstrap", json=_BOOT).status_code == 503


def test_bootstrap_bad_token_401(monkeypatch):
    _patch(monkeypatch, exc=FirebaseAuthError("x"))
    assert _client().post("/customer/auth/bootstrap", json=_BOOT).status_code == 401
