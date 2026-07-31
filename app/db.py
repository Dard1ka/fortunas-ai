"""Metadata-store (SQLAlchemy) untuk multi-tenant: tenants + tenant_users + settings.

Data BISNIS (transaksi, customers) tetap di BigQuery. Lapisan ini HANYA akun/tenant.
Public function dipertahankan agar auth.py & tenancy.py tidak berubah; internal
pakai SQLAlchemy session (engine dari app.db_pg, dialek SQLite/Postgres).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.db_pg import Base, SessionLocal, engine
from app.models import Tenant, TenantSettings, TenantUser
from app.schemas import LoyaltySettings

# table_prefix di-interpolasi ke nama tabel BigQuery → batasi karakter aman.
_PREFIX_RE = re.compile(r"^[a-z][a-z0-9_]{1,30}$")


def init_db() -> None:
    """Buat semua tabel kalau belum ada (idempotent). Dipanggil di startup."""
    Base.metadata.create_all(bind=engine)


def is_valid_prefix(prefix: str) -> bool:
    return bool(_PREFIX_RE.match(prefix or ""))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _tenant_to_dict(t: Tenant | None) -> dict[str, Any] | None:
    if t is None:
        return None
    return {
        "id": t.id,
        "name": t.name,
        "table_prefix": t.table_prefix,
        "business_profile": t.business_profile or {},
        "created_at": t.created_at,
    }


def create_tenant(name: str, table_prefix: str, business_profile: dict | None = None) -> int:
    if not is_valid_prefix(table_prefix):
        raise ValueError(
            "table_prefix tidak valid (huruf kecil/angka/underscore, mulai huruf, panjang 2-31)."
        )
    now = _now()
    with SessionLocal() as s:
        tenant = Tenant(
            name=name,
            table_prefix=table_prefix,
            business_profile=business_profile or {},
            created_at=now,
        )
        s.add(tenant)
        s.flush()  # dapatkan tenant.id sebelum seed settings
        s.add(
            TenantSettings(
                tenant_id=tenant.id,
                loyalty=LoyaltySettings().model_dump(),
                created_at=now,
                updated_at=now,
            )
        )
        s.commit()
        return int(tenant.id)


def get_tenant(tenant_id: int) -> dict[str, Any] | None:
    with SessionLocal() as s:
        return _tenant_to_dict(s.get(Tenant, tenant_id))


def get_tenant_by_prefix(table_prefix: str) -> dict[str, Any] | None:
    with SessionLocal() as s:
        t = s.scalar(select(Tenant).where(Tenant.table_prefix == table_prefix))
        return _tenant_to_dict(t)


def list_tenants() -> list[dict[str, Any]]:
    with SessionLocal() as s:
        return [_tenant_to_dict(t) for t in s.scalars(select(Tenant)).all()]


def get_tenant_by_code(code: str) -> dict[str, Any] | None:
    """Cari tenant berdasarkan kode publik UMKM (mis. 'KDS-001'), case-insensitive.

    Kode disimpan di business_profile['code']. Scan sederhana (jumlah tenant kecil);
    bisa dioptimalkan jadi kolom terindeks bila perlu."""
    key = (code or "").strip().upper()
    if not key:
        return None
    with SessionLocal() as s:
        for t in s.scalars(select(Tenant)).all():
            c = ((t.business_profile or {}).get("code") or "").strip().upper()
            if c == key:
                return _tenant_to_dict(t)
    return None


def update_tenant_profile(tenant_id: int, updates: dict[str, Any]) -> dict[str, Any] | None:
    """Merge `updates` ke business_profile tenant (mis. address, code). Return tenant baru."""
    with SessionLocal() as s:
        t = s.get(Tenant, tenant_id)
        if t is None:
            return None
        merged = dict(t.business_profile or {})
        merged.update(updates)
        t.business_profile = merged
        s.commit()
        return _tenant_to_dict(t)


def all_umkm_codes() -> list[str]:
    """Semua kode publik UMKM yang sudah terpakai (untuk penomoran urut unik)."""
    with SessionLocal() as s:
        codes = []
        for t in s.scalars(select(Tenant)).all():
            c = (t.business_profile or {}).get("code")
            if c:
                codes.append(str(c))
        return codes


def create_user(email: str, password_hash: str, tenant_id: int, role: str = "admin") -> int:
    with SessionLocal() as s:
        user = TenantUser(
            email=email.strip().lower(),
            password_hash=password_hash,
            tenant_id=tenant_id,
            role=role,
            created_at=_now(),
        )
        s.add(user)
        s.commit()
        return int(user.id)


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with SessionLocal() as s:
        u = s.scalar(select(TenantUser).where(TenantUser.email == email.strip().lower()))
        if u is None:
            return None
        return {
            "id": u.id,
            "email": u.email,
            "password_hash": u.password_hash,
            "tenant_id": u.tenant_id,
            "role": u.role,
            "created_at": u.created_at,
        }
