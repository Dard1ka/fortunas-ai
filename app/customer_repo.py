"""Repository customer + membership (state aplikasi di Postgres/SQLite).

Pola mengikuti app/db.py & app/dpa_repo.py: modul-level function, SessionLocal,
return dict. Data BISNIS (transaksi) tetap di BigQuery.
"""
from __future__ import annotations

import secrets
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select

from app.db_pg import SessionLocal
from app.models import CustomerTenantMembership, CustomerUser


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _new_customer_id() -> str:
    return "cu_" + secrets.token_hex(8)


def _customer_to_dict(c: CustomerUser | None) -> dict[str, Any] | None:
    if c is None:
        return None
    return {
        "customer_user_id": c.customer_user_id,
        "username": c.username,
        "phone_number": c.phone_number or "",
        "birth_date": c.birth_date or "",
        "created_at": c.created_at or "",
    }


def get_customer(customer_user_id: str) -> dict[str, Any] | None:
    with SessionLocal() as s:
        return _customer_to_dict(s.get(CustomerUser, customer_user_id))


def get_customer_by_firebase_uid(firebase_uid: str) -> dict[str, Any] | None:
    with SessionLocal() as s:
        c = s.scalar(select(CustomerUser).where(CustomerUser.firebase_uid == firebase_uid))
        return _customer_to_dict(c)


def upsert_customer(*, firebase_uid: str, phone_number: str, username: str,
                    birth_date: str) -> tuple[dict[str, Any], bool]:
    """Ada (by firebase_uid) -> (existing, False) tanpa clobber; baru -> insert -> (row, True)."""
    with SessionLocal() as s:
        existing = s.scalar(
            select(CustomerUser).where(CustomerUser.firebase_uid == firebase_uid)
        )
        if existing is not None:
            return _customer_to_dict(existing), False
        c = CustomerUser(
            customer_user_id=_new_customer_id(),
            firebase_uid=firebase_uid,
            username=username,
            phone_number=phone_number,
            birth_date=birth_date,
            created_at=_now(),
        )
        s.add(c)
        s.commit()
        return _customer_to_dict(c), True


def update_customer(customer_user_id: str, *, username: str | None = None,
                    birth_date: str | None = None) -> dict[str, Any] | None:
    with SessionLocal() as s:
        c = s.get(CustomerUser, customer_user_id)
        if c is None:
            return None
        if username is not None:
            c.username = username
        if birth_date is not None:
            c.birth_date = birth_date
        s.commit()
        return _customer_to_dict(c)


def _membership_to_dict(m: CustomerTenantMembership) -> dict[str, Any]:
    return {
        "id": m.id,
        "customer_user_id": m.customer_user_id,
        "tenant_id": m.tenant_id,
        "member_since": m.member_since,
        "created_at": m.created_at,
    }


def get_membership(customer_user_id: str, tenant_id: int) -> dict[str, Any] | None:
    with SessionLocal() as s:
        m = s.scalar(
            select(CustomerTenantMembership).where(
                CustomerTenantMembership.customer_user_id == customer_user_id,
                CustomerTenantMembership.tenant_id == tenant_id,
            )
        )
        return _membership_to_dict(m) if m else None


def ensure_membership(customer_user_id: str, tenant_id: int) -> tuple[dict[str, Any], bool]:
    """Ada -> (existing, False); baru -> member_since=today -> (row, True)."""
    with SessionLocal() as s:
        m = s.scalar(
            select(CustomerTenantMembership).where(
                CustomerTenantMembership.customer_user_id == customer_user_id,
                CustomerTenantMembership.tenant_id == tenant_id,
            )
        )
        if m is not None:
            return _membership_to_dict(m), False
        m = CustomerTenantMembership(
            customer_user_id=customer_user_id,
            tenant_id=tenant_id,
            member_since=date.today().isoformat(),
            created_at=_now(),
        )
        s.add(m)
        s.commit()
        return _membership_to_dict(m), True
