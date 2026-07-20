"""Repository promo instances + events (lifecycle: generated → redeemed/expired).

Pola mengikuti app/customer_repo.py: modul-level function, SessionLocal, return dict.
Redeem dibuat idempotent-safe: hanya status 'generated' yang bisa redeemed (guard di SQL-level
via re-check dalam transaksi).
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.db_pg import SessionLocal
from app.models import PromoEvent, PromoInstanceRow


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _new_promo_id() -> str:
    return "pr_" + secrets.token_hex(8)


def _new_promo_code() -> str:
    # Kode pendek untuk dibaca kasir; uniqueness ditegakkan constraint DB.
    return "FTN-" + secrets.token_hex(3).upper()


def _to_dict(p: PromoInstanceRow) -> dict[str, Any]:
    return {
        "promo_id": p.promo_id,
        "tenant_id": p.tenant_id,
        "customer_user_id": p.customer_user_id,
        "name": p.name or "",
        "code": p.promo_code,
        "description": p.description or "",
        "discount_amount": p.discount_amount,
        "target_product": p.target_product,
        "status": p.status,
        "points_cost": p.points_cost,
        "generated_at": p.generated_at or "",
        "expires_at": p.expires_at or "",
        "redeemed_at": p.redeemed_at,
        "redeemed_invoice": p.redeemed_invoice,
    }


def _add_event(s, promo_id: str, event_type: str, metadata: dict | None = None) -> None:
    s.add(PromoEvent(promo_id=promo_id, event_type=event_type,
                     metadata_json=metadata or {}, created_at=_now()))


def create_promo(
    *,
    customer_user_id: str,
    tenant_id: int,
    name: str,
    description: str,
    discount_amount: int,
    target_product: str | None,
    points_cost: int,
    expires_at: str,
) -> dict[str, Any]:
    with SessionLocal() as s:
        p = PromoInstanceRow(
            promo_id=_new_promo_id(),
            customer_user_id=customer_user_id,
            tenant_id=tenant_id,
            promo_code=_new_promo_code(),
            name=name,
            description=description,
            target_product=target_product,
            discount_amount=discount_amount,
            points_cost=points_cost,
            status="generated",
            generated_at=_now(),
            expires_at=expires_at,
        )
        s.add(p)
        _add_event(s, p.promo_id, "generated",
                   {"discount_amount": discount_amount, "points_cost": points_cost})
        s.commit()
        return _to_dict(p)


def get_promo(promo_id: str) -> dict[str, Any] | None:
    with SessionLocal() as s:
        p = s.get(PromoInstanceRow, promo_id)
        return _to_dict(p) if p else None


def get_promo_by_code(promo_code: str) -> dict[str, Any] | None:
    with SessionLocal() as s:
        p = s.scalar(select(PromoInstanceRow).where(
            PromoInstanceRow.promo_code == promo_code))
        return _to_dict(p) if p else None


def list_promos(customer_user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    with SessionLocal() as s:
        rows = s.scalars(
            select(PromoInstanceRow)
            .where(PromoInstanceRow.customer_user_id == customer_user_id)
            .order_by(PromoInstanceRow.generated_at.desc())
            .limit(limit)
        ).all()
        return [_to_dict(p) for p in rows]


def redeem_promo(promo_id: str, *, invoice: str) -> dict[str, Any] | None:
    """Tandai redeemed. Hanya status 'generated' & belum lewat expiry.

    Return dict promo bila sukses; None bila tidak bisa (sudah dipakai/expired/tak ada)
    — caller yang memutuskan pesan error.
    """
    now = _now()
    with SessionLocal() as s:
        p = s.get(PromoInstanceRow, promo_id)
        if p is None or p.status != "generated":
            return None
        if p.expires_at and p.expires_at < now:
            p.status = "expired"
            _add_event(s, p.promo_id, "expired", {"checked_at": now})
            s.commit()
            return None
        p.status = "redeemed"
        p.redeemed_at = now
        p.redeemed_invoice = invoice
        _add_event(s, p.promo_id, "redeemed", {"invoice": invoice})
        s.commit()
        return _to_dict(p)


def unused_promos(limit: int = 500) -> list[dict[str, Any]]:
    """Promo generated & belum expired — kandidat reminder push (job harian)."""
    now = _now()
    with SessionLocal() as s:
        rows = s.scalars(
            select(PromoInstanceRow)
            .where(PromoInstanceRow.status == "generated",
                   PromoInstanceRow.expires_at > now)
            .limit(limit)
        ).all()
        return [_to_dict(p) for p in rows]
