"""Payment gateway seam — Midtrans Snap dengan fallback simulasi.

Tujuan: alur checkout bisa diuji END-TO-END tanpa uang/kredensial nyata.
- Bila `MIDTRANS_SERVER_KEY` diset → pakai Midtrans Snap (sandbox default).
- Bila TIDAK diset → mode "simulated": kembalikan redirect_url internal yang,
  saat dibuka, langsung menandai pesanan lunas (untuk demo/testing).

Ganti provider cukup dengan mengganti implementasi `create_charge` +
`verify_notification`; pemanggil (routes) tidak perlu tahu detailnya.
"""
from __future__ import annotations

import base64
import hashlib
import os
from typing import Any

import httpx

_SANDBOX_URL = "https://app.sandbox.midtrans.com/snap/v1/transactions"
_PRODUCTION_URL = "https://app.midtrans.com/snap/v1/transactions"


def _server_key() -> str:
    return os.getenv("MIDTRANS_SERVER_KEY", "").strip()


def is_live() -> bool:
    """True bila Midtrans dikonfigurasi (ada server key)."""
    return bool(_server_key())


def _is_production() -> bool:
    return os.getenv("MIDTRANS_IS_PRODUCTION", "false").strip().lower() == "true"


def client_config() -> dict[str, Any]:
    """Info yang aman dibagi ke klien (mobile) untuk Snap."""
    return {
        "provider": "midtrans" if is_live() else "simulated",
        "client_key": os.getenv("MIDTRANS_CLIENT_KEY", "").strip(),
        "is_production": _is_production(),
    }


def create_charge(order: dict[str, Any]) -> dict[str, Any]:
    """Buat transaksi pembayaran untuk sebuah pesanan.

    Return: {"provider", "token", "redirect_url"}.
    - Midtrans: token = Snap token, redirect_url = Snap redirect page.
    - Simulasi: token = None, redirect_url = endpoint internal simulasi lunas.
    """
    payment_order_id = order["payment_order_id"]
    if not is_live():
        return {
            "provider": "simulated",
            "token": None,
            # Endpoint ini (routes) menandai pesanan lunas saat dibuka.
            "redirect_url": f"/public/orders/{order['id']}/simulate-pay",
        }

    items = order.get("items") or []
    item_details = [
        {
            "id": str(it.get("product_id", "")),
            "price": int(it["unit_price"]),
            "quantity": int(it["qty"]),
            "name": str(it.get("name", ""))[:50] or "Item",
        }
        for it in items
    ]
    payload = {
        "transaction_details": {
            "order_id": payment_order_id,
            "gross_amount": int(order["total"]),
        },
        "item_details": item_details,
        "customer_details": {
            "first_name": (order.get("customer_name") or "Pelanggan")[:50],
            "phone": order.get("customer_phone") or "",
        },
    }
    auth = base64.b64encode(f"{_server_key()}:".encode()).decode()
    url = _PRODUCTION_URL if _is_production() else _SANDBOX_URL
    resp = httpx.post(
        url,
        json=payload,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth}",
        },
        timeout=20.0,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "provider": "midtrans",
        "token": data.get("token"),
        "redirect_url": data.get("redirect_url"),
    }


def _map_status(transaction_status: str, fraud_status: str | None) -> str:
    """Petakan status Midtrans → outcome internal: paid | pending | failed."""
    ts = (transaction_status or "").lower()
    if ts in ("capture",):
        return "paid" if (fraud_status or "accept").lower() == "accept" else "pending"
    if ts in ("settlement",):
        return "paid"
    if ts in ("pending",):
        return "pending"
    # deny, cancel, expire, failure, refund, chargeback, ...
    return "failed"


def verify_notification(payload: dict[str, Any]) -> dict[str, Any]:
    """Validasi & petakan notifikasi webhook Midtrans.

    Return: {"valid", "payment_order_id", "transaction_status", "outcome"}.
    Signature Midtrans = sha512(order_id + status_code + gross_amount + server_key).
    """
    order_id = str(payload.get("order_id", ""))
    status_code = str(payload.get("status_code", ""))
    gross_amount = str(payload.get("gross_amount", ""))
    signature = str(payload.get("signature_key", ""))
    transaction_status = str(payload.get("transaction_status", ""))
    fraud_status = payload.get("fraud_status")

    expected = hashlib.sha512(
        f"{order_id}{status_code}{gross_amount}{_server_key()}".encode()
    ).hexdigest()
    valid = bool(signature) and signature == expected
    return {
        "valid": valid,
        "payment_order_id": order_id,
        "transaction_status": transaction_status,
        "outcome": _map_status(transaction_status, fraud_status),
    }
