"""Tests katalog produk + generator kode barang + riwayat per-barang pelanggan."""
from __future__ import annotations

import pytest

from app import customer_repo, db, product_repo
from app.product_repo import ProductImageError


def _tenant() -> int:
    return db.create_tenant("Warung Kopi", "warung_kopi")


# ── Stock code generator ─────────────────────────────────────────

def test_stock_code_sequential_same_prefix():
    t = _tenant()
    p1 = product_repo.create_product(t, name="Kopi Susu", description="kopi + susu")
    p2 = product_repo.create_product(t, name="Kopi Latte", description="kopi + latte")
    assert p1["stock_code"] == "ko-001"
    assert p2["stock_code"] == "ko-002"


def test_stock_code_prefix_per_first_two_letters():
    t = _tenant()
    teh = product_repo.create_product(t, name="Teh Manis")
    kopi = product_repo.create_product(t, name="Kopi Hitam")
    assert teh["stock_code"] == "te-001"
    assert kopi["stock_code"] == "ko-001"  # prefix beda → counter sendiri


def test_stock_code_isolated_per_tenant():
    t1 = _tenant()
    t2 = db.create_tenant("Kedai Lain", "kedai_lain")
    a = product_repo.create_product(t1, name="Kopi A")
    b = product_repo.create_product(t2, name="Kopi B")
    # Tenant berbeda → nomor urut mulai dari 001 masing-masing.
    assert a["stock_code"] == "ko-001"
    assert b["stock_code"] == "ko-001"


def test_find_by_name_case_insensitive():
    t = _tenant()
    product_repo.create_product(t, name="Kopi Susu")
    assert product_repo.find_by_name(t, "kopi susu")["stock_code"] == "ko-001"
    assert product_repo.find_by_name(t, "  KOPI SUSU  ")["stock_code"] == "ko-001"
    assert product_repo.find_by_name(t, "Kopi Hitam") is None


def test_find_by_name_scoped_to_tenant():
    t1 = _tenant()
    t2 = db.create_tenant("Toko Seberang", "toko_seberang")
    product_repo.create_product(t1, name="Nasi Goreng")
    # Produk tenant lain tidak boleh bocor ke tenant ini.
    assert product_repo.find_by_name(t2, "Nasi Goreng") is None


def test_count_and_list_products():
    t = _tenant()
    assert product_repo.count_products(t) == 0
    product_repo.create_product(t, name="Roti Bakar")
    assert product_repo.count_products(t) == 1
    assert product_repo.list_products(t)[0]["name"] == "Roti Bakar"


# ── Stock (nullable quantity) ────────────────────────────────────

def test_create_product_default_stock_none():
    t = _tenant()
    p = product_repo.create_product(t, name="Kopi Susu")
    assert p["stock"] is None  # default = tak-dilacak


def test_create_product_with_stock():
    t = _tenant()
    p = product_repo.create_product(t, name="Es Teh", stock=25)
    assert p["stock"] == 25


def test_set_stock_updates_value():
    t = _tenant()
    p = product_repo.create_product(t, name="Es Teh", stock=5)
    assert product_repo.set_stock(t, p["id"], 30) is True
    assert product_repo.list_products(t)[0]["stock"] == 30


def test_set_stock_to_none_untracks():
    t = _tenant()
    p = product_repo.create_product(t, name="Nasi Goreng", stock=10)
    assert product_repo.set_stock(t, p["id"], None) is True
    assert product_repo.list_products(t)[0]["stock"] is None


def test_set_stock_negative_raises():
    t = _tenant()
    p = product_repo.create_product(t, name="Kopi", stock=1)
    with pytest.raises(ValueError):
        product_repo.set_stock(t, p["id"], -3)


def test_set_stock_wrong_tenant_returns_false():
    t1 = _tenant()
    t2 = db.create_tenant("Toko Lain", "toko_lain")
    p = product_repo.create_product(t1, name="Kopi", stock=1)
    assert product_repo.set_stock(t2, p["id"], 99) is False


# ── Gambar produk ────────────────────────────────────────────────

def test_save_product_image_and_url(tmp_path, monkeypatch):
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    url = product_repo.save_product_image(1, "foto.png", b"\x89PNG\r\n\x1a\nfake")
    assert url.startswith("/media/products/1/")
    assert url.endswith(".png")


def test_save_product_image_rejects_bad_ext(tmp_path, monkeypatch):
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    with pytest.raises(ProductImageError):
        product_repo.save_product_image(1, "virus.exe", b"data")


def test_create_product_stores_image_url():
    t = _tenant()
    p = product_repo.create_product(
        t, name="Kopi Susu", image_url="/media/products/1/abc.png")
    assert p["image_url"] == "/media/products/1/abc.png"


# ── Customer per-item purchase stats (Indomaret Point) ───────────

def test_record_purchase_accumulates():
    t = _tenant()
    cust, _ = customer_repo.upsert_customer(
        firebase_uid="fb_p1", phone_number="+628", username="siti", birth_date="1999-01-01")
    cid = cust["customer_user_id"]

    product_repo.record_purchase(cid, t, product_name="Kopi Susu", amount=15000)
    product_repo.record_purchase(cid, t, product_name="Kopi Susu", amount=15000)
    product_repo.record_purchase(cid, t, product_name="Roti", amount=8000)

    stats = product_repo.customer_product_stats(cid)
    by_name = {s["product_name"]: s for s in stats}
    assert by_name["Kopi Susu"]["purchase_count"] == 2
    assert by_name["Kopi Susu"]["total_amount"] == 30000
    assert by_name["Roti"]["purchase_count"] == 1
    # Urut desc by count → Kopi Susu duluan.
    assert stats[0]["product_name"] == "Kopi Susu"
