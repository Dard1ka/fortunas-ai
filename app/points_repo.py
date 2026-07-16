"""Repository points ledger + balance (universal per-customer).

Ledger = sumber kebenaran; balance = derived, di-update dalam transaksi yang sama
(REQUIREMENTS §6.4: "Use points ledger, not only mutable balance").
Pola mengikuti app/customer_repo.py: modul-level function, SessionLocal, return dict.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.db_pg import SessionLocal
from app.models import PointsBalance, PointsLedger


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _entry_to_dict(e: PointsLedger) -> dict[str, Any]:
    return {
        "event_type": e.event_type,
        "points_delta": e.points_delta,
        "invoice": e.invoice,
        "promo_id": e.promo_id,
        "tenant_id": e.tenant_id,
        "created_at": e.created_at or "",
    }


def add_entry(
    customer_user_id: str,
    *,
    event_type: str,
    points_delta: int,
    tenant_id: int | None = None,
    invoice: str | None = None,
    promo_id: str | None = None,
) -> dict[str, Any]:
    """Append ledger + update balance atomik. Return {entry, balance}.

    Saldo tidak boleh negatif — redeem melebihi saldo melempar ValueError
    (caller wajib cek eligibility dulu; ini guard terakhir).
    """
    with SessionLocal() as s:
        bal = s.get(PointsBalance, customer_user_id)
        current = bal.balance if bal is not None else 0
        new_balance = current + points_delta
        if new_balance < 0:
            raise ValueError(
                f"Saldo poin tidak cukup (saldo {current}, butuh {-points_delta})."
            )
        entry = PointsLedger(
            customer_user_id=customer_user_id,
            tenant_id=tenant_id,
            event_type=event_type,
            points_delta=points_delta,
            invoice=invoice,
            promo_id=promo_id,
            created_at=_now(),
        )
        s.add(entry)
        if bal is None:
            s.add(PointsBalance(customer_user_id=customer_user_id,
                                balance=new_balance, updated_at=_now()))
        else:
            bal.balance = new_balance
            bal.updated_at = _now()
        s.commit()
        return {"entry": _entry_to_dict(entry), "balance": new_balance}


def get_balance(customer_user_id: str) -> int:
    with SessionLocal() as s:
        bal = s.get(PointsBalance, customer_user_id)
        return bal.balance if bal is not None else 0


def recent_entries(customer_user_id: str, limit: int = 20) -> list[dict[str, Any]]:
    with SessionLocal() as s:
        rows = s.scalars(
            select(PointsLedger)
            .where(PointsLedger.customer_user_id == customer_user_id)
            .order_by(PointsLedger.id.desc())
            .limit(limit)
        ).all()
        return [_entry_to_dict(e) for e in rows]
