from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import auth, products

_PNG = b"\x89PNG\r\n\x1a\nfakeimagedata"


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(products.router)
    return TestClient(app)


def _token(c) -> str:
    r = c.post("/auth/register",
               json={"email": "o@t.com", "password": "rahasia123", "business_name": "Toko A"})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _create(c, tok, name, stock=None):
    data = {"name": name, "description": "x"}
    if stock is not None:
        data["stock"] = str(stock)
    return c.post("/umkm/products", headers={"Authorization": f"Bearer {tok}"},
                  data=data, files={"image": ("f.png", _PNG, "image/png")})


def test_create_with_stock_and_list_shows_it(monkeypatch, tmp_path):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    c = _client()
    tok = _token(c)
    r = _create(c, tok, "Es Teh", stock=25)
    assert r.status_code == 201, r.text
    assert r.json()["stock"] == 25
    lst = c.get("/umkm/products", headers={"Authorization": f"Bearer {tok}"}).json()
    assert lst["products"][0]["stock"] == 25


def test_create_without_stock_is_untracked(monkeypatch, tmp_path):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    c = _client()
    tok = _token(c)
    r = _create(c, tok, "Nasi Goreng")
    assert r.status_code == 201 and r.json()["stock"] is None


def test_patch_stock_updates(monkeypatch, tmp_path):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    c = _client()
    tok = _token(c)
    pid = _create(c, tok, "Kopi", stock=5).json()["id"]
    r = c.patch(f"/umkm/products/{pid}/stock",
                headers={"Authorization": f"Bearer {tok}"}, json={"stock": 40})
    assert r.status_code == 200 and r.json()["stock"] == 40


def test_patch_stock_negative_rejected(monkeypatch, tmp_path):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    c = _client()
    tok = _token(c)
    pid = _create(c, tok, "Kopi", stock=5).json()["id"]
    r = c.patch(f"/umkm/products/{pid}/stock",
                headers={"Authorization": f"Bearer {tok}"}, json={"stock": -1})
    assert r.status_code == 422


def test_patch_stock_not_found(monkeypatch, tmp_path):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    c = _client()
    tok = _token(c)
    r = c.patch("/umkm/products/9999/stock",
                headers={"Authorization": f"Bearer {tok}"}, json={"stock": 10})
    assert r.status_code == 404


def test_patch_stock_cross_tenant_returns_404(monkeypatch, tmp_path):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    c = _client()
    tok_a = _token(c)  # tenant A = o@t.com
    pid = _create(c, tok_a, "Kopi", stock=5).json()["id"]
    rb = c.post("/auth/register",
                json={"email": "b@t.com", "password": "rahasia123", "business_name": "Toko B"})
    assert rb.status_code == 201, rb.text
    tok_b = rb.json()["access_token"]
    r = c.patch(f"/umkm/products/{pid}/stock",
                headers={"Authorization": f"Bearer {tok_b}"}, json={"stock": 99})
    assert r.status_code == 404


def test_create_negative_stock_rejected(monkeypatch, tmp_path):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    c = _client()
    tok = _token(c)
    r = _create(c, tok, "Kopi", stock=-1)
    assert r.status_code == 422
