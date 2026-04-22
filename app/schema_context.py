SCHEMA_CONTEXT = """
Table: online_retail
Description: Transaksi e-commerce retail UK (UCI Online Retail dataset).

Columns (EXACT names — perhatikan CamelCase & spasi):
- Invoice (INTEGER)         — nomor invoice transaksi
- StockCode (STRING)        — kode produk unik
- Description (STRING)      — nama produk (bisa NULL)
- Quantity (INTEGER)        — jumlah unit (bisa negatif untuk return; filter > 0)
- InvoiceDate (TIMESTAMP)   — waktu transaksi
- Price (FLOAT)             — harga per unit (filter > 0)
- `Customer ID` (FLOAT)     — id pelanggan (bisa NULL untuk guest) — WAJIB pakai backtick karena ada spasi
- Country (STRING)          — negara asal pelanggan

Aturan query yang harus diikuti:
- Nama kolom CASE-SENSITIVE. Contoh: `InvoiceDate`, bukan `invoice_date`.
- `Customer ID` harus ditulis dengan backtick: `Customer ID` (bukan customer_id atau Customer_ID).
- Selalu filter Quantity > 0 dan Price > 0 untuk exclude return & data noise.
- `Customer ID` bisa NULL — handle eksplisit dengan `Customer ID IS NOT NULL`.
- Gunakan CAST(`Customer ID` AS STRING) saat group by customer.
- WAJIB pakai LIMIT (max 1000).
- Hanya boleh SELECT, dilarang INSERT/UPDATE/DELETE/DDL.

Contoh snippet yang BENAR:
  SELECT CAST(`Customer ID` AS STRING) AS customer_id,
         COUNT(DISTINCT Invoice) AS total_orders
  FROM `project.dataset.online_retail`
  WHERE `Customer ID` IS NOT NULL AND Quantity > 0 AND Price > 0
  GROUP BY CAST(`Customer ID` AS STRING)
  LIMIT 10
"""


def get_schema_context() -> str:
    return SCHEMA_CONTEXT
