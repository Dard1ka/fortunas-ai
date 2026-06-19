"""Tenant context: identifikasi bisnis dari JWT + helper nama tabel BigQuery.

Setiap request yang menyentuh data WAJIB lewat get_current_tenant supaya backend
hanya mengakses tabel milik tenant tsb ({prefix}_transactions / {prefix}_customers).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import jwt
from fastapi import Depends, Header, HTTPException, status

from app import db
from app.core.auth import decode_access_token
from app.core.config import get_settings


@dataclass
class TenantContext:
    tenant_id: int
    name: str
    table_prefix: str
    business_profile: dict[str, Any] = field(default_factory=dict)
    email: str = ""

    def table(self, kind: str) -> str:
        """Full BigQuery ref untuk tabel tenant. kind: 'transactions' | 'customers'."""
        return tenant_table(self, kind)


def tenant_table(ctx: TenantContext, kind: str) -> str:
    """`project.dataset.{prefix}_{kind}` — dataset bersama, tabel ber-prefix tenant."""
    if kind not in ("transactions", "customers"):
        raise ValueError(f"kind tabel tidak dikenal: {kind}")
    s = get_settings()
    return f"{s.bigquery_project_id}.{s.bigquery_dataset}.{ctx.table_prefix}_{kind}"


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_tenant(authorization: str | None = Header(default=None)) -> TenantContext:
    """FastAPI dependency: baca 'Authorization: Bearer <jwt>' → TenantContext."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Token tidak ada. Sertakan header Authorization: Bearer <token>.")
    token = authorization.split(" ", 1)[1].strip()

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise _unauthorized("Token kedaluwarsa. Silakan login lagi.") from exc
    except jwt.PyJWTError as exc:
        raise _unauthorized("Token tidak valid.") from exc

    tenant_id = payload.get("tenant_id")
    tenant = db.get_tenant(tenant_id) if tenant_id is not None else None
    if not tenant:
        raise _unauthorized("Tenant tidak ditemukan.")

    return TenantContext(
        tenant_id=tenant["id"],
        name=tenant["name"],
        table_prefix=tenant["table_prefix"],
        business_profile=tenant.get("business_profile") or {},
        email=payload.get("email", ""),
    )


# Alias dependency untuk dipakai di route signatures.
CurrentTenant = Depends(get_current_tenant)
