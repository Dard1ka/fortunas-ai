"""Riwayat transaksi milik UMKM (dibaca dari BigQuery per-tenant).

Setiap UMKM hanya melihat transaksinya sendiri: ref tabel dibangun dari
TenantContext (`{prefix}_transactions`), diisolasi lewat JWT. Dipakai untuk
tampilan Riwayat & sumber analisis AI. Empty-safe saat BQ belum aktif.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.tenancy import TenantContext, get_current_tenant
from app.schemas import (
    UmkmTransaction,
    UmkmTransactionItem,
    UmkmTransactionsResponse,
)
from app.services import transactions_service

router = APIRouter(tags=["transactions"])


@router.get("/umkm/transactions", response_model=UmkmTransactionsResponse)
def list_transactions(
    limit: int = Query(default=transactions_service.DEFAULT_LIMIT, ge=1, le=transactions_service.MAX_LIMIT),
    tenant: TenantContext = Depends(get_current_tenant),
) -> UmkmTransactionsResponse:
    rows = transactions_service.list_umkm_transactions(tenant, limit=limit)
    txs = [
        UmkmTransaction(
            invoice=r["invoice"],
            customer=r.get("customer", ""),
            country=r.get("country", ""),
            invoice_date=r.get("invoice_date", ""),
            total=r.get("total", 0),
            items=[UmkmTransactionItem(**it) for it in r.get("items", [])],
        )
        for r in rows
    ]
    return UmkmTransactionsResponse(
        transactions=txs, count=len(txs), source="bigquery" if txs else "")
