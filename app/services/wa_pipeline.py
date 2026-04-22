"""Orchestrator alur transaksi WhatsApp.

Flow:
  1. parse (wa_parser)
  2. validate kolom + tipe + rules tambahan (wa_validator)
  3. duplicate check (BigQuery)
  4. append ke Google Sheets (staging, selalu dilakukan dulu)
  5. insert ke BigQuery
  6. update bq_status di Sheet
  7. return pesan balasan user-friendly

Tiap step punya error handling yang menghasilkan pesan balasan WA yang jelas.
"""
from __future__ import annotations

import logging
from typing import Any

from app.services import sheets_service
from app.services.excel_upload import _insert_in_batches
from app.services.wa_parser import WaParseError, parse_wa_message
from app.services.wa_validator import (
    WaValidationError,
    check_duplicate_in_bq,
    check_rate_limit,
    is_sender_allowed,
    validate_payload,
)

log = logging.getLogger("fortunas.wa")


def _format_success(payload: dict[str, Any]) -> str:
    return (
        "✅ Transaksi masuk!\n"
        f"Invoice {payload['Invoice']} · {payload['StockCode']}\n"
        f"Qty {payload['Quantity']} @ {payload['Price']}\n"
        f"Tanggal {payload['InvoiceDate']}\n"
        f"Customer {payload.get('Customer ID') or '—'}"
    )


def process_wa_message(message: str, sender: str) -> dict[str, Any]:
    """Proses 1 pesan WA. Return dict:
      {
        "ok": bool,
        "reply": str,                # pesan balasan ke user (plaintext)
        "payload": dict | None,      # payload BQ kalau sukses
        "status": "success"|"rejected"|"duplicate"|"parse_error"|"validation_error"
                  |"rate_limited"|"forbidden"|"bq_error"|"sheets_error",
      }
    """
    # ── 1. Allowlist ────────────────────────────────────────────
    if not is_sender_allowed(sender):
        return {
            "ok": False,
            "status": "forbidden",
            "reply": "🚫 Nomor kamu belum terdaftar untuk input transaksi. Hubungi admin.",
            "payload": None,
        }

    # ── 2. Rate limit ──────────────────────────────────────────
    allowed, retry = check_rate_limit(sender)
    if not allowed:
        return {
            "ok": False,
            "status": "rate_limited",
            "reply": f"⏳ Terlalu banyak pesan. Coba lagi dalam {retry} detik.",
            "payload": None,
        }

    # ── 3. Parse ───────────────────────────────────────────────
    try:
        raw = parse_wa_message(message)
    except WaParseError as exc:
        return {
            "ok": False,
            "status": "parse_error",
            "reply": f"⚠️ Gagal baca pesan.\n{exc}",
            "payload": None,
        }

    # ── 4. Validate kolom + tipe + bounds ──────────────────────
    try:
        payload = validate_payload(raw)
    except WaValidationError as exc:
        return {
            "ok": False,
            "status": "validation_error",
            "reply": f"⚠️ Data tidak lolos validasi.\n{exc}",
            "payload": None,
        }

    # ── 5. Duplicate check ─────────────────────────────────────
    if check_duplicate_in_bq(int(payload["Invoice"]), str(payload["StockCode"])):
        return {
            "ok": False,
            "status": "duplicate",
            "reply": (
                f"⚠️ Transaksi duplikat: Invoice {payload['Invoice']} + "
                f"{payload['StockCode']} sudah ada di database."
            ),
            "payload": payload,
        }

    # ── 6. Append ke Sheets (staging) ──────────────────────────
    row_number = -1
    try:
        row_number = sheets_service.append_transaction(
            payload=payload,
            sender=sender,
            source="whatsapp",
            bq_status="pending",
        )
    except sheets_service.SheetsUnavailableError as exc:
        log.warning("Sheets unavailable, lanjut tanpa staging: %s", exc)
    except Exception as exc:  # noqa: BLE001
        log.exception("Sheets append gagal: %s", exc)

    # ── 7. Insert ke BigQuery ──────────────────────────────────
    try:
        inserted, errors = _insert_in_batches([payload])
    except PermissionError as exc:
        sheets_service.update_bq_status(row_number, "failed", str(exc)[:200])
        return {
            "ok": False,
            "status": "bq_error",
            "reply": (
                "❌ Gagal kirim ke BigQuery (izin service account). "
                "Data sudah tersimpan di Sheet staging untuk retry."
            ),
            "payload": payload,
        }
    except Exception as exc:  # noqa: BLE001
        sheets_service.update_bq_status(row_number, "failed", str(exc)[:200])
        return {
            "ok": False,
            "status": "bq_error",
            "reply": (
                f"❌ Gagal kirim ke BigQuery: {exc}. "
                "Data sudah tersimpan di Sheet staging untuk retry."
            ),
            "payload": payload,
        }

    if errors or inserted != 1:
        msg = "; ".join(errors) if errors else "unknown"
        sheets_service.update_bq_status(row_number, "failed", msg[:200])
        return {
            "ok": False,
            "status": "bq_error",
            "reply": f"❌ BigQuery menolak row: {msg}",
            "payload": payload,
        }

    sheets_service.update_bq_status(row_number, "inserted", "")
    return {
        "ok": True,
        "status": "success",
        "reply": _format_success(payload),
        "payload": payload,
    }


# ────────────────────── Retry job ──────────────────────


def _row_to_bq_payload(row: dict[str, Any]) -> dict[str, Any] | None:
    """Ambil kolom BQ dari row Sheet, coerce tipe seperlunya. Return None kalau row
    tidak bisa dibentuk (mis. Invoice kosong)."""
    from app.services.excel_upload import (
        _clean_str,
        _coerce_float,
        _coerce_int,
        _parse_invoice_date,
    )

    invoice = _coerce_int(row.get("Invoice"))
    stock = _clean_str(row.get("StockCode"))
    qty = _coerce_int(row.get("Quantity"))
    price = _coerce_float(row.get("Price"))
    dt = _parse_invoice_date(row.get("InvoiceDate"))

    if invoice is None or not stock or qty is None or price is None or dt is None:
        return None

    return {
        "Invoice": invoice,
        "StockCode": stock,
        "Description": _clean_str(row.get("Description")),
        "Quantity": qty,
        "InvoiceDate": dt.isoformat(),
        "Price": price,
        "Customer ID": _coerce_float(row.get("Customer ID")),
        "Country": _clean_str(row.get("Country")),
    }


def retry_failed_rows(max_rows: int = 100) -> dict[str, Any]:
    """Scan Sheet untuk baris status failed/pending, coba kirim ulang ke BigQuery.

    Return ringkasan:
      {
        "scanned": int,
        "retried": int,
        "inserted": int,
        "still_failed": int,
        "skipped_malformed": int,
        "details": [ {"row": N, "status": "inserted"|"failed"|"skipped", "reason": str}, ...]
      }
    """
    from app.services.excel_upload import _insert_in_batches
    from app.services.wa_validator import check_duplicate_in_bq

    retryable = sheets_service.list_retryable_rows()[:max_rows]
    summary: dict[str, Any] = {
        "scanned": len(retryable),
        "retried": 0,
        "inserted": 0,
        "still_failed": 0,
        "skipped_malformed": 0,
        "duplicates": 0,
        "details": [],
    }

    for row_number, row in retryable:
        payload = _row_to_bq_payload(row)
        if payload is None:
            summary["skipped_malformed"] += 1
            sheets_service.update_bq_status(
                row_number, "skipped", "Row tidak lengkap / tipe invalid"
            )
            summary["details"].append({
                "row": row_number,
                "status": "skipped",
                "reason": "malformed row",
            })
            continue

        # Cek duplikat sebelum retry — baris yang sebenarnya sudah masuk BQ
        # (mungkin retry sebelumnya sukses tapi Sheet gagal update)
        if check_duplicate_in_bq(int(payload["Invoice"]), str(payload["StockCode"])):
            summary["duplicates"] += 1
            sheets_service.update_bq_status(row_number, "inserted", "already in BQ (dedup on retry)")
            summary["details"].append({
                "row": row_number,
                "status": "duplicate",
                "reason": "sudah ada di BQ",
            })
            continue

        summary["retried"] += 1
        try:
            inserted, errors = _insert_in_batches([payload])
        except Exception as exc:  # noqa: BLE001
            summary["still_failed"] += 1
            sheets_service.update_bq_status(row_number, "failed", str(exc)[:200])
            summary["details"].append({
                "row": row_number,
                "status": "failed",
                "reason": str(exc)[:200],
            })
            continue

        if errors or inserted != 1:
            msg = "; ".join(errors) if errors else "unknown"
            summary["still_failed"] += 1
            sheets_service.update_bq_status(row_number, "failed", msg[:200])
            summary["details"].append({
                "row": row_number,
                "status": "failed",
                "reason": msg[:200],
            })
        else:
            summary["inserted"] += 1
            sheets_service.update_bq_status(row_number, "inserted", "")
            summary["details"].append({
                "row": row_number,
                "status": "inserted",
                "reason": "",
            })

    log.info(
        "WA retry done: scanned=%d retried=%d inserted=%d failed=%d skipped=%d dup=%d",
        summary["scanned"], summary["retried"], summary["inserted"],
        summary["still_failed"], summary["skipped_malformed"], summary["duplicates"],
    )
    return summary
