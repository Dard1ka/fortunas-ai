"""Endpoint WhatsApp webhook untuk Meta Cloud API.

Meta butuh 2 endpoint pada URL yang sama:
  GET  /wa/webhook  → verifikasi (echo hub.challenge sekali saat setup)
  POST /wa/webhook  → terima pesan masuk (JSON), proses, balas via Graph API

Ada juga:
  POST /wa/simulate → testing lokal tanpa Meta (form: body, sender)
  POST /wa/retry    → retry baris Sheet status failed/pending → BigQuery
  GET  /wa/recent   → list transaksi terakhir dari Sheet
"""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from app.services import meta_wa, sheets_service
from app.services.wa_pipeline import process_wa_message, retry_failed_rows

load_dotenv()

log = logging.getLogger("fortunas.wa.route")


def _send_reply_enabled() -> bool:
    """Toggle apakah bot balas ke user via Meta Graph API.

    Set `META_SEND_REPLY=false` di .env kalau akun Meta kamu kena country
    restriction (error 130497) atau kamu memang mau silent-receive mode —
    pesan tetap diproses (parse → Sheet → BigQuery), cuma reply di-skip.
    """
    val = os.getenv("META_SEND_REPLY", "true").strip().lower()
    return val not in ("false", "0", "no", "off", "")

router = APIRouter(tags=["whatsapp"])


# ─────────────────── 1. Verifikasi webhook (Meta) ───────────────────


@router.get("/wa/webhook")
def meta_verify_webhook(
    hub_mode: str = Query("", alias="hub.mode"),
    hub_verify_token: str = Query("", alias="hub.verify_token"),
    hub_challenge: str = Query("", alias="hub.challenge"),
) -> Response:
    """Meta hit endpoint ini sekali saat kamu daftarkan webhook URL di dashboard.

    Kalau token cocok dengan META_VERIFY_TOKEN, balas plaintext `hub.challenge`
    dengan status 200. Kalau tidak, 403.
    """
    challenge = meta_wa.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    if challenge is None:
        return PlainTextResponse("Forbidden", status_code=403)
    return PlainTextResponse(challenge, status_code=200)


# ─────────────────── 2. Terima pesan masuk (Meta) ───────────────────


@router.post("/wa/webhook")
async def meta_receive_webhook(request: Request) -> JSONResponse:
    """Endpoint utama: terima pesan dari Meta, proses transaksi, balas user.

    Penting: Meta expect HTTP 200 secepat mungkin, kalau tidak event akan
    di-retry. Jadi kita selalu balas {"status":"ok"} kecuali payload jelas-jelas
    rusak. Reply ke user dilakukan via Graph API call (bukan response body).
    """
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse({"status": "bad_json"}, status_code=400)

    messages = meta_wa.extract_messages(payload)
    if not messages:
        # Bisa juga event status update / read receipt. Log dulu untuk debug.
        try:
            for entry in payload.get("entry", []) or []:
                for change in entry.get("changes", []) or []:
                    value = change.get("value") or {}
                    for st in value.get("statuses", []) or []:
                        log.info(
                            "Meta status event: id=%s status=%s recipient=%s errors=%s",
                            st.get("id"), st.get("status"),
                            st.get("recipient_id"), st.get("errors"),
                        )
        except Exception:  # noqa: BLE001
            pass
        return JSONResponse({"status": "ok", "processed": 0})

    reply_enabled = _send_reply_enabled()
    processed = 0
    for msg in messages:
        sender = msg["from"]
        body = msg["body"]
        try:
            result = process_wa_message(body, sender)
        except Exception as exc:  # noqa: BLE001
            log.exception("Pipeline crash untuk sender %s: %s", sender, exc)
            if reply_enabled:
                meta_wa.send_text_reply(sender, f"❌ Error internal: {exc}")
            continue

        log.info("WA %s → %s", sender, result["status"])
        if reply_enabled:
            meta_wa.send_text_reply(sender, result["reply"])
        else:
            log.info("Reply ke %s di-skip (META_SEND_REPLY=false)", sender)
        processed += 1

    return JSONResponse({"status": "ok", "processed": processed})


# ─────────────────── 3. Simulator lokal (tanpa Meta) ───────────────────


@router.post("/wa/simulate")
async def simulate_wa_message(
    body: str = Form(..., description="Isi pesan WA"),
    sender: str = Form("6281393378081", description="Nomor pengirim (wa_id, tanpa '+')"),
) -> JSONResponse:
    """Endpoint testing lokal — kirim pesan tanpa lewat Meta webhook.

    Return JSON supaya frontend bisa render pretty (chat bubble + payload).

    Contoh:
      curl -X POST http://127.0.0.1:8000/wa/simulate \\
        -F body='489438,21329,DINOSAURS WRITING SET,28,2009-12-01 09:24:00,0.98,18102.0,United Kingdom' \\
        -F sender='6281393378081'
    """
    result = process_wa_message(body, sender)
    return JSONResponse({
        "ok": bool(result.get("ok")),
        "status": result.get("status"),
        "reply": result.get("reply"),
        "payload": result.get("payload"),
        "sender": sender,
        "body": body,
    })


# ─────────────────── 4. Retry job ───────────────────


@router.post("/wa/retry")
def retry_wa_failed(max_rows: int = 100) -> dict:
    """Retry semua baris Sheet ber-status failed/pending → BigQuery."""
    max_rows = max(1, min(max_rows, 500))
    try:
        return retry_failed_rows(max_rows=max_rows)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": str(exc)}


# ─────────────────── 5. List riwayat ───────────────────


@router.get("/wa/recent")
def recent_wa_transactions(limit: int = 20) -> dict:
    """List transaksi WA terakhir (dari Google Sheet staging)."""
    limit = max(1, min(limit, 100))
    try:
        rows = sheets_service.list_recent_transactions(limit=limit)
        return {"status": "success", "count": len(rows), "rows": rows}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": str(exc), "rows": []}
