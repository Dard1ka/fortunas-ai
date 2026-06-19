"""Sinkronkan Customer ID dari Google Sheet ke BigQuery untuk baris yang masih null.

Idempotent & aman dijalankan berkali-kali — hanya meng-update baris BQ yang
`Customer ID`-nya NULL, memakai nilai dari Sheet (kolom Customer ID per Invoice).

Kegunaan utama: melengkapi backfill ketika UPDATE BigQuery sebelumnya gagal
karena baris masih di streaming buffer (~90 menit sejak insert).

Jalankan dari root project:
    .\.venv\Scripts\python.exe scripts\backfill_bq_customer_id.py
"""
import os
import sys
from datetime import datetime, timezone

# Pastikan root project ada di path saat dijalankan dari folder scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

import gspread
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

from app.bigquery_service import get_bigquery_client

print("Sekarang UTC:", datetime.now(timezone.utc).isoformat(timespec="seconds"))

# --- Peta Invoice -> Customer ID dari Sheet ---
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), scopes=scopes)
gc = gspread.authorize(creds)
ws = gc.open_by_key(os.getenv("GOOGLE_SHEETS_ID")).worksheet(os.getenv("GOOGLE_SHEETS_TAB", "wa_transactions"))
vals = ws.get_all_values()
hdr = vals[0]
inv_i = hdr.index("Invoice")
cid_i = hdr.index("Customer ID")

invoice_to_cid: dict[int, int] = {}
for row in vals[1:]:
    inv = (row[inv_i] if inv_i < len(row) else "").strip()
    cid = (row[cid_i] if cid_i < len(row) else "").strip()
    if inv and cid:
        try:
            invoice_to_cid[int(inv)] = int(float(cid))
        except (ValueError, TypeError):
            continue

# --- Baris BQ yang Customer ID-nya masih NULL ---
proj = os.getenv("BIGQUERY_PROJECT_ID"); ds = os.getenv("BIGQUERY_DATASET"); tbl = os.getenv("BIGQUERY_TABLE")
client = get_bigquery_client()
full = f"`{proj}.{ds}.{tbl}`"

null_rows = list(client.query(
    f"SELECT DISTINCT Invoice FROM {full} WHERE `Customer ID` IS NULL"
).result())
null_invoices = {int(r["Invoice"]) for r in null_rows if r["Invoice"] is not None}

todo = {inv: cid for inv, cid in invoice_to_cid.items() if inv in null_invoices}
if not todo:
    print("Tidak ada yang perlu di-backfill (semua sudah sinkron).")
    raise SystemExit(0)

print(f"Akan backfill {len(todo)} invoice:", todo)
ok, fail = 0, 0
for inv, cid in todo.items():
    try:
        job = client.query(
            f"UPDATE {full} SET `Customer ID` = @cid WHERE Invoice = @inv AND `Customer ID` IS NULL",
            job_config=bigquery.QueryJobConfig(query_parameters=[
                bigquery.ScalarQueryParameter("cid", "FLOAT64", float(cid)),
                bigquery.ScalarQueryParameter("inv", "INT64", int(inv)),
            ]),
        )
        job.result()
        print(f"  Invoice {inv} -> Customer ID {cid}: {job.num_dml_affected_rows} baris OK")
        ok += 1
    except Exception as e:  # noqa: BLE001
        print(f"  Invoice {inv}: GAGAL (streaming buffer?) — {type(e).__name__}: {str(e)[:100]}")
        fail += 1

print(f"\nSelesai. Berhasil: {ok}, gagal: {fail}")
if fail:
    print("Baris yang gagal masih di streaming buffer. Jalankan lagi script ini nanti (~1 jam sejak insert).")
