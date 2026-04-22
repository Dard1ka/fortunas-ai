"""Adapter untuk Meta WhatsApp Cloud API.

Meta beda dengan Twilio dalam 3 hal:
  1. Webhook verification: Meta GET /wa/webhook dengan ?hub.mode=subscribe
     &hub.verify_token=<TOKEN>&hub.challenge=<NONCE>. Kita harus echo `hub.challenge`
     kalau token cocok.
  2. Webhook payload: JSON nested (entry[].changes[].value.messages[]), bukan
     form-urlencoded.
  3. Balasan: bukan via TwiML response, tapi POST terpisah ke
     https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages.

Env yang dipakai:
  META_VERIFY_TOKEN     — string bebas yang kita pilih, dipakai saat setup webhook.
  META_ACCESS_TOKEN     — Bearer token (Permanent atau System User token).
  META_PHONE_NUMBER_ID  — ID nomor WA Business (bukan nomor telepon-nya).
  META_API_VERSION      — default 'v21.0'.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv

# Pastikan .env ke-load ke os.environ supaya os.getenv() bisa baca META_*.
# pydantic-settings hanya isi ke object Settings, tidak push ke os.environ.
load_dotenv()

log = logging.getLogger("fortunas.meta_wa")

GRAPH_BASE = "https://graph.facebook.com"


class MetaConfigError(RuntimeError):
    """Env Meta belum lengkap."""


# ────────────────────── Webhook verification ──────────────────────


def verify_webhook(mode: str, token: str, challenge: str) -> str | None:
    """Return string challenge kalau token cocok, atau None kalau ditolak."""
    expected = os.getenv("META_VERIFY_TOKEN", "").strip()
    if not expected:
        log.warning("META_VERIFY_TOKEN belum di-set, webhook verification akan gagal.")
        return None
    if mode == "subscribe" and token == expected:
        return challenge
    return None


# ────────────────────── Parse incoming webhook ──────────────────────


def extract_messages(payload: dict[str, Any]) -> list[dict[str, str]]:
    """Ambil daftar pesan teks dari webhook payload Meta.

    Return list of {"from": "<wa_id>", "body": "<text>", "message_id": "<wamid>"}.
    Pesan non-teks (image, audio, dst) diskip.
    """
    messages: list[dict[str, str]] = []
    if not isinstance(payload, dict):
        return messages

    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value") or {}
            for msg in value.get("messages", []) or []:
                if msg.get("type") != "text":
                    continue
                text = ((msg.get("text") or {}).get("body") or "").strip()
                if not text:
                    continue
                messages.append({
                    "from": str(msg.get("from", "")),
                    "body": text,
                    "message_id": str(msg.get("id", "")),
                })
    return messages


# ────────────────────── Send reply via Graph API ──────────────────────


def send_text_reply(to_wa_id: str, body: str) -> bool:
    """Kirim pesan teks balasan ke user. Return True kalau sukses.

    `to_wa_id` = nomor user dalam format internasional tanpa '+', contoh '628123456789'.
    Body otomatis dipotong di 4096 karakter (limit WhatsApp).
    """
    access_token = os.getenv("META_ACCESS_TOKEN", "").strip()
    phone_number_id = os.getenv("META_PHONE_NUMBER_ID", "").strip()
    api_version = os.getenv("META_API_VERSION", "v21.0").strip() or "v21.0"

    if not access_token or not phone_number_id:
        log.error("META_ACCESS_TOKEN / META_PHONE_NUMBER_ID belum di-set; balasan tidak terkirim.")
        return False
    if not to_wa_id or not body:
        return False

    url = f"{GRAPH_BASE}/{api_version}/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_wa_id,
        "type": "text",
        "text": {"body": body[:4096], "preview_url": False},
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
    except requests.RequestException as exc:
        log.exception("Gagal kirim balasan WA ke %s: %s", to_wa_id, exc)
        return False

    if r.status_code >= 400:
        log.error(
            "Meta API error %s saat kirim ke %s: %s",
            r.status_code, to_wa_id, r.text[:500],
        )
        return False
    log.info("Meta reply OK ke %s (status=%s, body=%s)", to_wa_id, r.status_code, r.text[:200])
    return True
