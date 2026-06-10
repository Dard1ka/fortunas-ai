"""Structured-transaction entry point (skip parse step).

The standard wa_pipeline.process_wa_message starts from a raw text message and
runs parse → validate → duplicate → sheets → bigquery. For voice flows we
already have a parsed + user-confirmed dict from the frontend, so we skip the
parse step but reuse everything else.

Mapping (voice payload → wa schema):
  invoice    → Invoice       (int — strip non-digits if needed)
  product    → Description   (also reused as StockCode if no separate code)
  qty        → Quantity
  unit_price → Price
  customer   → Customer ID   (float-coerced; blank → omitted)
  country    → Country
  + InvoiceDate is auto-filled with now() (UTC ISO)
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

from app.services import sheets_service
from app.services.excel_upload import _insert_in_batches
from app.services.wa_validator import (
    WaValidationError,
    check_duplicate_in_bq,
    validate_payload,
)

log = logging.getLogger("fortunas.voice")


def _strip_to_digits(s: str) -> str:
    digits = re.sub(r"\D", "", s or "")
    return digits


def _stock_code_from_product(product: str) -> str:
    """Derive a stable StockCode from product name. Uppercase + alphanumeric only,
    capped at 16 chars. e.g. 'Sabun Cuci' → 'SABUNCUCI'."""
    code = re.sub(r"[^A-Za-z0-9]", "", product or "").upper()
    return (code or "VOICE")[:16]


def to_wa_payload(structured: dict[str, Any]) -> dict[str, str]:
    """Reshape voice payload to wa_validator-compatible raw dict."""
    invoice_digits = _strip_to_digits(str(structured.get("invoice", "")))
    if not invoice_digits:
        raise WaValidationError(
            "Invoice harus berisi angka. Contoh: 'INV-2024' atau '489438'."
        )

    return {
        "Invoice": invoice_digits,
        "StockCode": str(structured.get("stock_code") or _stock_code_from_product(structured.get("product", ""))),
        "Description": str(structured.get("product") or ""),
        "Quantity": str(structured.get("qty", "")),
        "InvoiceDate": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "Price": str(structured.get("unit_price", "")),
        "Customer ID": str(structured.get("customer", "") or "").strip(),
        "Country": str(structured.get("country") or "Indonesia"),
    }


def process_structured_transaction(structured: dict[str, Any], sender: str = "voice_user") -> dict[str, Any]:
    """Voice/structured entry. Mirrors wa_pipeline.process_wa_message minus parse step.

    Returns the same shape:
        { ok, status, reply, payload, row_number? }
    """
    try:
        raw = to_wa_payload(structured)
    except WaValidationError as exc:
        return {"ok": False, "status": "validation_error", "reply": f"❌ {exc}", "payload": None}

    try:
        payload = validate_payload(raw)
    except WaValidationError as exc:
        return {"ok": False, "status": "validation_error", "reply": f"❌ {exc}", "payload": None}

    if check_duplicate_in_bq(payload["Invoice"], payload["StockCode"]):
        return {
            "ok": False,
            "status": "duplicate",
            "reply": (
                f"⚠ Invoice {payload['Invoice']} dengan StockCode {payload['StockCode']} "
                "sudah ada di BigQuery. Transaksi tidak ditambahkan dua kali."
            ),
            "payload": payload,
        }

    # Sheets-first staging (audit trail, even if BigQuery insert fails).
    row_number = -1
    try:
        row_number = sheets_service.append_transaction(
            payload=payload,
            sender=sender,
            source="voice",
            bq_status="pending",
            bq_error="",
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("Sheets append failed (continuing to BQ): %s", exc)

    inserted, errors = _insert_in_batches([payload])

    bq_status = "success" if inserted > 0 and not errors else "failed"
    bq_error = "; ".join(errors[:3]) if errors else ""

    if row_number > 0:
        try:
            sheets_service.update_bq_status(row_number, bq_status, bq_error)
        except Exception as exc:  # noqa: BLE001
            log.warning("Sheets status update failed: %s", exc)

    if bq_status != "success":
        return {
            "ok": False,
            "status": "bq_error",
            "reply": f"⚠ BigQuery insert gagal: {bq_error or 'unknown error'}",
            "payload": payload,
            "row_number": row_number,
        }

    return {
        "ok": True,
        "status": "success",
        "reply": (
            f"✅ Transaksi {payload['Invoice']} ({payload['Description']}) berhasil dicatat. "
            f"Tersimpan di Google Sheets (baris {row_number}) dan BigQuery."
        ),
        "payload": payload,
        "row_number": row_number,
    }
