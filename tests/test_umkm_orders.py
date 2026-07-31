"""Slice 1: inbox pesanan UMKM (list + accept/reject/complete) & idempotensi stok."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import order_repo
from app.api.routes import auth, products, public
from app.services import umkm_code

_PNG = b"\x89PNG\r\n\x1a\nfake"


def _client() -> TestClient:
    app = FastAPI()
    for r in (auth.router, products.router, public.router):
        app.include_router(r)
    return TestClient(app)


def _h(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


def _setup(c, monkeypatch, tmp_path, *, email, city="Kudus", price=15000, stock=None,
           business_name="Warung Uji"):
    """Daftar UMKM + 1 produk. Return (kode_umkm, product_id, token).

    `business_name` WAJIB dibedakan saat satu test mendaftarkan DUA UMKM:
    `POST /auth/register` menurunkan `table_prefix` dari nama bisnis
    (`_slugify_prefix`) dan menolak prefix yang sudah dipakai dengan 409.
    """
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    monkeypatch.setattr(umkm_code, "llm_generate", lambda *a, **k: f'{{"city": "{city}"}}')
    body = c.post("/auth/register", json={
        "email": email, "password": "rahasia123", "business_name": business_name,
        "address": f"Jl. Uji No. 1, {city}"}).json()
    tok = body["access_token"]
    data = {"name": "Kopi Susu", "price": str(price)}
    if stock is not None:
        data["stock"] = str(stock)
    p = c.post("/umkm/products", headers=_h(tok), data=data,
               files={"image": ("f.png", _PNG, "image/png")}).json()
    return body["code"], p["id"], tok


def _order(c, code, pid, qty=1):
    """Buat pesanan publik. Return dict order."""
    r = c.post(f"/public/umkm/{code}/orders",
               json={"customer_name": "Budi", "customer_phone": "0812",
                     "items": [{"product_id": pid, "qty": qty}]})
    assert r.status_code == 201, r.text
    return r.json()


def _pay(c, order: dict):
    """Bayar mode simulasi lewat redirect_url yang diberikan backend."""
    r = c.post(order["payment_redirect_url"])
    assert r.status_code == 200, r.text
    return r.json()


# ── Task 1: penanda stok ─────────────────────────────────────────

def test_new_order_has_empty_stock_markers(monkeypatch, tmp_path):
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, _ = _setup(c, monkeypatch, tmp_path, email="m1@t.com", stock=5)
    o = _order(c, code, pid)
    row = order_repo.get_order(o["id"])
    assert row["paid_at"] is None
    assert row["stock_restored_at"] is None


def test_paid_at_filled_after_payment(monkeypatch, tmp_path):
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, _ = _setup(c, monkeypatch, tmp_path, email="m2@t.com", stock=5)
    o = _order(c, code, pid)
    _pay(c, o)
    row = order_repo.get_order(o["id"])
    assert row["paid_at"] is not None
    assert row["stock_restored_at"] is None


# ── Task 2: restore_by_ids ───────────────────────────────────────

def test_restore_by_ids_adds_stock_back(monkeypatch, tmp_path):
    from app import product_repo

    c = _client()
    _, pid, tok = _setup(c, monkeypatch, tmp_path, email="r1@t.com", stock=10)
    tenant_id = c.get("/auth/me", headers=_h(tok)).json()["tenant_id"]

    product_repo.decrement_by_ids(tenant_id, [{"product_id": pid, "qty": 4}])
    assert product_repo.get_product(tenant_id, pid)["stock"] == 6

    out = product_repo.restore_by_ids(tenant_id, [{"product_id": pid, "qty": 4}])
    assert out["ok"] is True
    assert out["restored"] == [pid]
    assert product_repo.get_product(tenant_id, pid)["stock"] == 10


def test_restore_by_ids_skips_untracked_stock(monkeypatch, tmp_path):
    """Produk tanpa pelacakan stok (stock None) tak boleh mendadak jadi angka."""
    from app import product_repo

    c = _client()
    _, pid, tok = _setup(c, monkeypatch, tmp_path, email="r2@t.com", stock=None)
    tenant_id = c.get("/auth/me", headers=_h(tok)).json()["tenant_id"]

    out = product_repo.restore_by_ids(tenant_id, [{"product_id": pid, "qty": 3}])
    assert out["ok"] is True
    assert pid not in out["restored"]
    assert product_repo.get_product(tenant_id, pid)["stock"] is None


def test_restore_by_ids_ignores_other_tenant(monkeypatch, tmp_path):
    from app import product_repo

    c = _client()
    _, pid_a, tok_a = _setup(c, monkeypatch, tmp_path, email="r3a@t.com", stock=5,
                            business_name="Warung A")
    _, _, tok_b = _setup(c, monkeypatch, tmp_path, email="r3b@t.com", stock=5,
                        business_name="Warung B")
    tenant_a = c.get("/auth/me", headers=_h(tok_a)).json()["tenant_id"]
    tenant_b = c.get("/auth/me", headers=_h(tok_b)).json()["tenant_id"]

    out = product_repo.restore_by_ids(tenant_b, [{"product_id": pid_a, "qty": 3}])
    assert out["ok"] is True
    assert pid_a not in out["restored"]
    assert product_repo.get_product(tenant_a, pid_a)["stock"] == 5  # tak tersentuh
