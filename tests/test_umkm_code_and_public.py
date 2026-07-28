"""Fase 1: kode UMKM dari alamat (AI+fallback), register+alamat, cari produk, lookup publik."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import auth, products, public
from app.services import umkm_code

_PNG = b"\x89PNG\r\n\x1a\nfake"


# ── Unit: generate kode ──────────────────────────────────────────

def test_prefix_from_city_consonants():
    assert umkm_code._prefix_from_city("Kudus") == "KDS"
    assert umkm_code._prefix_from_city("Semarang") == "SMR"


def test_generate_code_sequence(monkeypatch):
    # LLM dimatikan → pakai heuristik; alamat menyebut kota eksplisit.
    def _boom(*a, **k):
        raise RuntimeError("off")

    monkeypatch.setattr(umkm_code, "llm_generate", _boom)
    addr = "Jl. Sudirman No. 1, Kota Kudus, Jawa Tengah"
    g1 = umkm_code.generate_umkm_code(addr, [])
    assert g1["code"] == "KDS-001"
    g2 = umkm_code.generate_umkm_code(addr, ["KDS-001"])
    assert g2["code"] == "KDS-002"


def test_extract_city_via_llm(monkeypatch):
    monkeypatch.setattr(umkm_code, "llm_generate",
                        lambda *a, **k: '{"city": "Kudus"}')
    assert umkm_code.extract_city("alamat apapun") == "Kudus"


# ── Route: register + alamat + cari + publik ─────────────────────

def _client() -> TestClient:
    app = FastAPI()
    for r in (auth.router, products.router, public.router):
        app.include_router(r)
    return TestClient(app)


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def test_register_with_address_generates_code(monkeypatch, tmp_path):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    monkeypatch.setattr(umkm_code, "llm_generate", lambda *a, **k: '{"city": "Kudus"}')
    c = _client()
    r = c.post("/auth/register", json={
        "email": "kds@t.com", "password": "rahasia123", "business_name": "Warung Kudus",
        "address": "Jl. Mawar No. 5, Kudus"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["code"].startswith("KDS-")
    assert body["address"] == "Jl. Mawar No. 5, Kudus"
    tok = body["access_token"]

    # produk + cari (autocomplete) menyertakan image_url
    c.post("/umkm/products", headers=_h(tok), data={"name": "Kopi Susu"},
           files={"image": ("f.png", _PNG, "image/png")})
    s = c.get("/umkm/products/search", headers=_h(tok), params={"q": "kop"}).json()
    assert s["count"] == 1 and s["products"][0]["name"] == "Kopi Susu"
    assert "image_url" in s["products"][0]

    # lookup publik by code → menu bergambar
    code = body["code"]
    pub = c.get(f"/public/umkm/{code}")
    assert pub.status_code == 200, pub.text
    pj = pub.json()
    assert pj["name"] == "Warung Kudus" and pj["count"] == 1
    assert pj["products"][0]["name"] == "Kopi Susu"


def test_set_address_endpoint(monkeypatch, tmp_path):
    monkeypatch.setattr(umkm_code, "llm_generate", lambda *a, **k: '{"city": "Semarang"}')
    c = _client()
    tok = c.post("/auth/register", json={
        "email": "smg@t.com", "password": "rahasia123", "business_name": "Toko Semarang"}).json()["access_token"]
    r = c.put("/umkm/address", headers=_h(tok), json={"address": "Jl. Pemuda, Semarang"})
    assert r.status_code == 200, r.text
    assert r.json()["code"].startswith("SMR-")


def test_public_unknown_code_404():
    c = _client()
    assert c.get("/public/umkm/ZZZ-999").status_code == 404
