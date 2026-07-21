"""Repository kategori produk per-UMKM (tenant-scoped). Pola: app/product_repo.py."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from app.db_pg import SessionLocal
from app.models import Product, ProductCategory


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _to_dict(c: ProductCategory) -> dict[str, Any]:
    return {"id": c.id, "tenant_id": c.tenant_id, "name": c.name,
            "created_at": c.created_at or ""}


def create_category(tenant_id: int, name: str) -> dict[str, Any]:
    clean = (name or "").strip()
    if not clean:
        raise ValueError("Nama kategori wajib diisi.")
    with SessionLocal() as s:
        exists = s.scalar(select(ProductCategory).where(
            ProductCategory.tenant_id == tenant_id,
            func.lower(ProductCategory.name) == clean.lower()))
        if exists is not None:
            raise ValueError("Kategori dengan nama itu sudah ada.")
        c = ProductCategory(tenant_id=tenant_id, name=clean, created_at=_now())
        s.add(c)
        try:
            s.commit()
        except IntegrityError as exc:
            s.rollback()
            raise ValueError("Kategori dengan nama itu sudah ada.") from exc
        return _to_dict(c)


def list_categories(tenant_id: int) -> list[dict[str, Any]]:
    with SessionLocal() as s:
        rows = s.scalars(select(ProductCategory).where(
            ProductCategory.tenant_id == tenant_id).order_by(ProductCategory.name)).all()
        return [_to_dict(c) for c in rows]


def count_products_in_category(tenant_id: int, category_id: int) -> int:
    with SessionLocal() as s:
        return int(s.scalar(select(func.count()).select_from(Product).where(
            Product.tenant_id == tenant_id, Product.category_id == category_id)) or 0)


def delete_category(tenant_id: int, category_id: int) -> dict[str, Any]:
    """Hapus kategori; produk di dalamnya di-SET NULL (bukan ikut terhapus).
    1 transaksi. Return {deleted, reassigned}. deleted=False bila bukan milik tenant."""
    with SessionLocal() as s:
        c = s.get(ProductCategory, category_id)
        if c is None or c.tenant_id != tenant_id:
            return {"deleted": False, "reassigned": 0}
        res = s.execute(update(Product).where(
            Product.tenant_id == tenant_id, Product.category_id == category_id
        ).values(category_id=None))
        s.delete(c)
        s.commit()
        return {"deleted": True, "reassigned": int(res.rowcount or 0)}
