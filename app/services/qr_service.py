"""QR identitas customer: signed JWT 90 detik + nonce. PURE (nol I/O DB).

Keamanan signature+exp ditegakkan di sini; single-use (konsumsi nonce) ditegakkan
terpisah di app/qr_nonce_repo.py oleh route scan.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.core.auth import JWT_ALGORITHM, JWT_SECRET

QR_TTL_SECONDS = 90


def issue_qr(customer_user_id: str) -> dict:
    now = datetime.now(timezone.utc)
    exp_dt = now + timedelta(seconds=QR_TTL_SECONDS)
    nonce = secrets.token_hex(8)
    token = jwt.encode(
        {"customer_user_id": customer_user_id, "nonce": nonce, "typ": "qr",
         "iat": now, "exp": exp_dt},
        JWT_SECRET, algorithm=JWT_ALGORITHM,
    )
    return {
        "qr_token": token,
        "nonce": nonce,
        "issued_at": now.isoformat(timespec="seconds"),
        "expires_at": exp_dt.isoformat(timespec="seconds"),
        "ttl_seconds": QR_TTL_SECONDS,
    }


def verify_qr(qr_token: str) -> dict:
    try:
        payload = jwt.decode(qr_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return {"valid": False, "reason": "expired"}
    except jwt.PyJWTError:
        return {"valid": False, "reason": "tampered"}

    cid = payload.get("customer_user_id")
    nonce = payload.get("nonce")
    if payload.get("typ") != "qr" or not cid or not nonce:
        return {"valid": False, "reason": "tampered"}
    exp_iso = datetime.fromtimestamp(payload["exp"], tz=timezone.utc).isoformat(timespec="seconds")
    return {"valid": True, "customer_user_id": cid, "nonce": nonce,
            "expires_at": exp_iso, "reason": None}
