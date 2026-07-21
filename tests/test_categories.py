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
