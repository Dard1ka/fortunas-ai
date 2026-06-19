"""Voice-to-transaction endpoints.

Two-step flow:
  POST /voice/parse        — transcript → structured fields (preview to user)
  POST /voice/transaction  — confirmed payload → Sheets staging + BigQuery insert
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends

from app.core.tenancy import TenantContext, get_current_tenant
from app.schemas import (
    VoiceParseRequest,
    VoiceParseResponse,
    VoiceTransactionRequest,
    VoiceTransactionResponse,
)
from app.services.voice_parser import parse_transcript
from app.services.wa_pipeline_structured import next_invoice_number, process_structured_transaction

router = APIRouter(tags=["voice"])


def _dry_run_enabled() -> bool:
    """Milestone 1 toggle. When VOICE_DRY_RUN=true, /voice/transaction validates
    the payload shape but SKIPS Google Sheets + BigQuery writes — useful to test
    the full voice → parse → confirm UI flow before wiring up real persistence.
    Set VOICE_DRY_RUN=false (or remove it) in .env to enable real BigQuery inserts."""
    return os.getenv("VOICE_DRY_RUN", "false").lower() == "true"


@router.post("/voice/parse", response_model=VoiceParseResponse)
def voice_parse(
    payload: VoiceParseRequest,
    tenant: TenantContext = Depends(get_current_tenant),
) -> VoiceParseResponse:
    parsed = parse_transcript(payload.transcript)
    # Invoice SELALU dibuat otomatis (user tidak menyebutnya), dari tabel tenant.
    try:
        parsed["invoice"] = str(next_invoice_number(tenant.table("transactions")))
    except Exception:  # noqa: BLE001
        parsed["invoice"] = ""  # diisi saat confirm oleh process_structured_transaction
    return VoiceParseResponse(**parsed)


@router.post("/voice/transaction", response_model=VoiceTransactionResponse)
def voice_transaction(
    payload: VoiceTransactionRequest,
    tenant: TenantContext = Depends(get_current_tenant),
) -> VoiceTransactionResponse:
    structured = payload.model_dump()
    if not structured.get("total"):
        structured["total"] = structured["qty"] * structured["unit_price"]

    if _dry_run_enabled():
        # Mode uji: validasi alur tanpa menulis ke BigQuery.
        return VoiceTransactionResponse(
            ok=True,
            status="dry_run",
            reply=(
                f"✅ (Mode uji) Transaksi {structured.get('product')} diterima. "
                "Penyimpanan ke BigQuery belum diaktifkan."
            ),
            invoice=str(structured.get("invoice")) if structured.get("invoice") else None,
            row_number=None,
        )

    result = process_structured_transaction(structured, tenant)

    return VoiceTransactionResponse(
        ok=result["ok"],
        status=result["status"],
        reply=result["reply"],
        invoice=str(result["payload"]["Invoice"]) if result.get("payload") else None,
        row_number=None,
    )
