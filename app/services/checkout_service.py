"""Checkout multi-item → BigQuery + opt-in loyalty link (reuse QR Day 4).

Sale = sumber kebenaran; loyalty best-effort SETELAH sale.
BigQuery di belakang satu seam lazy (`persist_basket`) supaya modul ini
import bersih di CI (tanpa google-cloud). Pola lazy = firebase_auth/pipeline.
"""
from __future__ import annotations

import os  # noqa: F401
from typing import Any  # noqa: F401

from app import customer_repo  # noqa: F401
from app.core.tenancy import TenantContext  # noqa: F401
from app.qr_nonce_repo import consume_nonce  # noqa: F401
from app.schemas import CheckoutConfirmRequest, CheckoutConfirmResponse  # noqa: F401
from app.services.qr_service import verify_qr  # noqa: F401


def resolve_bq_customer_name(req: CheckoutConfirmRequest, qr_username: str | None) -> str:
    """Unify, QR menang: identitas QR valid → username QR; else nama free-text request."""
    if qr_username:
        return qr_username
    return (req.customer or "").strip()
