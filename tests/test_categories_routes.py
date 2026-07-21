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
