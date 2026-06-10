"""Voice-to-transaction endpoints.

Two-step flow:
  POST /voice/parse        — transcript → structured fields (preview to user)
  POST /voice/transaction  — confirmed payload → Sheets staging + BigQuery insert
"""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas import (
    VoiceParseRequest,
    VoiceParseResponse,
    VoiceTransactionRequest,
    VoiceTransactionResponse,
)
from app.services.voice_parser import parse_transcript
from app.services.wa_pipeline_structured import process_structured_transaction

router = APIRouter(tags=["voice"])


@router.post("/voice/parse", response_model=VoiceParseResponse)
def voice_parse(payload: VoiceParseRequest) -> VoiceParseResponse:
    parsed = parse_transcript(payload.transcript)
    return VoiceParseResponse(**parsed)


@router.post("/voice/transaction", response_model=VoiceTransactionResponse)
def voice_transaction(payload: VoiceTransactionRequest) -> VoiceTransactionResponse:
    structured = payload.model_dump()
    if not structured.get("total"):
        structured["total"] = structured["qty"] * structured["unit_price"]

    result = process_structured_transaction(structured, sender="voice_user")

    return VoiceTransactionResponse(
        ok=result["ok"],
        status=result["status"],
        reply=result["reply"],
        invoice=str(result["payload"]["Invoice"]) if result.get("payload") else None,
        row_number=result.get("row_number"),
    )
