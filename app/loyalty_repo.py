"""Repository loyalty settings per-tenant (tenant_settings.loyalty JSON).

Pola mengikuti app/dpa_repo.py: modul-level function, SessionLocal, return dict.
Default settings datang dari schemas.LoyaltySettings (satu sumber kebenaran).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db_pg import SessionLocal
from app.models import TenantSettings
from app.schemas import LoyaltySettings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_loyalty(tenant_id: int) -> dict[str, Any]:
    """Settings loyalty tenant; belum ada → default LoyaltySettings (tidak melempar)."""
    with SessionLocal() as s:
        row = s.get(TenantSettings, tenant_id)
        raw = dict(row.loyalty or {}) if row is not None else {}
    return LoyaltySettings(**raw).model_dump()


def put_loyalty(tenant_id: int, settings: LoyaltySettings) -> dict[str, Any]:
    """Upsert settings loyalty (validasi sudah di schema)."""
    now = _now()
    payload = settings.model_dump()
    with SessionLocal() as s:
        row = s.get(TenantSettings, tenant_id)
        if row is None:
            row = TenantSettings(tenant_id=tenant_id, loyalty=payload,
                                 created_at=now, updated_at=now)
            s.add(row)
        else:
            row.loyalty = payload
            row.updated_at = now
        s.commit()
    return payload
