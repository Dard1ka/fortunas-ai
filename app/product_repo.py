"""Repository katalog produk per-UMKM + statistik belanja per-barang pelanggan.

- Product: milik satu tenant (tenant_id). stock_code auto = 2 huruf awal nama +
  nomor urut per-prefix per-tenant (kopi susu -> ko-001, kopi latte -> ko-002).
- CustomerProductStat: riwayat belanja per-barang di akun pelanggan (Indomaret Point).

Pola mengikuti app/customer_repo.py: modul-level function, SessionLocal, return dict.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select

from app.db_pg import SessionLocal
from app.models import CustomerProductStat, Product


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _code_prefix(name: str) -> str:
    """2 huruf awal nama (hanya alfabet), lowercase. Fallback 'xx' bila kurang."""
    letters = re.sub(r"[^a-z]", "", (name or "").lower())
    prefix = letters[:2]
    return prefix.ljust(2, "x") if prefix else "xx"


def generate_stock_code(tenant_id: int, name: str, session=None) -> str:
    """Kode unik per tenant: {prefix}-{urut:03d}. Nomor lanjut dari max prefix itu."""
    prefix = _code_prefix(name)

    def _compute(s) -> str:
        # Ambil semua kode existing dengan prefix sama untuk tenant ini.
        rows = s.scalars(
            select(Product.stock_code).where(
                Product.tenant_id == tenant_id,
                Product.stock_code.like(f"{prefix}-%"),
            )
        ).all()
        max_n = 0
        for code in rows:
            m = re.match(rf"^{re.escape(prefix)}-(\d+)$", code or "")
            if m:
                max_n = max(max_n, int(m.group(1)))
        return f"{prefix}-{max_n + 1:03d}"

    if session is not None:
        return _compute(session)
    with SessionLocal() as s:
        return _compute(s)


def _product_to_dict(p: Product) -> dict[str, Any]:
    return {
        "id": p.id,
        "tenant_id": p.tenant_id,
        "name": p.name,
        "description": p.description or "",
        "stock_code": p.stock_code,
        "created_at": p.created_at or "",
    }


def create_product(tenant_id: int, *, name: str, description: str = "") -> dict[str, Any]:
    """Buat produk baru; stock_code di-generate otomatis dalam transaksi yang sama
    (hindari balapan nomor urut)."""
    with SessionLocal() as s:
        code = generate_stock_code(tenant_id, name, session=s)
        p = Product(
            tenant_id=tenant_id,
            name=name.strip(),
            description=description.strip(),
            stock_code=code,
            created_at=_now(),
        )
        s.add(p)
        s.commit()
        return _product_to_dict(p)


def list_products(tenant_id: int) -> list[dict[str, Any]]:
    with SessionLocal() as s:
        rows = s.scalars(
            select(Product).where(Product.tenant_id == tenant_id).order_by(Product.id)
        ).all()
        return [_product_to_dict(p) for p in rows]


def count_products(tenant_id: int) -> int:
    with SessionLocal() as s:
        return int(s.scalar(
            select(func.count()).select_from(Product).where(Product.tenant_id == tenant_id)
        ) or 0)


def delete_product(tenant_id: int, product_id: int) -> bool:
    with SessionLocal() as s:
        p = s.get(Product, product_id)
        if p is None or p.tenant_id != tenant_id:
            return False
        s.delete(p)
        s.commit()
        return True


# ── Customer per-item purchase stats (Indomaret Point) ───────────

def _stat_to_dict(st: CustomerProductStat) -> dict[str, Any]:
    return {
        "tenant_id": st.tenant_id,
        "product_name": st.product_name,
        "purchase_count": st.purchase_count,
        "total_amount": st.total_amount,
        "last_purchased_at": st.last_purchased_at,
    }


def record_purchase(customer_user_id: str, tenant_id: int, *, product_name: str,
                    amount: int, count: int = 1) -> dict[str, Any]:
    """Upsert statistik: +count transaksi, +amount total untuk (customer, tenant, produk)."""
    now = _now()
    with SessionLocal() as s:
        st = s.scalar(
            select(CustomerProductStat).where(
                CustomerProductStat.customer_user_id == customer_user_id,
                CustomerProductStat.tenant_id == tenant_id,
                CustomerProductStat.product_name == product_name,
            )
        )
        if st is None:
            st = CustomerProductStat(
                customer_user_id=customer_user_id,
                tenant_id=tenant_id,
                product_name=product_name,
                purchase_count=count,
                total_amount=amount,
                last_purchased_at=now,
            )
            s.add(st)
        else:
            st.purchase_count += count
            st.total_amount += amount
            st.last_purchased_at = now
        s.commit()
        return _stat_to_dict(st)


def customer_product_stats(customer_user_id: str,
                           tenant_id: int | None = None) -> list[dict[str, Any]]:
    """Riwayat per-barang milik customer; opsional difilter tenant."""
    with SessionLocal() as s:
        q = select(CustomerProductStat).where(
            CustomerProductStat.customer_user_id == customer_user_id)
        if tenant_id is not None:
            q = q.where(CustomerProductStat.tenant_id == tenant_id)
        rows = s.scalars(q.order_by(CustomerProductStat.purchase_count.desc())).all()
        return [_stat_to_dict(st) for st in rows]
