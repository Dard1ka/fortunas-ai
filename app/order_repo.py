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


class TransitionError(Exception):
    """Aksi UMKM tak sah dari status pesanan sekarang (route → 409)."""


# Aksi UMKM → himpunan status sumber yang sah. SATU sumber kebenaran: ketiga
# endpoint di routes/orders.py memvalidasi lewat tabel ini.
_ALLOWED_FROM: dict[str, set[str]] = {
    "accept": {STATUS_PAID},
    "reject": {STATUS_PAID},
    "complete": {STATUS_ACCEPTED},
}
_RESULT_STATUS: dict[str, str] = {
    "accept": STATUS_ACCEPTED,
    "reject": STATUS_REJECTED,
    "complete": STATUS_COMPLETED,
}


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
        "paid_at": o.paid_at,
        "stock_restored_at": o.stock_restored_at,
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


def list_orders(tenant_id: int,
                statuses: list[str] | None = None) -> list[dict[str, Any]]:
    """Pesanan milik tenant, terbaru dulu. `statuses=None` → semua status.

    Menerima DAFTAR status (bukan satu) karena inbox default menampilkan dua
    status sekaligus: `paid` (perlu diterima) + `accepted` (perlu diselesaikan).
    """
    with SessionLocal() as s:
        q = select(PublicOrder).where(PublicOrder.tenant_id == tenant_id)
        if statuses:
            q = q.where(PublicOrder.status.in_(statuses))
        rows = s.scalars(q.order_by(PublicOrder.id.desc())).all()
        return [_to_dict(o) for o in rows]


def get_order_for_tenant(tenant_id: int, order_id: int) -> dict[str, Any] | None:
    """Ambil pesanan milik tenant. None bila tak ada ATAU milik tenant lain.

    `get_order` biasa tak kenal tenant karena dipakai jalur publik. Route UMKM
    WAJIB lewat sini: tanpa penyaringan tenant, UMKM A bisa menerima/menolak
    pesanan UMKM B hanya dengan menebak id. Route membalas 404 (bukan 403) untuk
    keduanya — 403 akan mengakui bahwa pesanan itu ada.
    """
    with SessionLocal() as s:
        o = s.get(PublicOrder, order_id)
        if o is None or o.tenant_id != tenant_id:
            return None
        return _to_dict(o)


def _update(order_id: int, **fields: Any) -> dict[str, Any] | None:
    """Terapkan perubahan field ke satu pesanan + stempel updated_at.

    Satu-satunya tempat yang tahu cara menulis baris pesanan, supaya
    set_status/mark_paid/restore_stock tidak mengencerkan aturannya
    masing-masing lalu menyimpang.
    """
    with SessionLocal() as s:
        o = s.get(PublicOrder, order_id)
        if o is None:
            return None
        for k, v in fields.items():
            setattr(o, k, v)
        o.updated_at = _now()
        s.commit()
        return _to_dict(o)


def set_status(order_id: int, status: str, *,
               payment_status: str | None = None) -> dict[str, Any] | None:
    fields: dict[str, Any] = {"status": status}
    if payment_status is not None:
        fields["payment_status"] = payment_status
    return _update(order_id, **fields)


def mark_paid(order_id: int, *, payment_status: str | None = None) -> dict[str, Any] | None:
    """Tandai pesanan lunas + potong stok — SEKALI saja.

    Idempoten lewat `paid_at`, BUKAN lewat status sekarang. Guard lama
    (`status == STATUS_PAID`) bocor begitu UMKM menerima pesanan: status jadi
    `accepted`, lalu notifikasi settlement ulang dari gateway (Midtrans mengirim
    ganda dan bisa di-retrigger manual dari dashboard) lolos guard → stok
    terpotong dua kali DAN status mundur ke `paid`, membatalkan penerimaan UMKM.
    """
    with SessionLocal() as s:
        o = s.get(PublicOrder, order_id)
        if o is None:
            return None
        if o.paid_at is not None:  # pernah lunas → tanpa efek apa pun
            return _to_dict(o)
        tenant_id = o.tenant_id
        items = list(o.items or [])
    # Potong stok di luar sesi baca di atas (product_repo punya sesi sendiri).
    product_repo.decrement_by_ids(
        tenant_id, [{"product_id": it["product_id"], "qty": it["qty"]} for it in items])
    fields: dict[str, Any] = {"status": STATUS_PAID, "paid_at": _now()}
    if payment_status is not None:
        fields["payment_status"] = payment_status
    return _update(order_id, **fields)


def restore_stock(order_id: int) -> bool:
    """Kembalikan stok pesanan yang PERNAH lunas. Idempoten via `stock_restored_at`.

    Return True hanya bila stok benar-benar dikembalikan pada pemanggilan ini.
    False bila pesanan tak ada, belum pernah lunas (stok belum dipotong), atau
    stoknya sudah dikembalikan.
    """
    with SessionLocal() as s:
        o = s.get(PublicOrder, order_id)
        if o is None or o.paid_at is None or o.stock_restored_at is not None:
            return False
        tenant_id = o.tenant_id
        items = list(o.items or [])
    product_repo.restore_by_ids(
        tenant_id, [{"product_id": it["product_id"], "qty": it["qty"]} for it in items])
    return _update(order_id, stock_restored_at=_now()) is not None


def apply_action(tenant_id: int, order_id: int,
                 action: str) -> dict[str, Any] | None:
    """Jalankan aksi UMKM (`accept` | `reject` | `complete`) dengan validasi transisi.

    Return order terbaru. None bila pesanan tak ada / bukan milik tenant.
    Raise `TransitionError` bila status sekarang tak mengizinkan aksi itu.

    `reject` mengembalikan stok lebih dulu (idempoten) — pesanan yang sudah lunas
    berarti stoknya sudah dipotong; menolak tanpa mengembalikan membuat barang yang
    tak terjual tercatat terjual. Pengembalian UANG tidak otomatis (bucket B).
    """
    o = get_order_for_tenant(tenant_id, order_id)
    if o is None:
        return None
    if o["status"] not in _ALLOWED_FROM[action]:
        raise TransitionError(
            f"Pesanan berstatus '{o['status']}' tidak bisa di-{action}.")
    if action == "reject":
        restore_stock(order_id)
    return set_status(order_id, _RESULT_STATUS[action])
