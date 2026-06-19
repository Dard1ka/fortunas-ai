"""Voice/structured transaction → BigQuery (tenant-aware, Sheets-free).

Tiap tenant punya tabel sendiri di dataset bersama:
  {prefix}_transactions  (skema online_retail)
  {prefix}_customers     (CustomerID, CustomerName, created_at)

Tidak ada Google Sheets di jalur multi-tenant — transaksi langsung ke BigQuery.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

from google.cloud import bigquery

from app.bigquery_service import get_bigquery_client
from app.core.tenancy import TenantContext
from app.services.excel_upload import _insert_in_batches
from app.services.wa_validator import (
    WaValidationError,
    check_duplicate_in_bq,
    validate_payload,
)

log = logging.getLogger("fortunas.voice")


def _strip_to_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def _stock_code_from_product(product: str) -> str:
    code = re.sub(r"[^A-Za-z0-9]", "", product or "").upper()
    return (code or "VOICE")[:16]


# ───────────────────────── Invoice auto-increment ─────────────────────────


def _max_invoice_in_bq(tx_table: str) -> int:
    try:
        client = get_bigquery_client()
        rows = list(client.query(f"SELECT MAX(Invoice) AS mx FROM `{tx_table}`").result())
        return int(rows[0]["mx"] or 0)
    except Exception:  # noqa: BLE001
        return 0


def next_invoice_number(tx_table: str) -> int:
    """Nomor invoice berikutnya untuk tenant = MAX(Invoice) tabel tenant + 1.
    Streaming-insert rows tetap terlihat oleh SELECT, jadi MAX akurat."""
    return _max_invoice_in_bq(tx_table) + 1


# ───────────────────────── Customers master (per-tenant BQ) ─────────────────────────


def ensure_customers_table_bq(customers_table: str) -> None:
    client = get_bigquery_client()
    client.query(
        f"CREATE TABLE IF NOT EXISTS `{customers_table}` "
        "(CustomerID INT64, CustomerName STRING, created_at TIMESTAMP)"
    ).result()


def register_customer_in_bq(customer_id: int, name: str, customers_table: str) -> None:
    ensure_customers_table_bq(customers_table)
    client = get_bigquery_client()
    client.query(
        f"INSERT INTO `{customers_table}` (CustomerID, CustomerName, created_at) "
        "VALUES (@id, @name, CURRENT_TIMESTAMP())",
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("id", "INT64", int(customer_id)),
                bigquery.ScalarQueryParameter("name", "STRING", name),
            ]
        ),
    ).result()


def lookup_customer_id_by_name(name: str, customers_table: str) -> int | None:
    """Cari CustomerID dari nama (case-insensitive) di tabel customers tenant."""
    target = (name or "").strip()
    if not target:
        return None
    try:
        client = get_bigquery_client()
        rows = list(
            client.query(
                f"SELECT CustomerID FROM `{customers_table}` "
                "WHERE LOWER(CustomerName) = LOWER(@n) ORDER BY CustomerID LIMIT 1",
                job_config=bigquery.QueryJobConfig(
                    query_parameters=[bigquery.ScalarQueryParameter("n", "STRING", target)]
                ),
            ).result()
        )
        return int(rows[0]["CustomerID"]) if rows else None
    except Exception:  # noqa: BLE001
        return None


def _max_customer_id_in_master(customers_table: str) -> int:
    try:
        client = get_bigquery_client()
        rows = list(
            client.query(f"SELECT MAX(CustomerID) AS mx FROM `{customers_table}`").result()
        )
        return int(rows[0]["mx"] or 0)
    except Exception:  # noqa: BLE001
        return 0


def _max_customer_id_in_tx(tx_table: str) -> int:
    try:
        client = get_bigquery_client()
        rows = list(
            client.query(f"SELECT MAX(`Customer ID`) AS mx FROM `{tx_table}`").result()
        )
        return int(rows[0]["mx"] or 0)
    except Exception:  # noqa: BLE001
        return 0


def lookup_customer_names(customer_ids: list, customers_table: str) -> dict[str, str]:
    """Map {customer_id(str): CustomerName} dari tabel customers tenant."""
    int_ids = set()
    for cid in customer_ids:
        try:
            int_ids.add(int(float(cid)))
        except (TypeError, ValueError):
            continue
    if not int_ids:
        return {}
    try:
        client = get_bigquery_client()
        in_clause = ",".join(str(i) for i in sorted(int_ids))
        rows = client.query(
            f"SELECT CustomerID, CustomerName FROM `{customers_table}` "
            f"WHERE CustomerID IN ({in_clause})"
        ).result()
        out: dict[str, str] = {}
        for r in rows:
            nm = (r["CustomerName"] or "").strip()
            if nm:
                out[str(int(r["CustomerID"]))] = nm
        return out
    except Exception:  # noqa: BLE001
        return {}


def resolve_customer_id(name: str, customers_table: str, tx_table: str) -> int | None:
    """Nama pelanggan → Customer ID numerik (auto-assign + reuse) untuk tenant."""
    name = (name or "").strip()
    if not name:
        return None
    if name.isdigit():
        return int(name)

    existing = lookup_customer_id_by_name(name, customers_table)
    if existing is not None:
        return existing

    new_id = max(_max_customer_id_in_master(customers_table), _max_customer_id_in_tx(tx_table), 0) + 1
    try:
        register_customer_in_bq(new_id, name, customers_table)
    except Exception:  # noqa: BLE001
        pass  # gagal daftar master tidak boleh menggagalkan transaksi
    return new_id


# ───────────────────────── Transaction insert ─────────────────────────


def to_wa_payload(structured: dict[str, Any]) -> dict[str, str]:
    invoice_digits = _strip_to_digits(str(structured.get("invoice", "")))
    if not invoice_digits:
        raise WaValidationError("Invoice harus berisi angka.")
    return {
        "Invoice": invoice_digits,
        "StockCode": str(structured.get("stock_code") or _stock_code_from_product(structured.get("product", ""))),
        "Description": str(structured.get("product") or ""),
        "Quantity": str(structured.get("qty", "")),
        "InvoiceDate": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "Price": str(structured.get("unit_price", "")),
        "Customer ID": str(structured.get("customer", "") or "").strip(),
        "Country": str(structured.get("country") or "Indonesia"),
    }


def process_structured_transaction(
    structured: dict[str, Any], tenant: TenantContext, sender: str = "voice_user"
) -> dict[str, Any]:
    """Voice/structured entry, tenant-aware, langsung ke BigQuery (tanpa Sheets)."""
    tx_table = tenant.table("transactions")
    customers_table = tenant.table("customers")

    # Invoice auto-increment kalau tidak disebut.
    if not str(structured.get("invoice") or "").strip():
        structured = {**structured, "invoice": str(next_invoice_number(tx_table))}

    # Nama pelanggan → Customer ID numerik (auto-assign + reuse).
    customer_name = str(structured.get("customer") or "").strip()
    customer_id = resolve_customer_id(customer_name, customers_table, tx_table)
    structured = {**structured, "customer": "" if customer_id is None else str(customer_id)}

    try:
        raw = to_wa_payload(structured)
        payload = validate_payload(raw)
    except WaValidationError as exc:
        return {"ok": False, "status": "validation_error", "reply": f"❌ {exc}", "payload": None}

    if check_duplicate_in_bq(payload["Invoice"], payload["StockCode"], tx_table):
        return {
            "ok": False,
            "status": "duplicate",
            "reply": (
                f"⚠ Invoice {payload['Invoice']} ({payload['StockCode']}) sudah ada. "
                "Transaksi tidak ditambahkan dua kali."
            ),
            "payload": payload,
        }

    inserted, errors = _insert_in_batches([payload], table_ref=tx_table)
    if inserted <= 0 or errors:
        return {
            "ok": False,
            "status": "bq_error",
            "reply": f"⚠ Gagal simpan ke BigQuery: {'; '.join(errors[:3]) or 'unknown error'}",
            "payload": payload,
        }

    cust_info = (
        f" Pelanggan {customer_name} (ID {customer_id})."
        if customer_name and customer_id is not None
        else ""
    )
    return {
        "ok": True,
        "status": "success",
        "reply": (
            f"✅ Transaksi {payload['Invoice']} ({payload['Description']}) berhasil dicatat.{cust_info}"
        ),
        "payload": payload,
    }
