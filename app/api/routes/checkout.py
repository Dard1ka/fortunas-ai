# app/api/routes/checkout.py
"""Checkout multi-item (UMKM-auth) → BigQuery + opt-in loyalty link.

Coexist dengan /voice/transaction (tidak diganggu). BQ di belakang seam lazy
di checkout_service, jadi modul ini import bersih di CI.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.tenancy import TenantContext, get_current_tenant
from app.schemas import CheckoutConfirmRequest, CheckoutConfirmResponse
from app.services.checkout_service import confirm_checkout

router = APIRouter(tags=["checkout"])


@router.post("/checkout/confirm", response_model=CheckoutConfirmResponse)
def checkout_confirm(
    payload: CheckoutConfirmRequest,
    tenant: TenantContext = Depends(get_current_tenant),
) -> CheckoutConfirmResponse:
    return confirm_checkout(payload, tenant)
