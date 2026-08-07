"""Inbox pesanan publik untuk UMKM (butuh auth tenant).

Pelanggan memesan lewat `routes/public.py` (tanpa auth); di sini pemilik UMKM
melihat pesanan yang masuk dan menggerakkan statusnya.

Endpoint dibuat PER-AKSI, bukan `PATCH {status}` generik: dengan PATCH generik
UMKM bisa mengirim `expired` atau `cancelled` — status yang hak sistem (job
kedaluwarsa & webhook gateway). Per-aksi memberi penyaringan itu gratis, dan
tiap aksi punya prasyarat berbeda (lihat `order_repo._ALLOWED_FROM`).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app import order_repo
from app.core.tenancy import TenantContext, get_current_tenant
from app.schemas import UmkmOrder, UmkmOrderListResponse
from app.services import checkout_service

router = APIRouter(tags=["orders"])

# Tanpa filter, inbox menampilkan yang BUTUH TINDAKAN: `paid` (perlu diterima)
# dan `accepted` (perlu diselesaikan). `pending_payment` disembunyikan default —
# itu keranjang yang belum dibayar, kebisingan bagi UMKM.
_ACTIONABLE = [order_repo.STATUS_PAID, order_repo.STATUS_ACCEPTED]


@router.get("/umkm/orders", response_model=UmkmOrderListResponse)
def list_umkm_orders(
    status: str | None = Query(default=None,
                               description="status tunggal, atau 'all' untuk semua"),
    tenant: TenantContext = Depends(get_current_tenant),
) -> UmkmOrderListResponse:
    if status == "all":
        statuses = None
    elif status:
        statuses = [status]
    else:
        statuses = _ACTIONABLE
    rows = order_repo.list_orders(tenant.tenant_id, statuses)
    return UmkmOrderListResponse(
        orders=[UmkmOrder(**o) for o in rows], count=len(rows))


def _act(tenant_id: int, order_id: int, action: str) -> UmkmOrder:
    """Jalankan aksi + petakan kegagalan ke kode HTTP.

    404 untuk pesanan tak ada MAUPUN milik tenant lain — 403 akan mengakui
    bahwa pesanan itu ada.
    """
    try:
        o = order_repo.apply_action(tenant_id, order_id, action)
    except order_repo.TransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if o is None:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan.")
    return UmkmOrder(**o)


@router.post("/umkm/orders/{order_id}/accept", response_model=UmkmOrder)
def accept_order(order_id: int,
                 tenant: TenantContext = Depends(get_current_tenant)) -> UmkmOrder:
    """`paid` → `accepted`. UMKM menyanggupi pesanan."""
    return _act(tenant.tenant_id, order_id, "accept")


@router.post("/umkm/orders/{order_id}/reject", response_model=UmkmOrder)
def reject_order(order_id: int,
                 tenant: TenantContext = Depends(get_current_tenant)) -> UmkmOrder:
    """`paid` → `rejected`. Stok dikembalikan otomatis; UANG tidak (manual)."""
    return _act(tenant.tenant_id, order_id, "reject")


@router.post("/umkm/orders/{order_id}/complete", response_model=UmkmOrder)
def complete_order(order_id: int,
                   tenant: TenantContext = Depends(get_current_tenant)) -> UmkmOrder:
    """`accepted` → `completed`, lalu jembatani penjualan ke BigQuery (Slice 2).

    Penulisan BigQuery dilakukan HANYA di sini (bukan di `order_repo.apply_action`)
    supaya `order_repo` tetap murni relasional dan bebas dependensi BigQuery.
    Titik `completed` = barang diserahkan; baru di sinilah pesanan online layak
    dihitung sebagai penjualan oleh analitik/riwayat (semua baca BigQuery).

    Jembatan best-effort: pesanan sudah `completed` terlebih dulu, jadi kegagalan
    BigQuery tak membatalkan penyelesaian (lihat `checkout_service`). Karena
    transisi `accepted → completed` dijaga compare-and-set, `complete` hanya
    menang SEKALI — jadi jembatan ini tak pernah menulis pesanan yang sama dua kali.
    """
    try:
        order = order_repo.apply_action(tenant.tenant_id, order_id, "complete")
    except order_repo.TransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if order is None:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan.")
    checkout_service.persist_completed_order(order, tenant)
    return UmkmOrder(**order)
