"""Repository katalog produk per-UMKM + statistik belanja per-barang pelanggan.

- Product: milik satu tenant (tenant_id). stock_code auto = 2 huruf awal nama +
  nomor urut per-prefix per-tenant (kopi susu -> ko-001, kopi latte -> ko-002).
- CustomerProductStat: riwayat belanja per-barang di akun pelanggan (Indomaret Point).

Pola mengikuti app/customer_repo.py: modul-level function, SessionLocal, return dict.
"""
from __future__ import annotations

import os
import re
import secrets
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, update

from app.db_pg import SessionLocal
from app.models import CustomerProductStat, Product

# Direktori penyimpanan gambar produk (di-serve via StaticFiles /media/products).
PRODUCT_IMAGE_DIR = os.getenv("PRODUCT_IMAGE_DIR", "app/data/product_images")
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
LOW_STOCK_THRESHOLD = 5  # stok <= ini → tampil "Menipis" / peringatan kasir


class ProductImageError(ValueError):
    """Gambar produk tidak valid (format/ukuran)."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save_product_image(tenant_id: int, filename: str, content: bytes) -> str:
    """Simpan gambar ke {DIR}/{tenant_id}/{rand}.{ext}; return URL path /media/products/...

    Validasi ekstensi & ukuran. Melempar ProductImageError bila tidak valid.
    """
    ext = os.path.splitext((filename or "").lower())[1]
    if ext not in ALLOWED_IMAGE_EXTS:
        raise ProductImageError(
            f"Format gambar tidak didukung. Gunakan: {', '.join(sorted(ALLOWED_IMAGE_EXTS))}")
    if not content:
        raise ProductImageError("File gambar kosong.")
    if len(content) > MAX_IMAGE_BYTES:
        raise ProductImageError("Ukuran gambar maksimal 5 MB.")

    tenant_dir = os.path.join(PRODUCT_IMAGE_DIR, str(tenant_id))
    os.makedirs(tenant_dir, exist_ok=True)
    fname = f"{secrets.token_hex(8)}{ext}"
    with open(os.path.join(tenant_dir, fname), "wb") as f:
        f.write(content)
    return f"/media/products/{tenant_id}/{fname}"


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
        "image_url": p.image_url or "",
        "stock": p.stock,
        "category_id": p.category_id,
        "created_at": p.created_at or "",
    }


def create_product(tenant_id: int, *, name: str, description: str = "",
                   image_url: str = "", stock: int | None = None,
                   category_id: int | None = None) -> dict[str, Any]:
    """Buat produk baru; stock_code di-generate otomatis dalam transaksi yang sama
    (hindari balapan nomor urut). stock=None → tak-dilacak."""
    with SessionLocal() as s:
        if category_id is not None:
            from app.models import ProductCategory
            cat = s.get(ProductCategory, category_id)
            if cat is None or cat.tenant_id != tenant_id:
                raise ValueError("Kategori tidak valid.")
        code = generate_stock_code(tenant_id, name, session=s)
        p = Product(
            tenant_id=tenant_id,
            name=name.strip(),
            description=description.strip(),
            stock_code=code,
            image_url=image_url,
            stock=stock,
            category_id=category_id,
            created_at=_now(),
        )
        s.add(p)
        s.commit()
        return _product_to_dict(p)


def set_stock(tenant_id: int, product_id: int, stock: int | None) -> bool:
    """Set nilai stok absolut. None = tak-dilacak. Raises ValueError bila negatif.
    Return False bila produk tak ada / bukan milik tenant (scoped)."""
    if stock is not None and stock < 0:
        raise ValueError("Stok tidak boleh negatif.")
    with SessionLocal() as s:
        p = s.get(Product, product_id)
        if p is None or p.tenant_id != tenant_id:
            return False
        p.stock = stock
        s.commit()
        return True


def set_category(tenant_id: int, product_id: int, category_id: int | None) -> bool:
    """Set kategori produk. category_id non-null WAJIB milik tenant. False bila invalid/lintas-tenant."""
    from app.models import ProductCategory
    with SessionLocal() as s:
        p = s.get(Product, product_id)
        if p is None or p.tenant_id != tenant_id:
            return False
        if category_id is not None:
            c = s.get(ProductCategory, category_id)
            if c is None or c.tenant_id != tenant_id:
                return False
        p.category_id = category_id
        s.commit()
        return True


def _find_product_obj(s, tenant_id: int, name: str):
    """ORM Product milik tenant berdasarkan nama (case-insensitive, trim)."""
    key = (name or "").strip().lower()
    if not key:
        return None
    rows = s.scalars(select(Product).where(Product.tenant_id == tenant_id)).all()
    for p in rows:
        if (p.name or "").strip().lower() == key:
            return p
    return None


def check_stock(tenant_id: int, items: list) -> list[dict[str, Any]]:
    """Read-only: shortfall untuk item katalog & dilacak yang stok < qty.
    Item tak-dilacak (stock None) / non-katalog dilewati."""
    shortfalls: list[dict[str, Any]] = []
    with SessionLocal() as s:
        for it in items:
            p = _find_product_obj(s, tenant_id, it.product)
            if p is None or p.stock is None:
                continue
            if p.stock < it.qty:
                shortfalls.append(
                    {"name": p.name, "requested": it.qty, "available": p.stock})
    return shortfalls


def apply_decrement(tenant_id: int, items: list, *, allow_oversell: bool) -> dict[str, Any]:
    """Kurangi stok item katalog & dilacak.
    - allow_oversell=True (kasir): floor 0, ok selalu True, isi warnings.
    - allow_oversell=False (self-order): atomik bersyarat; bila ada yang kurang →
      ok=False + insufficient, rollback (tak ada perubahan).
    """
    report: dict[str, Any] = {"ok": True, "warnings": [], "insufficient": []}
    with SessionLocal() as s:
        for it in items:
            p = _find_product_obj(s, tenant_id, it.product)
            if p is None or p.stock is None:
                continue  # non-katalog / tak-dilacak
            if allow_oversell:
                oversold = max(0, it.qty - p.stock)
                p.stock = max(0, p.stock - it.qty)
                if oversold:
                    report["warnings"].append(
                        f"Stok {p.name} habis (terjual {oversold} melebihi stok).")
                elif p.stock <= LOW_STOCK_THRESHOLD:
                    report["warnings"].append(f"Stok {p.name} tinggal {p.stock}.")
            else:
                res = s.execute(
                    update(Product)
                    .where(Product.id == p.id, Product.stock >= it.qty)
                    .values(stock=Product.stock - it.qty)
                )
                if res.rowcount == 0:
                    report["ok"] = False
                    report["insufficient"].append(
                        {"name": p.name, "requested": it.qty, "available": p.stock})
        if not allow_oversell and not report["ok"]:
            s.rollback()
            return report
        s.commit()
    return report


def list_products(tenant_id: int) -> list[dict[str, Any]]:
    with SessionLocal() as s:
        rows = s.scalars(
            select(Product).where(Product.tenant_id == tenant_id).order_by(Product.id)
        ).all()
        return [_product_to_dict(p) for p in rows]


def find_by_name(tenant_id: int, name: str) -> dict[str, Any] | None:
    """Cari produk milik tenant berdasarkan nama (case-insensitive, trim).

    Dipakai checkout untuk mendeteksi apakah barang pesanan terdaftar di
    Kelola Produk; kalau ya, stock_code katalog dipakai di histori transaksi.
    """
    key = (name or "").strip().lower()
    if not key:
        return None
    with SessionLocal() as s:
        rows = s.scalars(select(Product).where(Product.tenant_id == tenant_id)).all()
        for p in rows:
            if (p.name or "").strip().lower() == key:
                return _product_to_dict(p)
        return None


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
