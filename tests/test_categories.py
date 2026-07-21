"""Tests kategori produk per-UMKM + assign + delete SET NULL."""
from __future__ import annotations

from app import db, product_repo


def _tenant() -> int:
    return db.create_tenant("Warung Kopi", "warung_kopi")


def test_create_product_default_category_none():
    t = _tenant()
    p = product_repo.create_product(t, name="Kopi Susu")
    assert p["category_id"] is None
