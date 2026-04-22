"""Excel → BigQuery upload pipeline.

Target schema (table: online_retail):
  Invoice       INTEGER    NULLABLE
  StockCode     STRING     NULLABLE
  Description   STRING     NULLABLE
  Quantity      INTEGER    NULLABLE
  InvoiceDate   TIMESTAMP  NULLABLE
  Price         FLOAT      NULLABLE
  Customer ID   FLOAT      NULLABLE
  Country       STRING     NULLABLE
"""
from __future__ import annotations

import io
import math
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from google.api_core import exceptions as gcp_exceptions

from app.bigquery_service import get_bigquery_client
from app.core.config import get_settings

# Excel header = BigQuery column name (match persis dengan schema BQ)
COLUMN_MAP: dict[str, str] = {
    "Invoice": "Invoice",
    "StockCode": "StockCode",
    "Description": "Description",
    "Quantity": "Quantity",
    "InvoiceDate": "InvoiceDate",
    "Price": "Price",
    "Customer ID": "Customer ID",
    "Country": "Country",
}

REQUIRED_COLUMNS: list[str] = list(COLUMN_MAP.keys())

ALLOWED_EXTENSIONS: set[str] = {".xlsx", ".xls", ".csv"}

MAX_ROWS_PER_UPLOAD = 50_000
BQ_INSERT_BATCH = 500


class ExcelValidationError(ValueError):
    """Raised when uploaded Excel fails structural validation."""


def _parse_excel_bytes(content: bytes, filename: str) -> pd.DataFrame:
    suffix = filename.lower().rsplit(".", 1)[-1]
    try:
        if suffix == "csv":
            return pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False)
        return pd.read_excel(io.BytesIO(content), dtype=str, engine="openpyxl")
    except Exception as exc:  # noqa: BLE001 — surface original message
        raise ExcelValidationError(f"Gagal membaca file: {exc}") from exc


def _validate_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ExcelValidationError(
            f"Kolom wajib tidak ditemukan: {', '.join(missing)}. "
            f"Pastikan header sesuai: {', '.join(REQUIRED_COLUMNS)}."
        )


def _parse_invoice_date(raw: Any) -> datetime | None:
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return None
    text = str(raw).strip()
    if not text:
        return None
    # Format utama dari sumber data: "01/12/2009 07:45" (dd/mm/yyyy HH:MM)
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    # Fallback ke parser pandas
    try:
        dt = pd.to_datetime(text, dayfirst=True, errors="raise").to_pydatetime()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:  # noqa: BLE001
        return None


def _coerce_int(raw: Any) -> int | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if text == "" or text.lower() == "nan":
        return None
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _coerce_float(raw: Any) -> float | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if text == "" or text.lower() == "nan":
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _clean_str(raw: Any) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    return text if text and text.lower() != "nan" else None


def _row_to_bq(idx: int, row: pd.Series) -> tuple[dict | None, str | None]:
    """Return (row_dict, error_message). row_dict is None jika row invalid.

    Validasi tipe mengikuti schema BigQuery:
      Invoice (INTEGER), StockCode (STRING), Description (STRING),
      Quantity (INTEGER), InvoiceDate (TIMESTAMP), Price (FLOAT),
      Customer ID (FLOAT), Country (STRING) — semuanya NULLABLE di BQ.

    Namun agar data analitik bermakna, kita tetap minta:
    Invoice, StockCode, Quantity, Price, InvoiceDate wajib terisi & valid.
    """
    invoice = _coerce_int(row.get("Invoice"))
    stock = _clean_str(row.get("StockCode"))
    qty = _coerce_int(row.get("Quantity"))
    price = _coerce_float(row.get("Price"))
    dt = _parse_invoice_date(row.get("InvoiceDate"))

    if invoice is None:
        return None, f"Baris {idx + 2}: Invoice harus angka (INTEGER) & tidak boleh kosong"
    if not stock:
        return None, f"Baris {idx + 2}: StockCode kosong"
    if qty is None:
        return None, f"Baris {idx + 2}: Quantity bukan INTEGER valid"
    if price is None:
        return None, f"Baris {idx + 2}: Price bukan FLOAT valid"
    if dt is None:
        return None, f"Baris {idx + 2}: InvoiceDate tidak bisa di-parse (format: dd/mm/yyyy HH:MM)"

    return (
        {
            "Invoice": invoice,
            "StockCode": stock,
            "Description": _clean_str(row.get("Description")),
            "Quantity": qty,
            "InvoiceDate": dt.isoformat(),
            "Price": price,
            "Customer ID": _coerce_float(row.get("Customer ID")),
            "Country": _clean_str(row.get("Country")),
        },
        None,
    )


def validate_excel(content: bytes, filename: str) -> dict:
    """Parse + validate WITHOUT inserting ke BigQuery. Untuk preview endpoint."""
    df = _parse_excel_bytes(content, filename)
    _validate_columns(df)

    if len(df) > MAX_ROWS_PER_UPLOAD:
        raise ExcelValidationError(
            f"File terlalu besar: {len(df)} baris. Maksimum {MAX_ROWS_PER_UPLOAD:,} baris per upload."
        )

    valid_rows: list[dict] = []
    errors: list[str] = []
    for idx, row in df.iterrows():
        parsed, err = _row_to_bq(idx, row)
        if err:
            errors.append(err)
        elif parsed:
            valid_rows.append(parsed)

    return {
        "total_rows": int(len(df)),
        "valid_rows": len(valid_rows),
        "invalid_rows": len(errors),
        "errors": errors[:20],  # cap preview
        "sample": valid_rows[:3],
        "_rows": valid_rows,
    }


def _insert_in_batches(rows: list[dict]) -> tuple[int, list[str]]:
    settings = get_settings()
    client = get_bigquery_client()
    table_ref = f"{settings.bigquery_project_id}.{settings.bigquery_dataset}.{settings.bigquery_table}"

    inserted = 0
    errors: list[str] = []
    for i in range(0, len(rows), BQ_INSERT_BATCH):
        chunk = rows[i : i + BQ_INSERT_BATCH]
        try:
            result = client.insert_rows_json(table_ref, chunk)
        except gcp_exceptions.NotFound as exc:
            raise RuntimeError(f"Table {table_ref} tidak ditemukan: {exc}") from exc
        except gcp_exceptions.Forbidden as exc:
            raise PermissionError(
                f"Service account tidak punya izin tulis ke {table_ref}. "
                f"Solusi: grant role 'BigQuery Data Editor' via GCP Console → IAM, "
                f"atau jalankan:\n"
                f"  gcloud projects add-iam-policy-binding {get_settings().bigquery_project_id} "
                f"--member=serviceAccount:<email> --role=roles/bigquery.dataEditor\n"
                f"Detail error asli: {exc}"
            ) from exc
        except gcp_exceptions.GoogleAPIError as exc:
            raise RuntimeError(f"BigQuery error saat insert batch {i}: {exc}") from exc

        if result:
            for err in result:
                errors.append(f"Row {i + err.get('index', 0)}: {err.get('errors')}")
        else:
            inserted += len(chunk)

    return inserted, errors


def upload_excel(content: bytes, filename: str) -> dict:
    """End-to-end: parse → validate → insert ke BigQuery."""
    preview = validate_excel(content, filename)
    rows = preview.pop("_rows")

    if not rows:
        return {
            "status": "failed",
            "message": "Tidak ada baris valid yang bisa di-upload.",
            "inserted_rows": 0,
            "total_rows": preview["total_rows"],
            "invalid_rows": preview["invalid_rows"],
            "errors": preview["errors"],
            "table": f"{get_settings().bigquery_dataset}.{get_settings().bigquery_table}",
        }

    inserted, insert_errors = _insert_in_batches(rows)
    status = "success" if inserted == len(rows) and not insert_errors else "partial_success"
    return {
        "status": status,
        "message": (
            f"Berhasil upload {inserted} baris ke BigQuery."
            if status == "success"
            else f"Upload sebagian: {inserted}/{len(rows)} baris masuk."
        ),
        "inserted_rows": inserted,
        "total_rows": preview["total_rows"],
        "valid_rows": preview["valid_rows"],
        "invalid_rows": preview["invalid_rows"],
        "errors": (preview["errors"] + insert_errors)[:20],
        "table": f"{get_settings().bigquery_dataset}.{get_settings().bigquery_table}",
    }
