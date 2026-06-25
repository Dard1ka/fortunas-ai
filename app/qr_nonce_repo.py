"""Single-use enforcement nonce QR. consume_nonce atomik via PK IntegrityError."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.db_pg import SessionLocal
from app.models import QRNonce


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def consume_nonce(nonce: str, expires_at: str) -> bool:
    """True kalau baru dikonsumsi; False kalau sudah ada (replay)."""
    with SessionLocal() as s:
        s.add(QRNonce(nonce=nonce, expires_at=expires_at, created_at=_now()))
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
            return False
    return True


def purge_expired(now_iso: str | None = None) -> int:
    cutoff = now_iso or _now()
    with SessionLocal() as s:
        result = s.execute(delete(QRNonce).where(QRNonce.expires_at < cutoff))
        s.commit()
        return int(result.rowcount or 0)
