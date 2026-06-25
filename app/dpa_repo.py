"""Repository DPA policy per-tenant (1:1 atas tabel tenant_dpa_policies).

Pola mengikuti app/db.py: modul-level function, SessionLocal, return dict.
Data BISNIS tetap di BigQuery; ini hanya state aplikasi (Postgres/SQLite).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db_pg import SessionLocal
from app.models import TenantDPAPolicy


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _empty() -> dict[str, Any]:
    return {
        "raw_text": "",
        "allowed_rules": [],
        "forbidden_rules": [],
        "policy_summary": None,
        "version": 0,
        "verified_at": None,
        "updated_at": None,
    }


def _to_dict(row: TenantDPAPolicy | None) -> dict[str, Any]:
    if row is None:
        return _empty()
    return {
        "raw_text": row.raw_text or "",
        "allowed_rules": list(row.allowed_rules or []),
        "forbidden_rules": list(row.forbidden_rules or []),
        "policy_summary": row.policy_summary,
        "version": int(row.version or 0),
        "verified_at": row.verified_at,
        "updated_at": row.updated_at,
    }


def get_dpa(tenant_id: int) -> dict[str, Any]:
    """Policy current tenant. Belum ada → payload kosong (version 0), tidak melempar."""
    with SessionLocal() as s:
        return _to_dict(s.get(TenantDPAPolicy, tenant_id))


def upsert_dpa(
    tenant_id: int,
    *,
    raw_text: str,
    allowed_rules: list[str],
    forbidden_rules: list[str],
) -> dict[str, Any]:
    """Insert (version 1) / update (version+1). Set updated_at=verified_at=now."""
    now = _now()
    with SessionLocal() as s:
        row = s.get(TenantDPAPolicy, tenant_id)
        if row is None:
            row = TenantDPAPolicy(
                tenant_id=tenant_id,
                raw_text=raw_text,
                allowed_rules=list(allowed_rules),
                forbidden_rules=list(forbidden_rules),
                version=1,
                verified_at=now,
                updated_at=now,
            )
            s.add(row)
        else:
            row.raw_text = raw_text
            row.allowed_rules = list(allowed_rules)
            row.forbidden_rules = list(forbidden_rules)
            row.version = int(row.version or 0) + 1
            row.verified_at = now
            row.updated_at = now
        s.commit()
        return _to_dict(row)
