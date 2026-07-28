"""Baca riwayat transaksi milik SATU UMKM dari BigQuery (tenant-scoped).

Sumber kebenaran transaksi = tabel BigQuery per-tenant `{prefix}_transactions`
(ditulis oleh checkout_service & voice). Modul ini menyediakan sisi BACA untuk
UMKM melihat/menganalisis riwayatnya sendiri — TIDAK pernah menyentuh tabel
tenant lain (ref tabel dibangun dari TenantContext.table()).

BigQuery disembunyikan di belakang seam lazy `_bq_query_transactions` supaya:
  - modul ini tetap import bersih di CI (tanpa google-cloud), dan
  - saat BQ mati / kredensial belum ada, endpoint balas daftar kosong (bukan 500).
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.tenancy import TenantContext

logger = logging.getLogger(__name__)

# Batas aman baris yang ditarik dari BQ per permintaan.
DEFAULT_LIMIT = 200
MAX_LIMIT = 1000


def _bq_query_transactions(tx_table: str, limit: int) -> list[dict[str, Any]]:  # pragma: no cover
    """Seam BQ: ambil baris transaksi terbaru tenant. Satu baris = satu line item.

    Diisolasi (import google di dalam fungsi) supaya CI tetap bersih. Kolom mengikuti
    skema online_retail (lihat wa_validator.validate_payload).
    """
    from app.bigquery_service import get_bigquery_client

    client = get_bigquery_client()
    sql = (
        "SELECT Invoice, StockCode, Description, Quantity, Price, "
        "InvoiceDate, `Customer ID` AS CustomerID, Country "
        f"FROM `{tx_table}` "
        "ORDER BY Invoice DESC "
        f"LIMIT {int(limit)}"
    )
    return [dict(row) for row in client.query(sql).result()]


def _row_item(row: dict[str, Any]) -> dict[str, Any]:
    qty = int(row.get("Quantity") or 0)
    price = int(float(row.get("Price") or 0))
    return {
        "product": (row.get("Description") or row.get("StockCode") or "").strip(),
        "stock_code": (row.get("StockCode") or "").strip(),
        "qty": qty,
        "unit_price": price,
        "total": qty * price,
    }


def _group_by_invoice(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Gabung baris (line item) menjadi transaksi per Invoice, urut terbaru dulu."""
    order: list[str] = []
    bucket: dict[str, dict[str, Any]] = {}
    for row in rows:
        inv = str(row.get("Invoice") or "").strip()
        if not inv:
            continue
        if inv not in bucket:
            order.append(inv)
            bucket[inv] = {
                "invoice": inv,
                "customer": str(row.get("CustomerID") or "").strip(),
                "country": (row.get("Country") or "").strip(),
                "invoice_date": str(row.get("InvoiceDate") or "").strip(),
                "items": [],
                "total": 0,
            }
        item = _row_item(row)
        bucket[inv]["items"].append(item)
        bucket[inv]["total"] += item["total"]
    return [bucket[i] for i in order]


def list_umkm_transactions(tenant: TenantContext, limit: int = DEFAULT_LIMIT) -> list[dict[str, Any]]:
    """Riwayat transaksi milik `tenant` dari BigQuery, dikelompokkan per invoice.

    Empty-safe: BQ mati / tabel belum ada / kredensial kosong → daftar kosong.
    """
    limit = max(1, min(int(limit or DEFAULT_LIMIT), MAX_LIMIT))
    tx_table = tenant.table("transactions")
    try:
        rows = _bq_query_transactions(tx_table, limit)
    except Exception as exc:  # noqa: BLE001 — jangan 500-kan UMKM saat BQ tak tersedia
        logger.warning("Gagal baca transaksi BQ untuk tenant %s: %s", tenant.tenant_id, exc)
        return []
    return _group_by_invoice(rows)
