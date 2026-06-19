"""Provisioning tabel BigQuery per tenant (dipanggil saat register).

Tiap tenant dapat 2 tabel di dataset bersama:
  {prefix}_transactions  (skema sama dengan online_retail)
  {prefix}_customers      (peta CustomerID ↔ CustomerName)

Idempotent (CREATE TABLE IF NOT EXISTS). prefix sudah divalidasi aman di db.py
(huruf kecil/angka/underscore), jadi aman di-interpolasi ke DDL.
"""
from __future__ import annotations

from app.bigquery_service import get_bigquery_client
from app.core.config import get_settings


def provision_tenant_tables(prefix: str) -> dict[str, str]:
    s = get_settings()
    dataset = f"{s.bigquery_project_id}.{s.bigquery_dataset}"
    tx = f"{dataset}.{prefix}_transactions"
    customers = f"{dataset}.{prefix}_customers"

    client = get_bigquery_client()

    client.query(
        f"""
        CREATE TABLE IF NOT EXISTS `{tx}` (
          Invoice INT64,
          StockCode STRING,
          Description STRING,
          Quantity INT64,
          InvoiceDate TIMESTAMP,
          Price FLOAT64,
          `Customer ID` FLOAT64,
          Country STRING
        )
        """
    ).result()

    client.query(
        f"""
        CREATE TABLE IF NOT EXISTS `{customers}` (
          CustomerID INT64,
          CustomerName STRING,
          created_at TIMESTAMP
        )
        """
    ).result()

    return {"transactions": tx, "customers": customers}
