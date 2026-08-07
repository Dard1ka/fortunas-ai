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


# ── Fase 2: pesan pelanggan + checkout berbayar (mode simulasi) ──────

def _register_with_product(c, monkeypatch, tmp_path, *, email, city, price=15000, stock=None):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    monkeypatch.setattr(umkm_code, "llm_generate", lambda *a, **k: f'{{"city": "{city}"}}')
    body = c.post("/auth/register", json={
        "email": email, "password": "rahasia123", "business_name": "Warung Uji",
        "address": f"Jl. Uji No. 1, {city}"}).json()
    tok = body["access_token"]
    data = {"name": "Kopi Susu", "price": str(price)}
    if stock is not None:
        data["stock"] = str(stock)
    p = c.post("/umkm/products", headers=_h(tok), data=data,
               files={"image": ("f.png", _PNG, "image/png")}).json()
    return body["code"], p["id"], tok


def test_public_menu_includes_price(monkeypatch, tmp_path):
    c = _client()
    code, pid, _ = _register_with_product(c, monkeypatch, tmp_path,
                                          email="price@t.com", city="Kudus", price=15000)
    pj = c.get(f"/public/umkm/{code}").json()
    assert pj["products"][0]["price"] == 15000


def test_create_order_and_confirm_payment_decrements_stock(monkeypatch, tmp_path):
    c = _client()
    code, pid, tok = _register_with_product(c, monkeypatch, tmp_path,
                                            email="ord@t.com", city="Kudus",
                                            price=15000, stock=3)
    r = c.post(f"/public/umkm/{code}/orders", json={
        "customer_name": "Budi", "customer_phone": "0812",
        "items": [{"product_id": pid, "qty": 2}]})
    assert r.status_code == 201, r.text
    o = r.json()
    assert o["total"] == 30000
    assert o["status"] == "pending_payment"
    # Pembayaran aktif = QRIS statis (Midtrans = future scope).
    assert o["payment_provider"] == "qris_static"
    assert o["payment_redirect_url"].endswith("/confirm-payment")

    # konfirmasi bayar (QRIS statis manual) → lunas + stok berkurang 2 (3 → 1)
    pay = c.post(o["payment_redirect_url"])
    assert pay.status_code == 200, pay.text
    assert pay.json()["status"] == "paid"

    got = c.get(f"/public/orders/{o['payment_order_id']}").json()
    assert got["status"] == "paid"
    menu = c.get(f"/public/umkm/{code}").json()
    assert menu["products"][0]["stock"] == 1


def test_order_rejects_product_without_price(monkeypatch, tmp_path):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    monkeypatch.setattr(umkm_code, "llm_generate", lambda *a, **k: '{"city": "Kudus"}')
    c = _client()
    body = c.post("/auth/register", json={
        "email": "noprice@t.com", "password": "rahasia123",
        "business_name": "Warung Tanpa Harga", "address": "Jl. X, Kudus"}).json()
    tok = body["access_token"]
    p = c.post("/umkm/products", headers=_h(tok), data={"name": "Teh"},
               files={"image": ("f.png", _PNG, "image/png")}).json()
    r = c.post(f"/public/umkm/{body['code']}/orders", json={
        "items": [{"product_id": p["id"], "qty": 1}]})
    assert r.status_code == 400
    assert "harga" in r.json()["detail"].lower()


def test_order_insufficient_stock_409(monkeypatch, tmp_path):
    c = _client()
    code, pid, _ = _register_with_product(c, monkeypatch, tmp_path,
                                          email="stock@t.com", city="Kudus",
                                          price=5000, stock=1)
    r = c.post(f"/public/umkm/{code}/orders", json={
        "items": [{"product_id": pid, "qty": 5}]})
    assert r.status_code == 409


def test_webhook_marks_paid_with_valid_signature(monkeypatch, tmp_path):
    import hashlib
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "SERVERKEY")  # Midtrans "live"
    # create_charge di-stub agar tak ada network ke Midtrans.
    monkeypatch.setattr(payment, "create_charge",
                        lambda order: {"provider": "midtrans", "token": "tok",
                                       "redirect_url": "https://snap/x"})
    c = _client()
    code, pid, _ = _register_with_product(c, monkeypatch, tmp_path,
                                          email="wh@t.com", city="Kudus",
                                          price=10000, stock=5)
    o = c.post(f"/public/umkm/{code}/orders", json={
        "items": [{"product_id": pid, "qty": 1}]}).json()
    from app import order_repo
    poid = order_repo.get_order(o["id"])["payment_order_id"]

    status_code, gross = "200", "10000"
    sig = hashlib.sha512(f"{poid}{status_code}{gross}SERVERKEY".encode()).hexdigest()
    wh = c.post("/public/payment/webhook", json={
        "order_id": poid, "status_code": status_code, "gross_amount": gross,
        "signature_key": sig, "transaction_status": "settlement"})
    assert wh.status_code == 200, wh.text
    assert c.get(f"/public/orders/{poid}").json()["status"] == "paid"


def test_webhook_rejects_bad_signature(monkeypatch, tmp_path):
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "SERVERKEY")
    c = _client()
    r = c.post("/public/payment/webhook", json={
        "order_id": "ORD-1-xx", "status_code": "200", "gross_amount": "1000",
        "signature_key": "wrong", "transaction_status": "settlement"})
    assert r.status_code == 403

    # non-ASCII signature_key tak boleh menabrak hmac.compare_digest jadi 500 —
    # penyerang yang tak berwenang harus tetap dibalas 403, bukan traceback.
    r2 = c.post("/public/payment/webhook", json={
        "order_id": "ORD-1-xx", "status_code": "200", "gross_amount": "1000",
        "signature_key": "café", "transaction_status": "settlement"})
    assert r2.status_code == 403, r2.text


def test_webhook_lone_surrogate_signature_returns_400(monkeypatch, tmp_path):
    """`str.encode()` menolak lone surrogate (mis. U+D800) — payload begini
    tak boleh pernah mencapai perbandingan signature, jadi 400, bukan 500/403.

    Body dikirim MENTAH (bukan lewat `json=`): httpx sendiri menolak
    men-serialize objek Python yang sudah memuat karakter surrogate mentah
    (gagal di sisi klien, sebelum pernah menyentuh jaringan). Yang perlu diuji
    adalah body kawat yang murni ASCII (`\\ud800` sebagai enam karakter escape
    JSON) yang, sesudah di-`json.loads()` ulang oleh SERVER, merekonstruksi
    lone surrogate itu di dalam str Python — persis skenario yang dilaporkan."""
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "SERVERKEY")
    c = _client()
    body = (b'{"order_id": "ORD-1-xx", "status_code": "200", '
            b'"gross_amount": "1000", "signature_key": "\\ud800", '
            b'"transaction_status": "settlement"}')
    r = c.post("/public/payment/webhook", content=body,
               headers={"content-type": "application/json"})
    assert r.status_code == 400, r.text


def test_webhook_malformed_body_returns_400(monkeypatch, tmp_path):
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "SERVERKEY")
    c = _client()
    r = c.post("/public/payment/webhook", content=b"{not json")
    assert r.status_code == 400, r.text


def test_webhook_non_object_body_returns_400(monkeypatch, tmp_path):
    from app.services import payment
    monkeypatch.setattr(payment, "_server_key", lambda: "SERVERKEY")
    c = _client()
    r = c.post("/public/payment/webhook", json=[1, 2])
    assert r.status_code == 400, r.text
