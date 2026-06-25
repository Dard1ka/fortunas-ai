"""Scan QR customer (UMKM-auth): validasi deterministik + auto-membership."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app import customer_repo
from app.core.tenancy import TenantContext, get_current_tenant
from app.qr_nonce_repo import consume_nonce
from app.schemas import QRValidateRequest, QRValidateResponse
from app.services.qr_service import verify_qr

router = APIRouter(tags=["scan"])


@router.post("/umkm/customer/scan/validate", response_model=QRValidateResponse)
def scan_validate(
    payload: QRValidateRequest,
    tenant: TenantContext = Depends(get_current_tenant),
) -> QRValidateResponse:
    r = verify_qr(payload.customer_qr_token)
    if not r["valid"]:
        return QRValidateResponse(valid=False, reason=r["reason"])

    customer = customer_repo.get_customer(r["customer_user_id"])
    if customer is None:
        return QRValidateResponse(valid=False, reason="tampered")

    if not consume_nonce(r["nonce"], r["expires_at"]):
        return QRValidateResponse(valid=False, reason="replayed")

    membership, is_new = customer_repo.ensure_membership(
        r["customer_user_id"], tenant.tenant_id
    )
    return QRValidateResponse(
        valid=True,
        customer_user_id=customer["customer_user_id"],
        username=customer["username"],
        is_new_member=is_new,
        member_since=membership["member_since"],
        reason=None,
    )
