import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID", "fortunasai")
DATASET = os.getenv("BIGQUERY_DATASET", "fortunas_ai")
TABLE = os.getenv("BIGQUERY_TABLE", "online_retail")

FULL_TABLE = f"`{PROJECT_ID}.{DATASET}.{TABLE}`"

# ─────────────────────────────────────────────────────────────────────────
# Schema BigQuery (aktual):
#   Invoice (INTEGER)      StockCode (STRING)    Description (STRING)
#   Quantity (INTEGER)     InvoiceDate (TIMESTAMP)  Price (FLOAT)
#   `Customer ID` (FLOAT, pakai backtick karena ada spasi)  Country (STRING)
#
# Alias output query tetap snake_case (customer_id, invoice_date, dst.)
# supaya llm_service.py & prompt_builder.py tidak perlu diubah.
# ─────────────────────────────────────────────────────────────────────────


# ---------- SQL definitions ----------
_HIGH_VALUE_CUSTOMER_SQL = f"""
WITH customer_summary AS (
  SELECT
    CAST(`Customer ID` AS STRING) AS customer_id,
    COUNT(DISTINCT Invoice) AS total_orders,
    ROUND(SUM(Quantity * Price), 2) AS total_spent,
    -- AOV yang benar: total_spent dibagi jumlah invoice unik, BUKAN rata-rata per line item
    ROUND(SUM(Quantity * Price) / NULLIF(COUNT(DISTINCT Invoice), 0), 2) AS avg_order_value
  FROM {FULL_TABLE}
  WHERE `Customer ID` IS NOT NULL AND Quantity > 0 AND Price > 0
  GROUP BY CAST(`Customer ID` AS STRING)
),
product_summary AS (
  SELECT
    CAST(`Customer ID` AS STRING) AS customer_id,
    Description AS description,
    SUM(Quantity) AS total_qty
  FROM {FULL_TABLE}
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

_REPEAT_CUSTOMER_SQL = f"""
WITH customer_summary AS (
  SELECT
    CAST(`Customer ID` AS STRING) AS customer_id,
    COUNT(DISTINCT Invoice) AS total_orders,
    ROUND(SUM(Quantity * Price), 2) AS total_spent
  FROM {FULL_TABLE}
  WHERE `Customer ID` IS NOT NULL AND Quantity > 0 AND Price > 0
  GROUP BY CAST(`Customer ID` AS STRING)
  HAVING COUNT(DISTINCT Invoice) > 1
),
product_summary AS (
  SELECT
    CAST(`Customer ID` AS STRING) AS customer_id,
    Description AS description,
    SUM(Quantity) AS total_qty
  FROM {FULL_TABLE}
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

_PEAK_HOUR_SQL = f"""
WITH hour_summary AS (
  SELECT EXTRACT(HOUR FROM InvoiceDate) AS purchase_hour,
         COUNT(DISTINCT Invoice) AS total_orders
  FROM {FULL_TABLE}
  WHERE Quantity > 0 AND Price > 0
  GROUP BY purchase_hour
),
product_summary AS (
  SELECT EXTRACT(HOUR FROM InvoiceDate) AS purchase_hour,
         Description AS description, SUM(Quantity) AS total_qty
  FROM {FULL_TABLE}
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

# OPTIMISASI bundle_opportunity:
# - Pre-filter di CTE supaya self-join scan jauh lebih kecil
# - Quantity > 0 dan Price > 0 di kedua sisi
# - Description IS NOT NULL di CTE, bukan di JOIN
_BUNDLE_OPPORTUNITY_SQL = f"""
WITH clean_lines AS (
  SELECT Invoice AS invoice, Description AS description
  FROM {FULL_TABLE}
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


# ---------- Named query registry dengan metadata ----------
NAMED_QUERIES = {
    "high_value_customer": {
        "sql": _HIGH_VALUE_CUSTOMER_SQL,
        "cost_tier": "cheap",
        "estimated_gb": 0.05,
    },
    "repeat_customer": {
        "sql": _REPEAT_CUSTOMER_SQL,
        "cost_tier": "cheap",
        "estimated_gb": 0.05,
    },
    "peak_hour": {
        "sql": _PEAK_HOUR_SQL,
        "cost_tier": "cheap",
        "estimated_gb": 0.03,
    },
    "bundle_opportunity": {
        "sql": _BUNDLE_OPPORTUNITY_SQL,
        "cost_tier": "expensive",  # self-join
        "estimated_gb": 0.5,
    },
}


# ---------- Backward compat: main.py masih import QUERY_MAP ----------
QUERY_MAP = {key: meta["sql"] for key, meta in NAMED_QUERIES.items()}
