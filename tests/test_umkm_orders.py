"""Slice 1: inbox pesanan UMKM (list + accept/reject/complete) & idempotensi stok."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import order_repo
from app.api.routes import auth, orders, products, public
from app.services import umkm_code

_PNG = b"\x89PNG\r\n\x1a\nfake"


def _client() -> TestClient:
    app = FastAPI()
    for r in (auth.router, products.router, public.router, orders.router):
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


# ── Task 3: repo — idempotensi, isolasi tenant, transisi ─────────

def _webhook_replay(c, order_id: int):
    """Tiru webhook settlement ULANG (Midtrans mengirim ganda / bisa di-retrigger)."""
    order_repo.mark_paid(order_id, payment_status="settlement")


def test_mark_paid_is_idempotent_after_accept(monkeypatch, tmp_path):
    """REGRESI: notifikasi settlement ulang setelah UMKM menerima pesanan tidak
    boleh memotong stok dua kali maupun memundurkan status ke `paid`."""
    from app import product_repo
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, tok = _setup(c, monkeypatch, tmp_path, email="idem@t.com", stock=5)
    tenant_id = c.get("/auth/me", headers=_h(tok)).json()["tenant_id"]

    o = _order(c, code, pid, qty=2)
    _pay(c, o)
    assert product_repo.get_product(tenant_id, pid)["stock"] == 3

    accepted = order_repo.apply_action(tenant_id, o["id"], "accept")
    assert accepted["status"] == order_repo.STATUS_ACCEPTED

    _webhook_replay(c, o["id"])

    row = order_repo.get_order(o["id"])
    assert row["status"] == order_repo.STATUS_ACCEPTED, "status mundur ke paid"
    assert product_repo.get_product(tenant_id, pid)["stock"] == 3, "stok terpotong 2x"


def test_get_order_for_tenant_blocks_other_tenant(monkeypatch, tmp_path):
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code_a, pid_a, tok_a = _setup(c, monkeypatch, tmp_path, email="t3a@t.com", stock=5,
                                  business_name="Warung A")
    _, _, tok_b = _setup(c, monkeypatch, tmp_path, email="t3b@t.com", stock=5,
                         business_name="Warung B")
    tenant_a = c.get("/auth/me", headers=_h(tok_a)).json()["tenant_id"]
    tenant_b = c.get("/auth/me", headers=_h(tok_b)).json()["tenant_id"]

    o = _order(c, code_a, pid_a)
    assert order_repo.get_order_for_tenant(tenant_a, o["id"]) is not None
    assert order_repo.get_order_for_tenant(tenant_b, o["id"]) is None


def test_list_orders_filters_by_statuses(monkeypatch, tmp_path):
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, tok = _setup(c, monkeypatch, tmp_path, email="t3l@t.com", stock=9)
    tenant_id = c.get("/auth/me", headers=_h(tok)).json()["tenant_id"]

    belum = _order(c, code, pid)                  # pending_payment
    lunas = _order(c, code, pid)
    _pay(c, lunas)                                # paid

    semua = order_repo.list_orders(tenant_id)
    assert {r["id"] for r in semua} == {belum["id"], lunas["id"]}
    hanya_lunas = order_repo.list_orders(tenant_id, [order_repo.STATUS_PAID])
    assert [r["id"] for r in hanya_lunas] == [lunas["id"]]


def test_reject_restores_stock_once(monkeypatch, tmp_path):
    from app import product_repo
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, tok = _setup(c, monkeypatch, tmp_path, email="t3r@t.com", stock=5)
    tenant_id = c.get("/auth/me", headers=_h(tok)).json()["tenant_id"]

    o = _order(c, code, pid, qty=2)
    _pay(c, o)
    assert product_repo.get_product(tenant_id, pid)["stock"] == 3

    order_repo.apply_action(tenant_id, o["id"], "reject")
    assert product_repo.get_product(tenant_id, pid)["stock"] == 5

    # restore_stock idempoten — panggilan kedua tak menaikkan lagi
    assert order_repo.restore_stock(o["id"]) is False
    assert product_repo.get_product(tenant_id, pid)["stock"] == 5


def test_illegal_transitions_raise(monkeypatch, tmp_path):
    import pytest
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, tok = _setup(c, monkeypatch, tmp_path, email="t3x@t.com", stock=5)
    tenant_id = c.get("/auth/me", headers=_h(tok)).json()["tenant_id"]

    o = _order(c, code, pid)                       # masih pending_payment
    with pytest.raises(order_repo.TransitionError):
        order_repo.apply_action(tenant_id, o["id"], "accept")

    _pay(c, o)
    with pytest.raises(order_repo.TransitionError):
        order_repo.apply_action(tenant_id, o["id"], "complete")   # belum accepted

    order_repo.apply_action(tenant_id, o["id"], "accept")
    with pytest.raises(order_repo.TransitionError):
        order_repo.apply_action(tenant_id, o["id"], "accept")     # dua kali

    done = order_repo.apply_action(tenant_id, o["id"], "complete")
    assert done["status"] == order_repo.STATUS_COMPLETED


def test_apply_action_returns_none_for_missing_order(monkeypatch, tmp_path):
    c = _client()
    _, _, tok = _setup(c, monkeypatch, tmp_path, email="t3n@t.com", stock=5)
    tenant_id = c.get("/auth/me", headers=_h(tok)).json()["tenant_id"]
    assert order_repo.apply_action(tenant_id, 999999, "accept") is None


# ── Task 4: route inbox ──────────────────────────────────────────

def test_inbox_hides_unpaid_by_default(monkeypatch, tmp_path):
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, tok = _setup(c, monkeypatch, tmp_path, email="i1@t.com", stock=9)
    _order(c, code, pid)                       # pending_payment → disembunyikan
    lunas = _order(c, code, pid)
    _pay(c, lunas)

    r = c.get("/umkm/orders", headers=_h(tok))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["count"] == 1
    assert body["orders"][0]["id"] == lunas["id"]
    assert body["orders"][0]["status"] == "paid"
    assert body["orders"][0]["items"][0]["unit_price"] == 15000
    assert body["orders"][0]["paid_at"] is not None


def test_inbox_status_filter_and_all(monkeypatch, tmp_path):
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, tok = _setup(c, monkeypatch, tmp_path, email="i2@t.com", stock=9)
    belum = _order(c, code, pid)

    r = c.get("/umkm/orders?status=pending_payment", headers=_h(tok))
    assert [o["id"] for o in r.json()["orders"]] == [belum["id"]]

    r = c.get("/umkm/orders?status=all", headers=_h(tok))
    assert r.json()["count"] == 1


def test_inbox_action_flow_paid_accept_complete(monkeypatch, tmp_path):
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, tok = _setup(c, monkeypatch, tmp_path, email="i3@t.com", stock=9)
    o = _order(c, code, pid)
    _pay(c, o)

    r = c.post(f"/umkm/orders/{o['id']}/accept", headers=_h(tok))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "accepted"

    r = c.post(f"/umkm/orders/{o['id']}/complete", headers=_h(tok))
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


def test_inbox_illegal_transition_409(monkeypatch, tmp_path):
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, tok = _setup(c, monkeypatch, tmp_path, email="i4@t.com", stock=9)
    o = _order(c, code, pid)                   # belum dibayar
    r = c.post(f"/umkm/orders/{o['id']}/accept", headers=_h(tok))
    assert r.status_code == 409, r.text


def test_inbox_other_tenant_gets_404_not_403(monkeypatch, tmp_path):
    """404, bukan 403 — 403 mengakui pesanan itu ada."""
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code_a, pid_a, _ = _setup(c, monkeypatch, tmp_path, email="i5a@t.com", stock=9,
                              business_name="Warung A")
    _, _, tok_b = _setup(c, monkeypatch, tmp_path, email="i5b@t.com", stock=9,
                         business_name="Warung B")
    o = _order(c, code_a, pid_a)
    _pay(c, o)

    assert c.get("/umkm/orders", headers=_h(tok_b)).json()["count"] == 0
    r = c.post(f"/umkm/orders/{o['id']}/accept", headers=_h(tok_b))
    assert r.status_code == 404, r.text


def test_inbox_requires_auth(monkeypatch, tmp_path):
    c = _client()
    assert c.get("/umkm/orders").status_code in (401, 403)


def test_inbox_reject_returns_stock(monkeypatch, tmp_path):
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, tok = _setup(c, monkeypatch, tmp_path, email="i6@t.com", stock=5)
    o = _order(c, code, pid, qty=2)
    _pay(c, o)
    assert c.get(f"/public/umkm/{code}").json()["products"][0]["stock"] == 3

    r = c.post(f"/umkm/orders/{o['id']}/reject", headers=_h(tok))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "rejected"
    assert c.get(f"/public/umkm/{code}").json()["products"][0]["stock"] == 5


# ── Task 5: hardening jalur publik ───────────────────────────────

def test_public_order_lookup_uses_unguessable_key(monkeypatch, tmp_path):
    """PII pelanggan tak boleh bisa dipanen dengan menghitung id 1,2,3,…"""
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, _ = _setup(c, monkeypatch, tmp_path, email="p1@t.com", stock=5)
    o = _order(c, code, pid)
    poid = o["payment_order_id"]

    assert c.get(f"/public/orders/{poid}").status_code == 200
    # id berurutan tak lagi jadi kunci publik
    assert c.get(f"/public/orders/{o['id']}").status_code == 404


def test_simulate_pay_also_keyed_by_payment_order_id(monkeypatch, tmp_path):
    """simulate-pay punya cacat enumerasi yang sama: dengan id berurutan siapa pun
    bisa menandai pesanan orang lain lunas di mode simulasi."""
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, _ = _setup(c, monkeypatch, tmp_path, email="p2@t.com", stock=5)
    o = _order(c, code, pid)
    poid = o["payment_order_id"]                       # ikut di respons create
    assert poid == order_repo.get_order(o["id"])["payment_order_id"]
    assert o["payment_redirect_url"] == f"/public/orders/{poid}/simulate-pay"
    assert c.post(o["payment_redirect_url"]).json()["status"] == "paid"
    # jalur id berurutan tak lagi ada
    assert c.post(f"/public/orders/{o['id']}/simulate-pay").status_code == 404


def test_public_responses_hide_tenant_id(monkeypatch, tmp_path):
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, _ = _setup(c, monkeypatch, tmp_path, email="p3@t.com", stock=5)
    assert "tenant_id" not in c.get(f"/public/umkm/{code}").json()
    o = _order(c, code, pid)
    assert "tenant_id" not in o
    assert o["payment_order_id"], "pelanggan butuh token ini untuk memantau status"


def test_webhook_rejected_when_midtrans_not_configured(monkeypatch, tmp_path):
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")   # simulasi
    c = _client()
    r = c.post("/public/payment/webhook", json={"order_id": "ORD-1-abcd"})
    assert r.status_code == 400, r.text


def test_webhook_refund_restores_stock(monkeypatch, tmp_path):
    """`refund`/`chargeback` dipetakan ke outcome `failed`; pesanan yang sudah
    lunas harus mengembalikan stok, bukan hanya berubah status."""
    import hashlib
    from app import product_repo
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, tok = _setup(c, monkeypatch, tmp_path, email="p4@t.com", stock=5)
    tenant_id = c.get("/auth/me", headers=_h(tok)).json()["tenant_id"]
    o = _order(c, code, pid, qty=2)
    _pay(c, o)
    assert product_repo.get_product(tenant_id, pid)["stock"] == 3

    poid = order_repo.get_order(o["id"])["payment_order_id"]
    monkeypatch.setattr(payment, "_server_key", lambda: "SERVERKEY")  # "live"
    sig = hashlib.sha512(f"{poid}200{o['total']}SERVERKEY".encode()).hexdigest()
    r = c.post("/public/payment/webhook", json={
        "order_id": poid, "status_code": "200", "gross_amount": str(o["total"]),
        "signature_key": sig, "transaction_status": "refund"})
    assert r.status_code == 200, r.text

    assert order_repo.get_order(o["id"])["status"] == order_repo.STATUS_CANCELLED
    assert product_repo.get_product(tenant_id, pid)["stock"] == 5


def test_webhook_refund_after_accept_keeps_accepted_status(monkeypatch, tmp_path):
    """TEMUAN Task 3: refund yang tiba SETELAH UMKM menerima pesanan tidak boleh
    membatalkan penerimaan itu diam-diam. Status harus tetap `accepted`, stok
    tetap kembali ke angka semula, dan `payment_status` mentah tetap tercatat."""
    import hashlib
    from app import product_repo
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, tok = _setup(c, monkeypatch, tmp_path, email="p5@t.com", stock=5)
    tenant_id = c.get("/auth/me", headers=_h(tok)).json()["tenant_id"]
    o = _order(c, code, pid, qty=2)
    _pay(c, o)
    assert product_repo.get_product(tenant_id, pid)["stock"] == 3

    accepted = order_repo.apply_action(tenant_id, o["id"], "accept")
    assert accepted["status"] == order_repo.STATUS_ACCEPTED

    poid = order_repo.get_order(o["id"])["payment_order_id"]
    monkeypatch.setattr(payment, "_server_key", lambda: "SERVERKEY")  # "live"
    sig = hashlib.sha512(f"{poid}200{o['total']}SERVERKEY".encode()).hexdigest()
    r = c.post("/public/payment/webhook", json={
        "order_id": poid, "status_code": "200", "gross_amount": str(o["total"]),
        "signature_key": sig, "transaction_status": "refund"})
    assert r.status_code == 200, r.text

    row = order_repo.get_order(o["id"])
    assert row["status"] == order_repo.STATUS_ACCEPTED, "refund membatalkan penerimaan UMKM"
    assert row["payment_status"] == "refund"
    assert product_repo.get_product(tenant_id, pid)["stock"] == 5


def test_cancel_by_gateway_records_empty_payment_status_after_accept(monkeypatch, tmp_path):
    """`transaction_status: ""` --> outcome `failed` --> `payment_status=""` tiba
    di `cancel_by_gateway` pada pesanan yang sudah `accepted` (status dibekukan).
    Guard-nya HARUS `is not None`, bukan truthy: string kosong tetap jejak audit
    yang sah dan tak boleh diam-diam dibuang begitu status dibekukan."""
    import hashlib
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, tok = _setup(c, monkeypatch, tmp_path, email="p6@t.com", stock=5)
    tenant_id = c.get("/auth/me", headers=_h(tok)).json()["tenant_id"]
    o = _order(c, code, pid, qty=2)
    _pay(c, o)
    order_repo.apply_action(tenant_id, o["id"], "accept")

    poid = order_repo.get_order(o["id"])["payment_order_id"]
    monkeypatch.setattr(payment, "_server_key", lambda: "SERVERKEY")  # "live"
    sig = hashlib.sha512(f"{poid}200{o['total']}SERVERKEY".encode()).hexdigest()
    r = c.post("/public/payment/webhook", json={
        "order_id": poid, "status_code": "200", "gross_amount": str(o["total"]),
        "signature_key": sig, "transaction_status": ""})
    assert r.status_code == 200, r.text

    row = order_repo.get_order(o["id"])
    assert row["status"] == order_repo.STATUS_ACCEPTED
    assert row["payment_status"] == "", "payment_status kosong dibuang diam-diam"


def test_set_pending_by_gateway_does_not_rewind_paid_order(monkeypatch, tmp_path):
    """Notifikasi `pending` yang tiba TERLAMBAT (setelah lunas) tak boleh
    memundurkan status ke `pending_payment` — stoknya sudah terpotong, dan
    inbox hanya menampilkan `paid`/`accepted`; order jadi tak terlihat kalau
    status dimundurkan."""
    import hashlib
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, tok = _setup(c, monkeypatch, tmp_path, email="p7@t.com", stock=5)
    o = _order(c, code, pid, qty=1)
    _pay(c, o)

    poid = order_repo.get_order(o["id"])["payment_order_id"]
    monkeypatch.setattr(payment, "_server_key", lambda: "SERVERKEY")  # "live"
    sig = hashlib.sha512(f"{poid}200{o['total']}SERVERKEY".encode()).hexdigest()
    r = c.post("/public/payment/webhook", json={
        "order_id": poid, "status_code": "200", "gross_amount": str(o["total"]),
        "signature_key": sig, "transaction_status": "pending"})
    assert r.status_code == 200, r.text

    row = order_repo.get_order(o["id"])
    assert row["status"] == order_repo.STATUS_PAID
    assert row["payment_status"] == "pending"


def test_set_pending_by_gateway_does_not_resurrect_cancelled_order(monkeypatch, tmp_path):
    """Notifikasi `pending` tak boleh menghidupkan ulang pesanan yang sudah
    dibatalkan gateway (mis. notifikasi `pending` yang datang belakangan,
    salah urutan, setelah `deny`/`cancel`/`expire` sebelumnya)."""
    import hashlib
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, tok = _setup(c, monkeypatch, tmp_path, email="p8@t.com", stock=5)
    o = _order(c, code, pid, qty=1)                     # masih pending_payment

    poid = order_repo.get_order(o["id"])["payment_order_id"]
    monkeypatch.setattr(payment, "_server_key", lambda: "SERVERKEY")  # "live"
    sig = hashlib.sha512(f"{poid}200{o['total']}SERVERKEY".encode()).hexdigest()

    r_cancel = c.post("/public/payment/webhook", json={
        "order_id": poid, "status_code": "200", "gross_amount": str(o["total"]),
        "signature_key": sig, "transaction_status": "cancel"})
    assert r_cancel.status_code == 200, r_cancel.text
    assert order_repo.get_order(o["id"])["status"] == order_repo.STATUS_CANCELLED

    r_pending = c.post("/public/payment/webhook", json={
        "order_id": poid, "status_code": "200", "gross_amount": str(o["total"]),
        "signature_key": sig, "transaction_status": "pending"})
    assert r_pending.status_code == 200, r_pending.text

    row = order_repo.get_order(o["id"])
    assert row["status"] == order_repo.STATUS_CANCELLED
    assert row["payment_status"] == "pending"


# ── Task 6: rate limit ───────────────────────────────────────────

def test_public_order_rate_limited(monkeypatch, tmp_path):
    from app.api.routes import public as public_routes
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    public_routes._order_hits.clear()
    c = _client()
    # stok None = tak dilacak → tak akan kena 409 stok kurang
    code, pid, _ = _setup(c, monkeypatch, tmp_path, email="rl@t.com", stock=None)
    body = {"items": [{"product_id": pid, "qty": 1}]}
    for i in range(public_routes._ORDER_RATE_LIMIT):
        assert c.post(f"/public/umkm/{code}/orders", json=body).status_code == 201, i
    assert c.post(f"/public/umkm/{code}/orders", json=body).status_code == 429


def test_public_order_rate_limit_recovers_after_window(monkeypatch, tmp_path):
    """Baris `now - t < _ORDER_RATE_WINDOW` di `_rate_limit_order` tak dites
    di test manapun sebelum ini: hapus filter jendela itu dan limiter diam-diam
    jadi jatah SEUMUR HIDUP 10 order per IP, tapi 264/264 test tetap hijau
    (review Task 6, finding #2) — tak ada test lain yang mendekati limitnya,
    apalagi menunggu jendelanya lewat. Tanpa sleep/patch clock: seed ember
    dengan hit yang SUDAH basi (lebih tua dari jendela), lalu pastikan order
    berikutnya tetap lolos."""
    import time
    from app.api.routes import public as public_routes
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, _ = _setup(c, monkeypatch, tmp_path, email="rlw@t.com", stock=None)
    body = {"items": [{"product_id": pid, "qty": 1}]}
    stale = time.monotonic() - public_routes._ORDER_RATE_WINDOW - 1
    public_routes._order_hits["testclient"] = [stale] * public_routes._ORDER_RATE_LIMIT
    assert c.post(f"/public/umkm/{code}/orders", json=body).status_code == 201


def test_public_order_rate_limit_is_per_ip(monkeypatch, tmp_path):
    """Baris `ip = request.client.host ...` juga tak dites: kalau regresi
    menjadikan limiter satu ember GLOBAL (bukan per-IP), 264/264 test tetap
    hijau karena `TestClient` selalu memakai host `testclient` — tak ada dua
    IP nyata yang berbeda di suite ini untuk menampakkan bocornya (review Task
    6, finding #2). Tak bisa dites lewat dua `TestClient` sungguhan (host-nya
    sama), jadi seed kunci IP LAIN sampai penuh, lalu pastikan `testclient`
    sendiri tetap lolos — kalau ember-nya global, ini akan gagal dengan 429."""
    from app.api.routes import public as public_routes
    from app.services import payment
    import time
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, _ = _setup(c, monkeypatch, tmp_path, email="rlip@t.com", stock=None)
    body = {"items": [{"product_id": pid, "qty": 1}]}
    now = time.monotonic()
    public_routes._order_hits["1.2.3.4"] = [now] * public_routes._ORDER_RATE_LIMIT
    assert c.post(f"/public/umkm/{code}/orders", json=body).status_code == 201


def test_public_order_rate_limit_sweeps_stale_ips(monkeypatch, tmp_path):
    """`_ORDER_HITS_SWEEP_THRESHOLD` ada supaya `_order_hits` tak numpuk tanpa
    batas kalau IP anonim mampir sekali lalu tak pernah balik (review Task 6,
    finding #1). Isi dict basi melebihi threshold, lalu buat satu order —
    entri basi itu harus tersapu, hanya IP yang barusan lolos yang tersisa."""
    from app.api.routes import public as public_routes
    from app.services import payment
    import time
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, _ = _setup(c, monkeypatch, tmp_path, email="rlsweep@t.com", stock=None)
    body = {"items": [{"product_id": pid, "qty": 1}]}
    stale = time.monotonic() - public_routes._ORDER_RATE_WINDOW - 1
    for i in range(public_routes._ORDER_HITS_SWEEP_THRESHOLD + 1):
        public_routes._order_hits[f"1.2.3.{i}"] = [stale]
    assert c.post(f"/public/umkm/{code}/orders", json=body).status_code == 201
    assert list(public_routes._order_hits.keys()) == ["testclient"]


def test_sweep_survives_key_removed_during_iteration(monkeypatch):
    """Review Task 6 (ronde 2): `_sweep_stale_order_hits` mengambil snapshot
    kunci (`list(_order_hits.keys())`) lalu belakangan mengakses
    `_order_hits[ip]`. `create_public_order` adalah `def` sync, jadi Starlette
    menjalankannya di threadpool anyio TANPA lock — begitu dict melewati
    threshold, sweep jalan bersamaan di banyak thread, dan thread A bisa
    men-pop kunci yang masih ada di snapshot thread B sebelum B sempat
    mengaksesnya, membuat subscript polos KeyError → 500 di endpoint order
    publik tanpa auth. Simulasikan race itu SECARA DETERMINISTIK (tanpa
    thread sungguhan): dict tiruan yang menghapus kuncinya sendiri persis
    setelah snapshot diambil, meniru thread lain yang menang duluan men-pop
    kunci yang sama tepat di titik rawan itu."""
    from app.api.routes import public as public_routes
    import time

    now = time.monotonic()
    stale = now - public_routes._ORDER_RATE_WINDOW - 1

    class _RaceDict(dict):
        """Menghapus `_victim` dari diri sendiri begitu snapshot kunci
        diambil — meniru thread lain yang men-pop kunci itu tepat di antara
        snapshot sweep dan akses per-kunci berikutnya."""
        _victim = "race-ip"

        def keys(self):
            snapshot = list(super().keys())
            self.pop(self._victim, None)
            return snapshot

    race_dict = _RaceDict({"race-ip": [stale], "other-ip": [stale]})
    monkeypatch.setattr(public_routes, "_order_hits", race_dict)

    public_routes._sweep_stale_order_hits(now)  # tak boleh KeyError

    assert "race-ip" not in race_dict
    assert "other-ip" not in race_dict


def test_payment_order_id_entropi_128_bit(monkeypatch, tmp_path):
    """`payment_order_id` kini SATU-SATUNYA autentikator untuk customer_name +
    customer_phone di jalur tanpa auth (Task 5), jadi bagian acaknya harus 128 bit."""
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "")
    c = _client()
    code, pid, _ = _setup(c, monkeypatch, tmp_path, email="ent@t.com", stock=None)
    body = {"items": [{"product_id": pid, "qty": 1}]}
    ids = [c.post(f"/public/umkm/{code}/orders", json=body).json()["payment_order_id"]
           for _ in range(2)]
    assert ids[0] != ids[1]
    for poid in ids:
        acak = poid.rsplit("-", 1)[1]
        assert len(acak) == 32, poid
        int(acak, 16)          # harus hex murni
