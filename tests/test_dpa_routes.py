"""Route test GET/PUT /umkm/dpa — minimal app (auth+dpa router) tanpa import berat."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import auth, dpa


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(dpa.router)
    return TestClient(app)


def _token(client, email="owner@toko.com", password="rahasia123", name="Toko Sehat"):
    r = client.post("/auth/register", json={"email": email, "password": password, "business_name": name})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def test_get_dpa_default_empty():
    client = _client()
    token = _token(client)
    r = client.get("/umkm/dpa", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == 0
    assert body["forbidden_rules"] == []
    assert body["allowed_rules"] == []
    assert body["raw_text"] == ""


def test_put_dpa_correct_password_persists_and_increments():
    client = _client()
    token = _token(client)
    h = {"Authorization": f"Bearer {token}"}
    r = client.put("/umkm/dpa", headers=h, json={
        "raw_text": "tidak jual rokok", "allowed_rules": ["diskon makanan"],
        "forbidden_rules": ["rokok", "tembakau"], "password": "rahasia123"})
    assert r.status_code == 200, r.text
    assert r.json()["version"] == 1
    assert r.json()["forbidden_rules"] == ["rokok", "tembakau"]
    g = client.get("/umkm/dpa", headers=h)
    assert g.json()["raw_text"] == "tidak jual rokok"
    assert g.json()["version"] == 1


def test_put_dpa_wrong_password_403():
    client = _client()
    token = _token(client)
    r = client.put("/umkm/dpa", headers={"Authorization": f"Bearer {token}"}, json={
        "raw_text": "x", "allowed_rules": [], "forbidden_rules": [], "password": "salah"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Konfirmasi password salah."


def test_put_dpa_empty_raw_text_422():
    client = _client()
    token = _token(client)
    r = client.put("/umkm/dpa", headers={"Authorization": f"Bearer {token}"}, json={
        "raw_text": "", "allowed_rules": [], "forbidden_rules": [], "password": "rahasia123"})
    assert r.status_code == 422
