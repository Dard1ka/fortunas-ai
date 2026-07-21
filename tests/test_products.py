"""Tests katalog produk + generator kode barang + riwayat per-barang pelanggan."""
from __future__ import annotations

import pytest

from app import customer_repo, db, product_repo
from app.product_repo import ProductImageError
from app.schemas import CheckoutLineItem


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


def test_check_stock_sufficient_returns_empty():
    t = _tenant()
    product_repo.create_product(t, name="Kopi Susu", stock=10)
    items = [CheckoutLineItem(product="Kopi Susu", qty=3, unit_price=15000)]
    assert product_repo.check_stock(t, items) == []


def test_check_stock_reports_shortfall():
    t = _tenant()
    product_repo.create_product(t, name="Kopi Susu", stock=2)
    items = [CheckoutLineItem(product="Kopi Susu", qty=5, unit_price=15000)]
    sf = product_repo.check_stock(t, items)
    assert sf == [{"name": "Kopi Susu", "requested": 5, "available": 2}]


def test_check_stock_untracked_skipped():
    t = _tenant()
    product_repo.create_product(t, name="Nasi Goreng", stock=None)  # tak-dilacak
    items = [CheckoutLineItem(product="Nasi Goreng", qty=99, unit_price=20000)]
    assert product_repo.check_stock(t, items) == []


def test_check_stock_non_catalog_skipped():
    t = _tenant()
    items = [CheckoutLineItem(product="Barang Random", qty=99, unit_price=1000)]
    assert product_repo.check_stock(t, items) == []


def _find_stock(t, name):
    for p in product_repo.list_products(t):
        if p["name"] == name:
            return p["stock"]
    return None


def test_decrement_kasir_floors_at_zero_and_warns_oversell():
    t = _tenant()
    product_repo.create_product(t, name="Es Teh", stock=3)
    items = [CheckoutLineItem(product="Es Teh", qty=5, unit_price=5000)]
    rep = product_repo.apply_decrement(t, items, allow_oversell=True)
    assert rep["ok"] is True
    assert _find_stock(t, "Es Teh") == 0  # floor, tak minus
    assert any("Es Teh" in w and "habis" in w for w in rep["warnings"])


def test_decrement_kasir_low_stock_warning():
    t = _tenant()
    product_repo.create_product(t, name="Kopi", stock=7)
    items = [CheckoutLineItem(product="Kopi", qty=4, unit_price=15000)]
    rep = product_repo.apply_decrement(t, items, allow_oversell=True)
    assert _find_stock(t, "Kopi") == 3
    assert any("Kopi" in w and "tinggal 3" in w for w in rep["warnings"])


def test_decrement_kasir_untracked_and_noncatalog_skipped():
    t = _tenant()
    product_repo.create_product(t, name="Nasi", stock=None)
    items = [CheckoutLineItem(product="Nasi", qty=9, unit_price=20000),
             CheckoutLineItem(product="Random", qty=1, unit_price=1000)]
    rep = product_repo.apply_decrement(t, items, allow_oversell=True)
    assert rep["warnings"] == [] and _find_stock(t, "Nasi") is None


def test_decrement_selforder_blocks_and_no_change_when_insufficient():
    t = _tenant()
    product_repo.create_product(t, name="Es Teh", stock=2)
    items = [CheckoutLineItem(product="Es Teh", qty=5, unit_price=5000)]
    rep = product_repo.apply_decrement(t, items, allow_oversell=False)
    assert rep["ok"] is False
    assert rep["insufficient"] == [{"name": "Es Teh", "requested": 5, "available": 2}]
    assert _find_stock(t, "Es Teh") == 2  # tidak berubah (rollback)


def test_decrement_selforder_succeeds_when_enough():
    t = _tenant()
    product_repo.create_product(t, name="Es Teh", stock=10)
    items = [CheckoutLineItem(product="Es Teh", qty=4, unit_price=5000)]
    rep = product_repo.apply_decrement(t, items, allow_oversell=False)
    assert rep["ok"] is True and _find_stock(t, "Es Teh") == 6


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


def test_decrement_selforder_cross_item_rollback_is_atomic():
    # Item A succeeds, item B insufficient → WHOLE batch rolls back (A undone).
    t = _tenant()
    product_repo.create_product(t, name="Kopi", stock=10)
    product_repo.create_product(t, name="Es Teh", stock=1)
    items = [CheckoutLineItem(product="Kopi", qty=2, unit_price=15000),
             CheckoutLineItem(product="Es Teh", qty=5, unit_price=5000)]
    rep = product_repo.apply_decrement(t, items, allow_oversell=False)
    assert rep["ok"] is False
    assert any(x["name"] == "Es Teh" for x in rep["insufficient"])
    assert _find_stock(t, "Kopi") == 10   # earlier successful line rolled back
    assert _find_stock(t, "Es Teh") == 1


def test_decrement_kasir_duplicate_lines_accumulate():
    # Two lines of same product accumulate via identity-map (not double/under-count).
    t = _tenant()
    product_repo.create_product(t, name="Kopi", stock=10)
    items = [CheckoutLineItem(product="Kopi", qty=3, unit_price=15000),
             CheckoutLineItem(product="Kopi", qty=2, unit_price=15000)]
    rep = product_repo.apply_decrement(t, items, allow_oversell=True)
    assert rep["ok"] is True
    assert _find_stock(t, "Kopi") == 5  # 10 - 3 - 2
