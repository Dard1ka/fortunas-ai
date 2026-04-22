"""Parser pesan WhatsApp → dict transaksi.

Mendukung 2 format:

1. CSV inline (1 baris, 8 kolom dipisah koma):
   489436,35004B,SET OF 3 BLACK FLYING DUCKS,12,2009-12-01 09:06:00,4.65,13078.0,United Kingdom

2. Key:Value multiline (case-insensitive key, spasi bebas):
   Invoice : 489438
   StockCode : 21329
   Description : DINOSAURS WRITING SET
   Quantity : 28
   InvoiceDate : 2009-12-01 09:24:00
   Price : 0.98
   Customer ID : 18102.0
   Country : United Kingdom

Output: dict dengan key EXACT sesuai schema BigQuery (Invoice, StockCode,
Description, Quantity, InvoiceDate, Price, Customer ID, Country). Nilai masih
string mentah — validasi tipe terjadi di wa_validator.
"""
from __future__ import annotations

import csv
import io
import re

REQUIRED_COLUMNS: list[str] = [
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer ID",
    "Country",
]

# Alias key (lowercase tanpa spasi) → nama kolom canonical
_KEY_ALIASES: dict[str, str] = {
    "invoice": "Invoice",
    "invoiceno": "Invoice",
    "noinvoice": "Invoice",
    "stockcode": "StockCode",
    "kodebarang": "StockCode",
    "sku": "StockCode",
    "description": "Description",
    "deskripsi": "Description",
    "produk": "Description",
    "namaproduk": "Description",
    "quantity": "Quantity",
    "qty": "Quantity",
    "jumlah": "Quantity",
    "invoicedate": "InvoiceDate",
    "tanggal": "InvoiceDate",
    "waktu": "InvoiceDate",
    "date": "InvoiceDate",
    "price": "Price",
    "harga": "Price",
    "customerid": "Customer ID",
    "customer": "Customer ID",
    "idpelanggan": "Customer ID",
    "pelanggan": "Customer ID",
    "country": "Country",
    "negara": "Country",
}


class WaParseError(ValueError):
    """Pesan WA tidak bisa di-parse ke struktur transaksi."""


def _normalize_key(raw: str) -> str | None:
    key = re.sub(r"[\s_\-]+", "", raw.strip().lower())
    return _KEY_ALIASES.get(key)


def _parse_csv_line(line: str) -> dict[str, str]:
    """Parse satu baris CSV pakai `csv` module (handle quoted fields dengan koma)."""
    reader = csv.reader(io.StringIO(line.strip()))
    try:
        row = next(reader)
    except StopIteration as exc:
        raise WaParseError("Pesan kosong.") from exc

    if len(row) != len(REQUIRED_COLUMNS):
        raise WaParseError(
            f"Format CSV harus punya {len(REQUIRED_COLUMNS)} kolom dipisah koma, "
            f"tapi ditemukan {len(row)}. Urutan: {', '.join(REQUIRED_COLUMNS)}."
        )

    return {col: row[i].strip() for i, col in enumerate(REQUIRED_COLUMNS)}


def _parse_key_value(text: str) -> dict[str, str]:
    """Parse pesan multiline Key:Value. Tiap baris bentuk `Key : Value`."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    parsed: dict[str, str] = {}
    unknown_keys: list[str] = []

    for ln in lines:
        if ":" not in ln:
            continue
        raw_key, _, raw_val = ln.partition(":")
        canonical = _normalize_key(raw_key)
        if canonical is None:
            unknown_keys.append(raw_key.strip())
            continue
        parsed[canonical] = raw_val.strip()

    missing = [c for c in REQUIRED_COLUMNS if c not in parsed]
    if missing:
        hint = ""
        if unknown_keys:
            hint = f" Key tidak dikenal: {', '.join(unknown_keys[:5])}."
        raise WaParseError(
            f"Kolom wajib belum lengkap: {', '.join(missing)}.{hint} "
            f"Urutan wajib: {', '.join(REQUIRED_COLUMNS)}."
        )

    return parsed


def detect_format(text: str) -> str:
    """Tebak format pesan: 'csv' | 'kv' | 'unknown'."""
    stripped = text.strip()
    if not stripped:
        return "unknown"

    # Kalau ada minimal 3 baris dan ≥1 pakai ':', asumsikan Key:Value
    lines = [ln for ln in stripped.splitlines() if ln.strip()]
    if len(lines) >= 3 and sum(1 for ln in lines if ":" in ln) >= 3:
        return "kv"

    # Kalau 1 baris dengan 7 koma (= 8 kolom), asumsikan CSV
    first_line = lines[0]
    if first_line.count(",") >= len(REQUIRED_COLUMNS) - 1:
        return "csv"

    return "unknown"


def parse_wa_message(text: str) -> dict[str, str]:
    """Entry point. Deteksi format dan parse ke dict.

    Raise WaParseError dengan pesan yang ramah user kalau gagal.
    """
    if not text or not text.strip():
        raise WaParseError("Pesan kosong. Kirim data transaksi dengan 8 kolom.")

    fmt = detect_format(text)
    if fmt == "csv":
        return _parse_csv_line(text.strip().splitlines()[0])
    if fmt == "kv":
        return _parse_key_value(text)

    raise WaParseError(
        "Format tidak dikenali. Kirim salah satu:\n"
        "1) CSV 1 baris: Invoice,StockCode,Description,Quantity,InvoiceDate,Price,Customer ID,Country\n"
        "2) Multiline Key:Value — satu kolom per baris (contoh: `Invoice : 489438`)."
    )
