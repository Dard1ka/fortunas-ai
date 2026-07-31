"""Riwayat transaksi per-UMKM: grouping BQ + empty-safe + isolasi tenant."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import auth, transactions
from app.services import transactions_service


def _fake_rows():
    # Dua line item invoice 1002, satu invoice 1001 (urut terbaru dulu dari BQ).
    return [
        {"Invoice": 1002, "StockCode": "ko-001", "Description": "Kopi Susu",
         "Quantity": 2, "Price": 15000.0, "InvoiceDate": "2026-07-27T10:00:00",
         "CustomerID": "42", "Country": "Indonesia"},
        {"Invoice": 1002, "StockCode": "te-001", "Description": "Teh Manis",
         "Quantity": 1, "Price": 8000.0, "InvoiceDate": "2026-07-27T10:00:00",
         "CustomerID": "42", "Country": "Indonesia"},
        {"Invoice": 1001, "StockCode": "ko-001", "Description": "Kopi Susu",
         "Quantity": 1, "Price": 15000.0, "InvoiceDate": "2026-07-27T09:00:00",
         "CustomerID": "", "Country": "Indonesia"},
    ]


def test_group_by_invoice_builds_transactions():
    grouped = transactions_service._group_by_invoice(_fake_rows())
    assert [t["invoice"] for t in grouped] == ["1002", "1001"]  # urutan dipertahankan
    first = grouped[0]
    assert len(first["items"]) == 2
    assert first["total"] == 2 * 15000 + 1 * 8000  # 38000
    assert first["customer"] == "42"
    assert grouped[1]["total"] == 15000


def test_list_umkm_transactions_empty_safe(monkeypatch):
    # BQ error → daftar kosong, bukan exception.
    def _boom(_tx_table, _limit):
        raise RuntimeError("BQ mati")

    monkeypatch.setattr(transactions_service, "_bq_query_transactions", _boom)

    class _T:
        tenant_id = 1
        def table(self, kind): return f"proj.ds.abc_{kind}"

    assert transactions_service.list_umkm_transactions(_T()) == []


def _client() -> TestClient:
    app = FastAPI()
    for r in (auth.router, transactions.router):
        app.include_router(r)
    return TestClient(app)


def _tok(c) -> str:
    r = c.post("/auth/register",
               json={"email": "o@t.com", "password": "rahasia123", "business_name": "Toko"})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def test_endpoint_returns_grouped_transactions(monkeypatch):
    monkeypatch.setattr(transactions_service, "_bq_query_transactions",
                        lambda _t, _l: _fake_rows())
    c = _client()
    tok = _tok(c)
    r = c.get("/umkm/transactions", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["count"] == 2
    assert body["source"] == "bigquery"
    assert body["transactions"][0]["invoice"] == "1002"
    assert body["transactions"][0]["total"] == 38000


def test_endpoint_requires_auth():
    c = _client()
    assert c.get("/umkm/transactions").status_code == 401
