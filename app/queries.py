"""Named analytics SQL — sekarang tenant-aware.

Tiap query dibangun dari FUNGSI yang menerima `tx` = ref tabel transaksi
(tanpa backtick), mis. `project.dataset.tokoA_transactions`. Multi-tenant:
caller kirim tabel milik tenant. Backward-compat: NAMED_QUERIES/QUERY_MAP tetap
ada (pakai tabel default dari .env) untuk kode lama / single-tenant.
"""
import os

from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID", "fortunasai")
DATASET = os.getenv("BIGQUERY_DATASET", "fortunas_ai")
TABLE = os.getenv("BIGQUERY_TABLE", "online_retail")

# Ref tabel default (.env) untuk backward-compat (single-tenant / sql_agent).
_ENV_TX = f"{PROJECT_ID}.{DATASET}.{TABLE}"

# Schema tabel transaksi (sama untuk tiap tenant):
#   Invoice INT, StockCode STR, Description STR, Quantity INT,
#   InvoiceDate TIMESTAMP, Price FLOAT, `Customer ID` FLOAT, Country STR


def _high_value_customer_sql(tx: str) -> str:
    return f"""
WITH customer_summary AS (
  SELECT
    CAST(`Customer ID` AS STRING) AS customer_id,
    COUNT(DISTINCT Invoice) AS total_orders,
    ROUND(SUM(Quantity * Price), 2) AS total_spent,
    ROUND(SUM(Quantity * Price) / NULLIF(COUNT(DISTINCT Invoice), 0), 2) AS avg_order_value
  FROM `{tx}`
  WHERE `Customer ID` IS NOT NULL AND Quantity > 0 AND Price > 0
  GROUP BY CAST(`Customer ID` AS STRING)
),
product_summary AS (
  SELECT
    CAST(`Customer ID` AS STRING) AS customer_id,
    Description AS description,
    SUM(Quantity) AS total_qty
  FROM `{tx}`
  WHERE `Customer ID` IS NOT NULL AND Description IS NOT NULL
    AND Quantity > 0 AND Price > 0
  GROUP BY CAST(`Customer ID` AS STRING), Description
),
product_ranked AS (
  SELECT customer_id, description, total_qty,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY total_qty DESC, description) AS rn
  FROM product_summary
),
top_products AS (
  SELECT customer_id,
    STRING_AGG(CONCAT(description, ' (', CAST(total_qty AS STRING), ')'), ', '
               ORDER BY total_qty DESC, description) AS top_products
  FROM product_ranked WHERE rn <= 5 GROUP BY customer_id
)
SELECT cs.customer_id, cs.total_orders, cs.total_spent, cs.avg_order_value, tp.top_products
FROM customer_summary cs
LEFT JOIN top_products tp ON cs.customer_id = tp.customer_id
ORDER BY cs.total_spent DESC
LIMIT 10
"""


def _repeat_customer_sql(tx: str) -> str:
    return f"""
WITH customer_summary AS (
  SELECT
    CAST(`Customer ID` AS STRING) AS customer_id,
    COUNT(DISTINCT Invoice) AS total_orders,
    ROUND(SUM(Quantity * Price), 2) AS total_spent
  FROM `{tx}`
  WHERE `Customer ID` IS NOT NULL AND Quantity > 0 AND Price > 0
  GROUP BY CAST(`Customer ID` AS STRING)
  HAVING COUNT(DISTINCT Invoice) > 1
),
product_summary AS (
  SELECT
    CAST(`Customer ID` AS STRING) AS customer_id,
    Description AS description,
    SUM(Quantity) AS total_qty
  FROM `{tx}`
  WHERE `Customer ID` IS NOT NULL AND Description IS NOT NULL
    AND Quantity > 0 AND Price > 0
  GROUP BY CAST(`Customer ID` AS STRING), Description
),
product_ranked AS (
  SELECT customer_id, description, total_qty,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY total_qty DESC, description) AS rn
  FROM product_summary
),
top_products AS (
  SELECT customer_id,
    STRING_AGG(CONCAT(description, ' (', CAST(total_qty AS STRING), ')'), ', '
               ORDER BY total_qty DESC, description) AS top_products
  FROM product_ranked WHERE rn <= 5 GROUP BY customer_id
)
SELECT cs.customer_id, cs.total_orders, cs.total_spent, tp.top_products
FROM customer_summary cs
LEFT JOIN top_products tp ON cs.customer_id = tp.customer_id
ORDER BY cs.total_orders DESC, cs.total_spent DESC
LIMIT 10
"""


def _peak_hour_sql(tx: str) -> str:
    return f"""
WITH hour_summary AS (
  SELECT EXTRACT(HOUR FROM InvoiceDate) AS purchase_hour,
         COUNT(DISTINCT Invoice) AS total_orders
  FROM `{tx}`
  WHERE Quantity > 0 AND Price > 0
  GROUP BY purchase_hour
),
product_summary AS (
  SELECT EXTRACT(HOUR FROM InvoiceDate) AS purchase_hour,
         Description AS description, SUM(Quantity) AS total_qty
  FROM `{tx}`
  WHERE Description IS NOT NULL AND Quantity > 0 AND Price > 0
  GROUP BY purchase_hour, Description
),
product_ranked AS (
  SELECT purchase_hour, description, total_qty,
    ROW_NUMBER() OVER (PARTITION BY purchase_hour ORDER BY total_qty DESC, description) AS rn
  FROM product_summary
),
top_products AS (
  SELECT purchase_hour,
    STRING_AGG(CONCAT(description, ' (', CAST(total_qty AS STRING), ')'), ', '
               ORDER BY total_qty DESC, description) AS top_products
  FROM product_ranked WHERE rn <= 5 GROUP BY purchase_hour
)
SELECT hs.purchase_hour, hs.total_orders, tp.top_products
FROM hour_summary hs
LEFT JOIN top_products tp ON hs.purchase_hour = tp.purchase_hour
ORDER BY hs.total_orders DESC
LIMIT 10
"""


def _bundle_opportunity_sql(tx: str) -> str:
    return f"""
WITH clean_lines AS (
  SELECT Invoice AS invoice, Description AS description
  FROM `{tx}`
  WHERE Description IS NOT NULL
    AND Quantity > 0
    AND Price > 0
)
SELECT
  a.description AS product_A,
  b.description AS product_B,
  COUNT(DISTINCT a.invoice) AS bundle_frequency
FROM clean_lines a
JOIN clean_lines b
  ON a.invoice = b.invoice
 AND a.description < b.description
GROUP BY product_A, product_B
ORDER BY bundle_frequency DESC
LIMIT 10
"""


def _top_product_sql(tx: str) -> str:
    return f"""
SELECT
  Description AS description,
  SUM(Quantity) AS total_qty,
  ROUND(SUM(Quantity * Price), 2) AS total_omzet
FROM `{tx}`
WHERE Description IS NOT NULL AND Quantity > 0 AND Price > 0
GROUP BY Description
ORDER BY total_omzet DESC, total_qty DESC, description
LIMIT 10
"""


# Builder per analisis (terima ref tabel transaksi tenant).
QUERY_BUILDERS = {
    "high_value_customer": _high_value_customer_sql,
    "repeat_customer": _repeat_customer_sql,
    "peak_hour": _peak_hour_sql,
    "bundle_opportunity": _bundle_opportunity_sql,
    "top_product": _top_product_sql,
}

_COST_TIER = {
    "high_value_customer": "cheap",
    "repeat_customer": "cheap",
    "peak_hour": "cheap",
    "bundle_opportunity": "expensive",
    "top_product": "cheap",
}


def build_query(analysis_key: str, tx_table: str) -> str | None:
    """SQL untuk analisis pada tabel transaksi tenant (tx_table tanpa backtick)."""
    builder = QUERY_BUILDERS.get(analysis_key)
    return builder(tx_table) if builder else None


# ---------- Backward-compat (single-tenant / sql_agent): pakai tabel .env ----------
NAMED_QUERIES = {
    key: {"sql": builder(_ENV_TX), "cost_tier": _COST_TIER.get(key, "unknown")}
    for key, builder in QUERY_BUILDERS.items()
}
QUERY_MAP = {key: meta["sql"] for key, meta in NAMED_QUERIES.items()}
