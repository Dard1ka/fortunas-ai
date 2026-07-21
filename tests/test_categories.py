"""Tests kategori produk per-UMKM + assign + delete SET NULL."""
from __future__ import annotations

import pytest

from app import category_repo, db, product_repo


def _tenant() -> int:
    return db.create_tenant("Warung Kopi", "warung_kopi")


def test_create_product_default_category_none():
    t = _tenant()
    p = product_repo.create_product(t, name="Kopi Susu")
    assert p["category_id"] is None


def test_create_and_list_category():
    t = _tenant()
    c = category_repo.create_category(t, "Minuman")
    assert c["name"] == "Minuman" and c["tenant_id"] == t
    assert [x["name"] for x in category_repo.list_categories(t)] == ["Minuman"]


def test_create_category_empty_name_raises():
    t = _tenant()
    with pytest.raises(ValueError):
        category_repo.create_category(t, "   ")


def test_create_category_duplicate_raises():
    t = _tenant()
    category_repo.create_category(t, "Nasi")
    with pytest.raises(ValueError):
        category_repo.create_category(t, "Nasi")


def test_category_isolated_per_tenant():
    t1 = _tenant()
    t2 = db.create_tenant("Kedai Lain", "kedai_lain")
    category_repo.create_category(t1, "Mie")
    assert category_repo.list_categories(t2) == []


def test_count_products_in_category():
    t = _tenant()
    c = category_repo.create_category(t, "Minuman")
    product_repo.create_product(t, name="Es Teh", category_id=c["id"])
    product_repo.create_product(t, name="Kopi", category_id=c["id"])
    product_repo.create_product(t, name="Roti")  # no category
    assert category_repo.count_products_in_category(t, c["id"]) == 2


def test_delete_category_sets_products_null():
    t = _tenant()
    c = category_repo.create_category(t, "Minuman")
    p = product_repo.create_product(t, name="Es Teh", category_id=c["id"])
    res = category_repo.delete_category(t, c["id"])
    assert res == {"deleted": True, "reassigned": 1}
    prod = [x for x in product_repo.list_products(t) if x["id"] == p["id"]][0]
    assert prod["category_id"] is None
    assert category_repo.list_categories(t) == []


def test_delete_category_wrong_tenant():
    t1 = _tenant()
    t2 = db.create_tenant("Lain", "lain2")
    c = category_repo.create_category(t1, "Nasi")
    assert category_repo.delete_category(t2, c["id"]) == {"deleted": False, "reassigned": 0}


def test_set_category_valid_and_reject_cross_tenant():
    t1 = _tenant()
    t2 = db.create_tenant("Lain", "lain3")
    c1 = category_repo.create_category(t1, "Nasi")
    c2 = category_repo.create_category(t2, "Mie")
    p = product_repo.create_product(t1, name="Nasi Goreng")
    assert product_repo.set_category(t1, p["id"], c1["id"]) is True
    assert product_repo.set_category(t1, p["id"], c2["id"]) is False  # kategori tenant lain
    assert product_repo.set_category(t1, p["id"], None) is True       # uncategorize
