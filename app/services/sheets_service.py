"""Google Sheets staging layer untuk transaksi WA.

Tiap transaksi yang lolos validasi di-append ke Sheet sebelum dikirim ke BQ.
Kolom Sheet = kolom BQ + metadata audit (received_at, sender, bq_status).

Butuh:
  GOOGLE_APPLICATION_CREDENTIALS → service account JSON (sama dengan BQ)
  GOOGLE_SHEETS_ID                → ID Sheet (ambil dari URL)
  GOOGLE_SHEETS_TAB               → nama tab (default: 'wa_transactions')

Service account di JSON itu WAJIB diberi akses Editor ke Sheet via tombol Share.
"""
from __future__ import annotations

import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

# Pastikan .env ke-load ke os.environ supaya os.getenv() bisa baca
# GOOGLE_SHEETS_ID / GOOGLE_APPLICATION_CREDENTIALS.
load_dotenv()

log = logging.getLogger("fortunas.sheets")

_lock = threading.Lock()
_client_cache: Any = None
_worksheet_cache: Any = None
_customers_ws_cache: Any = None

# Tab master pelanggan: peta CustomerID (angka) ↔ CustomerName.
CUSTOMERS_TAB: str = os.getenv("GOOGLE_SHEETS_CUSTOMERS_TAB", "customers")
CUSTOMER_HEADERS: list[str] = ["CustomerID", "CustomerName", "created_at"]

SHEET_HEADERS: list[str] = [
    "received_at",
    "sender",
    "source",  # 'whatsapp' / 'api' / dll
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer ID",
    "Country",
    "bq_status",  # 'pending' / 'inserted' / 'failed'
    "bq_error",
    # CustomerName sengaja DI AKHIR supaya kolom bq_status (L) / bq_error (M)
    # tetap di posisi sama (update_bq_status menulis ke L:M secara hardcoded)
    # dan baris lama tidak bergeser. Nama pelanggan disimpan HANYA di Sheet —
    # tabel BigQuery utama tetap pakai 'Customer ID' (FLOAT) saja.
    "CustomerName",
]


class SheetsUnavailableError(RuntimeError):
    """Gagal terhubung ke Google Sheets (credentials / network / permission)."""


def _build_client():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError as exc:
        raise SheetsUnavailableError(
            "Package gspread belum terinstall. Jalankan: "
            "pip install gspread google-auth"
        ) from exc

    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not os.path.exists(creds_path):
        raise SheetsUnavailableError(
            "GOOGLE_APPLICATION_CREDENTIALS tidak valid. Set path ke service "
            "account JSON yang punya akses Editor ke Sheet."
        )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    return gspread.authorize(creds)


def _get_worksheet():
    global _client_cache, _worksheet_cache
    with _lock:
        if _worksheet_cache is not None:
            return _worksheet_cache

        sheet_id = os.getenv("GOOGLE_SHEETS_ID", "").strip()
        tab_name = os.getenv("GOOGLE_SHEETS_TAB", "wa_transactions").strip()
        if not sheet_id:
            raise SheetsUnavailableError(
                "GOOGLE_SHEETS_ID belum di-set di .env. Ambil ID dari URL Sheet."
            )

        if _client_cache is None:
            _client_cache = _build_client()

        try:
            spreadsheet = _client_cache.open_by_key(sheet_id)
        except Exception as exc:  # gspread.SpreadsheetNotFound atau APIError
            raise SheetsUnavailableError(
                f"Gagal buka Sheet {sheet_id}. Pastikan sudah di-share ke "
                f"service account dengan role Editor. "
                f"Detail: {type(exc).__name__}: {exc!r}"
            ) from exc

        try:
            ws = spreadsheet.worksheet(tab_name)
        except Exception:
            # Auto-create tab + header kalau belum ada
            ws = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=len(SHEET_HEADERS))
            ws.append_row(SHEET_HEADERS, value_input_option="USER_ENTERED")

        # Pastikan header baris pertama sesuai
        try:
            first_row = ws.row_values(1)
            if first_row != SHEET_HEADERS:
                ws.update("A1", [SHEET_HEADERS])
        except Exception as exc:
            log.warning("Gagal sync header Sheet: %s", exc)

        _worksheet_cache = ws
        return ws


def append_transaction(
    payload: dict[str, Any],
    sender: str,
    source: str = "whatsapp",
    bq_status: str = "pending",
    bq_error: str = "",
    customer_name: str = "",
) -> int:
    """Append satu baris ke Sheet. Return nomor baris (1-based).

    customer_name = nama pelanggan dari ucapan voice (mis. "Budi"). Disimpan di
    kolom CustomerName (Sheet saja) karena kolom 'Customer ID' di BigQuery
    bertipe FLOAT dan tidak bisa menampung nama.
    """
    ws = _get_worksheet()
    received_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    row = [
        received_at,
        sender,
        source,
        payload.get("Invoice", ""),
        payload.get("StockCode", ""),
        payload.get("Description", "") or "",
        payload.get("Quantity", ""),
        payload.get("InvoiceDate", ""),
        payload.get("Price", ""),
        payload.get("Customer ID", "") if payload.get("Customer ID") is not None else "",
        payload.get("Country", "") or "",
        bq_status,
        bq_error,
        customer_name or "",
    ]

    result = ws.append_row(row, value_input_option="USER_ENTERED")
    # append_row return updatedRange spt "wa_transactions!A12:M12"; ambil nomor baris
    try:
        updates = result.get("updates", {})
        rng = updates.get("updatedRange", "")
        if rng and "!" in rng:
            ref = rng.split("!")[-1].split(":")[0]
            digits = "".join(ch for ch in ref if ch.isdigit())
            if digits:
                return int(digits)
    except Exception:  # noqa: BLE001
        pass
    return -1


def list_recent_transactions(limit: int = 20) -> list[dict[str, Any]]:
    """Baca N baris terakhir dari Sheet (pengurutan berdasarkan urutan append)."""
    try:
        ws = _get_worksheet()
    except SheetsUnavailableError:
        return []

    try:
        all_rows = ws.get_all_values()
    except Exception as exc:  # noqa: BLE001
        log.warning("Gagal baca Sheet: %s", exc)
        return []

    if len(all_rows) <= 1:
        return []

    headers = all_rows[0]
    data_rows = all_rows[1:][-limit:]
    result: list[dict[str, Any]] = []
    for row in reversed(data_rows):  # terbaru di atas
        item = {headers[i]: (row[i] if i < len(row) else "") for i in range(len(headers))}
        result.append(item)
    return result


def max_invoice_in_sheet() -> int:
    """Invoice numerik terbesar yang tercatat di Sheet (0 kalau kosong/gagal).

    Dipakai untuk auto-increment supaya transaksi yang baru di-append (tapi
    mungkin belum terlihat di BigQuery karena streaming buffer) tetap terhitung.
    """
    try:
        ws = _get_worksheet()
        all_rows = ws.get_all_values()
    except Exception:  # noqa: BLE001
        return 0

    if len(all_rows) <= 1:
        return 0
    headers = all_rows[0]
    if "Invoice" not in headers:
        return 0
    idx = headers.index("Invoice")
    mx = 0
    for row in all_rows[1:]:
        if idx < len(row):
            try:
                mx = max(mx, int(str(row[idx]).strip()))
            except (ValueError, TypeError):
                continue
    return mx


def update_bq_status(row_number: int, status: str, error: str = "") -> None:
    """Update kolom bq_status & bq_error untuk baris yang sudah di-append."""
    if row_number <= 1:
        return
    try:
        ws = _get_worksheet()
        # bq_status = kolom L (12), bq_error = kolom M (13)
        ws.update(f"L{row_number}:M{row_number}", [[status, error]])
    except Exception as exc:  # noqa: BLE001
        log.warning("Gagal update bq_status di Sheet row %s: %s", row_number, exc)


def list_retryable_rows() -> list[tuple[int, dict[str, Any]]]:
    """Return [(row_number, row_dict), ...] untuk baris dengan status 'failed' atau 'pending'.

    row_number = nomor baris di Sheet (1-based, row 1 = header, jadi data mulai row 2).
    """
    try:
        ws = _get_worksheet()
    except SheetsUnavailableError:
        return []

    try:
        all_rows = ws.get_all_values()
    except Exception as exc:  # noqa: BLE001
        log.warning("Gagal baca Sheet untuk retry: %s", exc)
        return []

    if len(all_rows) <= 1:
        return []

    headers = all_rows[0]
    retryable: list[tuple[int, dict[str, Any]]] = []
    for idx, row in enumerate(all_rows[1:], start=2):  # start=2 karena row 1 = header
        item = {headers[i]: (row[i] if i < len(row) else "") for i in range(len(headers))}
        status = str(item.get("bq_status", "")).strip().lower()
        if status in ("failed", "pending", ""):
            retryable.append((idx, item))
    return retryable


# ────────────────────── Customer master (tab 'customers') ──────────────────────


def _get_customers_ws():
    """Worksheet master pelanggan. Auto-create + header kalau belum ada."""
    global _client_cache, _customers_ws_cache
    with _lock:
        if _customers_ws_cache is not None:
            return _customers_ws_cache

        sheet_id = os.getenv("GOOGLE_SHEETS_ID", "").strip()
        if not sheet_id:
            raise SheetsUnavailableError("GOOGLE_SHEETS_ID belum di-set di .env.")

        if _client_cache is None:
            _client_cache = _build_client()

        spreadsheet = _client_cache.open_by_key(sheet_id)
        try:
            ws = spreadsheet.worksheet(CUSTOMERS_TAB)
        except Exception:
            ws = spreadsheet.add_worksheet(
                title=CUSTOMERS_TAB, rows=1000, cols=len(CUSTOMER_HEADERS)
            )
            ws.append_row(CUSTOMER_HEADERS, value_input_option="USER_ENTERED")

        _customers_ws_cache = ws
        return ws


def lookup_customer_id_by_name(name: str) -> int | None:
    """Cari CustomerID untuk nama (case-insensitive). None kalau belum terdaftar."""
    target = (name or "").strip().lower()
    if not target:
        return None
    try:
        rows = _get_customers_ws().get_all_values()
    except Exception:  # noqa: BLE001
        return None
    if len(rows) <= 1:
        return None
    hdr = rows[0]
    try:
        id_idx = hdr.index("CustomerID")
        name_idx = hdr.index("CustomerName")
    except ValueError:
        return None
    for row in rows[1:]:
        if name_idx < len(row) and row[name_idx].strip().lower() == target:
            if id_idx < len(row):
                try:
                    return int(float(row[id_idx]))
                except (ValueError, TypeError):
                    continue
    return None


def max_customer_id_in_master() -> int:
    """CustomerID terbesar di master (0 kalau kosong/gagal)."""
    try:
        rows = _get_customers_ws().get_all_values()
    except Exception:  # noqa: BLE001
        return 0
    if len(rows) <= 1:
        return 0
    hdr = rows[0]
    if "CustomerID" not in hdr:
        return 0
    idx = hdr.index("CustomerID")
    mx = 0
    for row in rows[1:]:
        if idx < len(row):
            try:
                mx = max(mx, int(float(row[idx])))
            except (ValueError, TypeError):
                continue
    return mx


def append_customer(customer_id: int, name: str) -> None:
    """Daftarkan pelanggan baru ke master."""
    ws = _get_customers_ws()
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ws.append_row(
        [customer_id, name, created_at], value_input_option="USER_ENTERED"
    )
