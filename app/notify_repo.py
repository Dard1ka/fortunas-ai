"""Repository device token (FCM) + notification log.

FCM send BELUM diimplementasi (butuh kredensial Firebase Admin) — job internal
mencatat notifikasi ke notification_log dengan status 'queued'; worker FCM
tinggal membaca log ini nanti. Pola modul mengikuti app/customer_repo.py.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.db_pg import SessionLocal
from app.models import DeviceToken, NotificationLog


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def upsert_device_token(*, fcm_token: str, platform: str,
                        user_type: str, owner_ref: str) -> dict[str, Any]:
    """Token unik global; register ulang → update pemilik (device pindah akun)."""
    with SessionLocal() as s:
        row = s.scalar(select(DeviceToken).where(DeviceToken.fcm_token == fcm_token))
        if row is None:
            row = DeviceToken(fcm_token=fcm_token, platform=platform,
                              user_type=user_type, owner_ref=owner_ref,
                              created_at=_now())
            s.add(row)
        else:
            row.platform = platform
            row.user_type = user_type
            row.owner_ref = owner_ref
        s.commit()
        return {"id": row.id, "platform": row.platform,
                "user_type": row.user_type, "owner_ref": row.owner_ref}


def tokens_for(user_type: str, owner_ref: str) -> list[str]:
    with SessionLocal() as s:
        rows = s.scalars(select(DeviceToken).where(
            DeviceToken.user_type == user_type,
            DeviceToken.owner_ref == owner_ref,
        )).all()
        return [r.fcm_token for r in rows]


def log_notification(*, recipient_type: str, recipient_id: str, template: str,
                     channel: str = "push", status: str = "queued",
                     metadata: dict | None = None) -> int:
    with SessionLocal() as s:
        row = NotificationLog(
            recipient_type=recipient_type, recipient_id=recipient_id,
            template=template, channel=channel, status=status,
            sent_at=_now() if status == "sent" else None,
            metadata_json=metadata or {},
        )
        s.add(row)
        s.commit()
        return row.id


def already_logged_today(recipient_type: str, recipient_id: str, template: str) -> bool:
    """Idempotency guard job harian: 1 reminder / template / penerima / hari (UTC)."""
    today = _now()[:10]
    with SessionLocal() as s:
        rows = s.scalars(select(NotificationLog).where(
            NotificationLog.recipient_type == recipient_type,
            NotificationLog.recipient_id == recipient_id,
            NotificationLog.template == template,
        )).all()
        return any((r.sent_at or "").startswith(today)
                   or str(r.metadata_json.get("date", "")) == today for r in rows)
