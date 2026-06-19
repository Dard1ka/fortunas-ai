"""Auth routes: register (buat tenant + admin user) + login → JWT."""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app import db
from app.core.auth import create_access_token, hash_password, verify_password
from app.core.tenancy import TenantContext, get_current_tenant

router = APIRouter(tags=["auth"])

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    business_name: str = Field(min_length=2)
    table_prefix: str | None = None  # opsional; kalau kosong diturunkan dari business_name
    business_profile: dict = Field(default_factory=dict)  # jenis usaha, target, dll

    @field_validator("email")
    @classmethod
    def _check_email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v.strip()):
            raise ValueError("Format email tidak valid.")
        return v.strip().lower()


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: int
    tenant_name: str
    table_prefix: str


def _slugify_prefix(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    if not s or not s[0].isalpha():
        s = "t_" + s
    return s[:31]


@router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> AuthResponse:
    email = payload.email.lower()
    if db.get_user_by_email(email):
        raise HTTPException(status_code=409, detail="Email sudah terdaftar.")

    prefix = (payload.table_prefix or _slugify_prefix(payload.business_name)).lower()
    if not db.is_valid_prefix(prefix):
        raise HTTPException(
            status_code=422,
            detail="table_prefix tidak valid (huruf kecil/angka/underscore, mulai huruf, maks 31).",
        )
    if db.get_tenant_by_prefix(prefix):
        raise HTTPException(status_code=409, detail=f"Prefix '{prefix}' sudah dipakai bisnis lain.")

    tenant_id = db.create_tenant(
        name=payload.business_name,
        table_prefix=prefix,
        business_profile=payload.business_profile,
    )
    # Provisioning tabel BigQuery tenant (idempotent). Fase 3.
    try:
        from app.services.tenant_provisioning import provision_tenant_tables

        provision_tenant_tables(prefix)
    except Exception:  # noqa: BLE001 — provisioning gagal tidak boleh batalkan register
        pass

    user_id = db.create_user(
        email=email, password_hash=hash_password(payload.password), tenant_id=tenant_id
    )
    token = create_access_token(user_id=user_id, email=email, tenant_id=tenant_id)
    return AuthResponse(
        access_token=token,
        tenant_id=tenant_id,
        tenant_name=payload.business_name,
        table_prefix=prefix,
    )


@router.get("/auth/me")
def me(tenant: TenantContext = Depends(get_current_tenant)) -> dict:
    """Info akun yang sedang login (untuk tampil di halaman profil)."""
    return {
        "email": tenant.email,
        "tenant_id": tenant.tenant_id,
        "tenant_name": tenant.name,
        "table_prefix": tenant.table_prefix,
        "business_profile": tenant.business_profile,
    }


@router.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    user = db.get_user_by_email(payload.email.lower())
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email atau password salah.")

    tenant = db.get_tenant(user["tenant_id"])
    if not tenant:
        raise HTTPException(status_code=500, detail="Tenant untuk user ini tidak ditemukan.")

    token = create_access_token(
        user_id=user["id"], email=user["email"], tenant_id=user["tenant_id"]
    )
    return AuthResponse(
        access_token=token,
        tenant_id=tenant["id"],
        tenant_name=tenant["name"],
        table_prefix=tenant["table_prefix"],
    )
