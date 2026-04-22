"""Validator transaksi WA — pakai type-coercion dari excel_upload + rules tambahan.

Rules ekstra (di luar tipe kolom):
- Quantity & Price bounds (0 < qty <= 10_000, 0 < price <= 1_000_000)
- InvoiceDate tidak di masa depan >24 jam, tidak sebelum tahun 2000
- Invoice duplicate check (cross-check BigQuery)
- Sender allowlist (env WA_ALLOWED_SENDERS, comma-separated)
- Rate limit in-memory per sender
"""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.excel_upload import (
    _clean_str,
    _coerce_float,
    _coerce_int,
    _parse_invoice_date,
)

MAX_QUANTITY = 10_000
MAX_PRICE = 1_000_000.0

# Rate limit: max N pesan per window detik per pengirim
RATE_LIMIT_WINDOW_S = 60
RATE_LIMIT_MAX_MSG = 10

_rate_lock = threading.Lock()
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)


class WaValidationError(ValueError):
    """Pesan WA tidak lolos validasi."""


# ────────────────────── Sender allowlist ──────────────────────


def _normalize_sender(raw: str) -> str:
    """Normalisasi nomor WA: hapus prefix 'whatsapp:', spasi, tanda +."""
    if not raw:
        return ""
    s = raw.strip().lower().replace("whatsapp:", "").replace(" ", "")
    if s.startswith("+"):
        s = s[1:]
    return s


def is_sender_allowed(sender: str) -> bool:
    raw = os.getenv("WA_ALLOWED_SENDERS", "").strip()
    if not raw:
        # Kalau allowlist kosong → terbuka (mode dev). Di production WAJIB isi.
        return True
    allowed = {_normalize_sender(x) for x in raw.split(",") if x.strip()}
    return _normalize_sender(sender) in allowed


# ────────────────────── Rate limit ──────────────────────


def check_rate_limit(sender: str) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds). allowed=False kalau melampaui limit."""
    now = time.time()
    key = _normalize_sender(sender) or "__anon__"
    with _rate_lock:
        bucket = _rate_buckets[key]
        # Buang timestamp di luar window
        while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_S:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT_MAX_MSG:
            retry = int(RATE_LIMIT_WINDOW_S - (now - bucket[0])) + 1
            return False, max(1, retry)
        bucket.append(now)
    return True, 0


# ────────────────────── Payload validation ──────────────────────


def _validate_date_bounds(dt: datetime) -> str | None:
    now = datetime.now(timezone.utc)
    if dt > now + timedelta(hours=24):
        return "InvoiceDate tidak boleh di masa depan."
    if dt < datetime(2000, 1, 1, tzinfo=timezone.utc):
        return "InvoiceDate terlalu jauh di masa lalu (minimum tahun 2000)."
    return None


def validate_payload(raw: dict[str, str]) -> dict[str, Any]:
    """Parse tipe + cek rules. Raise WaValidationError kalau gagal.

    Return dict siap-insert-ke-BQ (key = nama kolom BQ).
    """
    invoice = _coerce_int(raw.get("Invoice"))
    stock = _clean_str(raw.get("StockCode"))
    desc = _clean_str(raw.get("Description"))
    qty = _coerce_int(raw.get("Quantity"))
    price = _coerce_float(raw.get("Price"))
    dt = _parse_invoice_date(raw.get("InvoiceDate"))
    customer = _coerce_float(raw.get("Customer ID"))
    country = _clean_str(raw.get("Country"))

    errors: list[str] = []

    if invoice is None:
        errors.append("Invoice wajib angka (INTEGER).")
    if not stock:
        errors.append("StockCode wajib diisi.")
    if qty is None:
        errors.append("Quantity wajib angka (INTEGER).")
    elif qty <= 0:
        errors.append("Quantity harus > 0.")
    elif qty > MAX_QUANTITY:
        errors.append(f"Quantity melebihi batas wajar ({MAX_QUANTITY:,}).")
    if price is None:
        errors.append("Price wajib angka (FLOAT).")
    elif price <= 0:
        errors.append("Price harus > 0.")
    elif price > MAX_PRICE:
        errors.append(f"Price melebihi batas wajar ({MAX_PRICE:,.0f}).")
    if dt is None:
        errors.append("InvoiceDate tidak bisa di-parse (contoh: 2009-12-01 09:24:00).")
    else:
        bound_err = _validate_date_bounds(dt)
        if bound_err:
            errors.append(bound_err)

    if errors:
        raise WaValidationError(" • ".join(errors))

    # Build payload BQ (dt dijamin not None setelah cek di atas)
    assert dt is not None
    return {
        "Invoice": invoice,
        "StockCode": stock,
        "Description": desc,
        "Quantity": qty,
        "InvoiceDate": dt.isoformat(),
        "Price": price,
        "Customer ID": customer,
        "Country": country,
    }


# ────────────────────── Duplicate check ──────────────────────


def check_duplicate_in_bq(invoice: int, stock_code: str) -> bool:
    """Cek apakah kombinasi (Invoice, StockCode) sudah ada di BigQuery.

    Return True kalau DUPLICATE (artinya tolak).
    Gagal silent (return False) kalau BQ error — biar bot tetap jalan.
    """
    try:
        from app.bigquery_service import get_bigquery_client
        from app.core.config import get_settings

        settings = get_settings()
        table = (
            f"`{settings.bigquery_project_id}."
            f"{settings.bigquery_dataset}.{settings.bigquery_table}`"
        )
        sql = (
            f"SELECT COUNT(1) AS n FROM {table} "
            f"WHERE Invoice = @invoice AND StockCode = @stock LIMIT 1"
        )
        from google.cloud import bigquery

        client = get_bigquery_client()
        job = client.query(
            sql,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("invoice", "INT64", invoice),
                    bigquery.ScalarQueryParameter("stock", "STRING", stock_code),
                ]
            ),
        )
        for row in job.result():
            return int(row["n"]) > 0
    except Exception:
        return False
    return False
