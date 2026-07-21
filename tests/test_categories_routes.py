from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import auth, categories, products

_PNG = b"\x89PNG\r\n\x1a\nfake"


def _client() -> TestClient:
    app = FastAPI()
    for r in (auth.router, products.router, categories.router):
        app.include_router(r)
    return TestClient(app)


def _tok(c) -> str:
    r = c.post("/auth/register",
               json={"email": "o@t.com", "password": "rahasia123", "business_name": "Toko"})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def test_category_crud_and_assign(monkeypatch, tmp_path):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    c = _client()
    tok = _tok(c)

    r = c.post("/umkm/categories", headers=_h(tok), json={"name": "Minuman"})
    assert r.status_code == 201, r.text
    cid = r.json()["id"]

    cats = c.get("/umkm/categories", headers=_h(tok)).json()
    assert any(x["name"] == "Minuman" for x in cats["categories"])

    # duplicate → 409
    assert c.post("/umkm/categories", headers=_h(tok), json={"name": "Minuman"}).status_code == 409

    # create product with category_id
    pr = c.post("/umkm/products", headers=_h(tok),
                data={"name": "Es Teh", "category_id": str(cid)},
                files={"image": ("f.png", _PNG, "image/png")})
    assert pr.status_code == 201, pr.text
    assert pr.json()["category_id"] == cid
    pid = pr.json()["id"]

    # PATCH category → null
    r = c.patch(f"/umkm/products/{pid}/category", headers=_h(tok), json={"category_id": None})
    assert r.status_code == 200 and r.json()["category_id"] is None

    # delete category
    r = c.delete(f"/umkm/categories/{cid}", headers=_h(tok))
    assert r.status_code == 200 and r.json()["deleted"] is True


def test_create_product_rejects_cross_tenant_category(monkeypatch, tmp_path):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    c = _client()
    # tenant B makes a category
    tb = c.post("/auth/register", json={"email": "b@t.com", "password": "rahasia123", "business_name": "Toko B"}).json()["access_token"]
    cid_b = c.post("/umkm/categories", headers=_h(tb), json={"name": "Punya B"}).json()["id"]
    # tenant A tries to use B's category_id on create → 400
    ta = c.post("/auth/register", json={"email": "a@t.com", "password": "rahasia123", "business_name": "Toko A"}).json()["access_token"]
    r = c.post("/umkm/products", headers=_h(ta),
               data={"name": "Es Teh", "category_id": str(cid_b)},
               files={"image": ("f.png", _PNG, "image/png")})
    assert r.status_code == 400, r.text


def test_create_product_nonexistent_category_4xx(monkeypatch, tmp_path):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    c = _client()
    tok = _tok(c)
    r = c.post("/umkm/products", headers=_h(tok),
               data={"name": "Kopi", "category_id": "999999"},
               files={"image": ("f.png", _PNG, "image/png")})
    assert r.status_code == 400, r.text  # clean 4xx, NOT 500


def test_delete_missing_category_404(monkeypatch, tmp_path):
    c = _client()
    tok = _tok(c)
    assert c.delete("/umkm/categories/999999", headers=_h(tok)).status_code == 404
