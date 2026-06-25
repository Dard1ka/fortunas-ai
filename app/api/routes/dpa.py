"""DPA policy routes (UMKM): lihat & ubah aturan 'pagar AI'. Edit = password-confirm."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app import db, dpa_repo
from app.core.auth import verify_password
from app.core.tenancy import TenantContext, get_current_tenant
from app.schemas import DPAPayload, DPAUpdateRequest

router = APIRouter(tags=["dpa"])


@router.get("/umkm/dpa", response_model=DPAPayload)
def get_dpa(tenant: TenantContext = Depends(get_current_tenant)) -> DPAPayload:
    return DPAPayload(**dpa_repo.get_dpa(tenant.tenant_id))


@router.put("/umkm/dpa", response_model=DPAPayload)
def put_dpa(
    payload: DPAUpdateRequest,
    tenant: TenantContext = Depends(get_current_tenant),
) -> DPAPayload:
    user = db.get_user_by_email(tenant.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Konfirmasi password salah.")
    updated = dpa_repo.upsert_dpa(
        tenant.tenant_id,
        raw_text=payload.raw_text,
        allowed_rules=payload.allowed_rules,
        forbidden_rules=payload.forbidden_rules,
    )
    return DPAPayload(**updated)
