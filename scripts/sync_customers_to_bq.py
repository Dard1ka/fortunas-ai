"""Buat tabel dimensi `customers` di BigQuery + sinkron dari Google Sheet.

Idempotent: hanya menambah CustomerID yang belum ada di BQ. Aman dijalankan ulang.

Jalankan dari root project:
    .\.venv\Scripts\python.exe scripts\sync_customers_to_bq.py
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

import gspread
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

from app.bigquery_service import get_bigquery_client
from app.services.wa_pipeline_structured import _customers_bq_ref, ensure_customers_table_bq

# 1. Pastikan tabel ada
ensure_customers_table_bq()
ref = _customers_bq_ref()
print("Tabel BigQuery siap:", ref)

client = get_bigquery_client()

# 2. CustomerID yang sudah ada di BQ
existing = {int(r["CustomerID"]) for r in client.query(f"SELECT CustomerID FROM `{ref}`").result() if r["CustomerID"] is not None}
print("Sudah ada di BQ:", sorted(existing) or "(kosong)")

# 3. Baca master dari Google Sheet
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), scopes=scopes)
gc = gspread.authorize(creds)
tab = os.getenv("GOOGLE_SHEETS_CUSTOMERS_TAB", "customers")
rows = gc.open_by_key(os.getenv("GOOGLE_SHEETS_ID")).worksheet(tab).get_all_values()
hdr = rows[0]
id_i = hdr.index("CustomerID")
name_i = hdr.index("CustomerName")

to_insert = []
for row in rows[1:]:
    try:
        cid = int(float(row[id_i]))
    except (ValueError, IndexError, TypeError):
        continue
    name = row[name_i] if name_i < len(row) else ""
    if cid not in existing:
        to_insert.append({"CustomerID": cid, "CustomerName": name,
                          "created_at": datetime.now(timezone.utc).isoformat()})

if not to_insert:
    print("Tidak ada yang perlu disinkron (BQ sudah up-to-date).")
else:
    errors = client.insert_rows_json(ref, to_insert)
    if errors:
        print("GAGAL insert:", errors)
    else:
        print(f"Disinkron {len(to_insert)} pelanggan ke BQ:", [r["CustomerID"] for r in to_insert])

# 4. Tampilkan isi tabel
print("\nIsi tabel customers di BigQuery:")
for r in client.query(f"SELECT CustomerID, CustomerName FROM `{ref}` ORDER BY CustomerID").result():
    print(f"  {r['CustomerID']} | {r['CustomerName']}")
