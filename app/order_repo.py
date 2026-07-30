"""Repository pesanan publik (self-order pelanggan lewat kode UMKM).

Menyimpan state pesanan di SQLite/Postgres (bukan BigQuery) karena ini state
operasional pra-transaksi. Stok dipotong saat pesanan menjadi `paid`.

Pola mengikuti app/product_repo.py: modul-level function, SessionLocal, return dict.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app import product_repo
from app.db_pg import SessionLocal
from app.models import PublicOrder

# Status yang valid untuk pesanan publik.
STATUS_PENDING = "pending_payment"
STATUS_PAID = "paid"
STATUS_ACCEPTED = "accepted"
STATUS_REJECTED = "rejected"
STATUS_COMPLETED = "completed"
STATUS_EXPIRED = "expired"
STATUS_CANCELLED = "cancelled"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _to_dict(o: PublicOrder) -> dict[str, Any]:
    return {
        "id": o.id,
        "tenant_id": o.tenant_id,
        "code": o.code or "",
        "customer_name": o.customer_name or "",
        "customer_phone": o.customer_phone or "",
        "items": list(o.items or []),
        "total": o.total or 0,
        "status": o.status,
        "payment_provider": o.payment_provider,
        "payment_order_id": o.payment_order_id,
        "payment_token": o.payment_token,
        "payment_redirect_url": o.payment_redirect_url,
        "payment_status": o.payment_status,
        "created_at": o.created_at or "",
        "updated_at": o.updated_at or "",
    }


def create_order(tenant_id: int, *, code: str, customer_name: str,
                 customer_phone: str, items: list[dict[str, Any]],
                 total: int) -> dict[str, Any]:
    """Buat pesanan baru berstatus pending_payment. `payment_order_id` unik
    di-generate agar bisa dipetakan balik dari webhook gateway."""
    now = _now()
    with SessionLocal() as s:
        o = PublicOrder(
            tenant_id=tenant_id,
            code=code,
            customer_name=customer_name.strip(),
            customer_phone=customer_phone.strip(),
            items=items,
            total=total,
            status=STATUS_PENDING,
            created_at=now,
            updated_at=now,
        )
        s.add(o)
        s.flush()  # dapatkan o.id sebelum menyusun payment_order_id
        o.payment_order_id = f"ORD-{o.id}-{secrets.token_hex(4)}"
        s.commit()
        return _to_dict(o)


def attach_payment(order_id: int, *, provider: str, token: str | None,
                   redirect_url: str | None) -> dict[str, Any] | None:
    with SessionLocal() as s:
        o = s.get(PublicOrder, order_id)
        if o is None:
            return None
        o.payment_provider = provider
        o.payment_token = token
        o.payment_redirect_url = redirect_url
        o.updated_at = _now()
        s.commit()
        return _to_dict(o)


def get_order(order_id: int) -> dict[str, Any] | None:
    with SessionLocal() as s:
        o = s.get(PublicOrder, order_id)
        return _to_dict(o) if o else None


def get_by_payment_order_id(payment_order_id: str) -> dict[str, Any] | None:
    with SessionLocal() as s:
        o = s.scalars(
            select(PublicOrder).where(
                PublicOrder.payment_order_id == payment_order_id)
        ).first()
        return _to_dict(o) if o else None


def list_orders(tenant_id: int, status: str | None = None) -> list[dict[str, Any]]:
    with SessionLocal() as s:
        q = select(PublicOrder).where(PublicOrder.tenant_id == tenant_id)
        if status is not None:
            q = q.where(PublicOrder.status == status)
        rows = s.scalars(q.order_by(PublicOrder.id.desc())).all()
        return [_to_dict(o) for o in rows]


def set_status(order_id: int, status: str, *,
               payment_status: str | None = None) -> dict[str, Any] | None:
    with SessionLocal() as s:
        o = s.get(PublicOrder, order_id)
        if o is None:
            return None
        o.status = status
        if payment_status is not None:
            o.payment_status = payment_status
        o.updated_at = _now()
        s.commit()
        return _to_dict(o)


def mark_paid(order_id: int, *, payment_status: str | None = None) -> dict[str, Any] | None:
    """Tandai pesanan lunas + potong stok (idempoten: pesanan yang sudah paid
    tidak dipotong dua kali). Return order dict, atau None bila tak ada."""
    with SessionLocal() as s:
        o = s.get(PublicOrder, order_id)
        if o is None:
            return None
        if o.status == STATUS_PAID:  # idempoten — webhook bisa terkirim ganda
            return _to_dict(o)
        tenant_id = o.tenant_id
        items = list(o.items or [])
    # Potong stok di luar sesi baca di atas (product_repo punya sesi sendiri).
    product_repo.decrement_by_ids(
        tenant_id, [{"product_id": it["product_id"], "qty": it["qty"]} for it in items])
    return set_status(order_id, STATUS_PAID, payment_status=payment_status)
