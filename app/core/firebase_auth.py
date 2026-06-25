"""Seam verifikasi Firebase ID token — default-safe.

Prod: kredensial Firebase ada (FIREBASE_CREDENTIALS / credentials/firebase-admin.json)
      → lazy import firebase_admin (tak masuk CI).
Dev/CI: FORTUNAS_DEV_AUTH=1 + token "dev:<uid>:<phone>".
Tak ada keduanya → FirebaseNotConfigured (bootstrap balas 503).
"""
from __future__ import annotations

import os


class FirebaseAuthError(Exception):
    """Token Firebase invalid (route → 401)."""


class FirebaseNotConfigured(Exception):
    """Tak ada kredensial real & dev-mode mati (route → 503)."""


def _creds_path() -> str | None:
    path = os.getenv("FIREBASE_CREDENTIALS") or "credentials/firebase-admin.json"
    return path if os.path.isfile(path) else None


def verify_firebase_token(token: str) -> dict:
    """Return {firebase_uid, phone_number}. Raise FirebaseAuthError / FirebaseNotConfigured."""
    creds = _creds_path()
    if creds:
        return _verify_real(token, creds)
    if os.getenv("FORTUNAS_DEV_AUTH") == "1":
        return _verify_dev(token)
    raise FirebaseNotConfigured("Firebase belum dikonfigurasi.")


def _verify_dev(token: str) -> dict:
    parts = token.split(":")
    if len(parts) != 3 or parts[0] != "dev" or not parts[1]:
        raise FirebaseAuthError("Format dev token salah (harus 'dev:<uid>:<phone>').")
    return {"firebase_uid": parts[1], "phone_number": parts[2]}


def _verify_real(token: str, creds_path: str) -> dict:  # pragma: no cover (butuh kredensial)
    try:
        import firebase_admin
        from firebase_admin import auth, credentials

        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(creds_path))
        decoded = auth.verify_id_token(token)
    except Exception as exc:  # noqa: BLE001
        raise FirebaseAuthError("Token Firebase tidak valid.") from exc
    return {"firebase_uid": decoded["uid"], "phone_number": decoded.get("phone_number", "")}
