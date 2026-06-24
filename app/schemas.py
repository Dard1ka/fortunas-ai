from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class AskRequest(BaseModel):
    question: str


class LLMOutput(BaseModel):
    summary: str
    top_findings: list[str] = Field(default_factory=list)
    recommendation: list[str] = Field(default_factory=list)
    data_confidence: str = "low"
    rag_sources: list[str] = Field(default_factory=list)


class AskResponse(BaseModel):
    question: str
    mapped_analysis: str
    status: str
    message: str
    agent_trace: list[str] = Field(default_factory=list)
    rows: list[dict] = Field(default_factory=list)
    llm_output: LLMOutput | None = None


class BriefingSection(BaseModel):
    analysis_type: str
    label: str
    status: str
    summary: str
    top_findings: list[str] = Field(default_factory=list)
    recommendation: list[str] = Field(default_factory=list)
    row_count: int = 0
    data_confidence: str | None = None
    rag_sources: list[str] = Field(default_factory=list)


class BriefingResponse(BaseModel):
    status: str
    message: str
    executive_summary: str = ""
    sections: list[BriefingSection] = Field(default_factory=list)
    agent_trace: list[str] = Field(default_factory=list)


class DailyReportEntry(BaseModel):
    generated_at: str
    date: str
    executive_summary: str
    sections: list[BriefingSection] = Field(default_factory=list)


class DailyReportResponse(BaseModel):
    status: str
    message: str
    latest: DailyReportEntry | None = None
    history: list[DailyReportEntry] = Field(default_factory=list)


class IngestResponse(BaseModel):
    status: str
    message: str
    ingested_chunks: int = 0
    docs: list[str] = Field(default_factory=list)


class UploadPreviewResponse(BaseModel):
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[str] = Field(default_factory=list)
    sample: list[dict] = Field(default_factory=list)


class UploadResponse(BaseModel):
    status: str
    message: str
    table: str
    total_rows: int
    valid_rows: int = 0
    invalid_rows: int = 0
    inserted_rows: int = 0
    errors: list[str] = Field(default_factory=list)


class VoiceParseRequest(BaseModel):
    transcript: str


class VoiceParseResponse(BaseModel):
    invoice: str = ""
    product: str = ""
    qty: int = 0
    unit_price: int = 0
    total: int = 0
    customer: str = ""
    country: str = "Indonesia"
    confidence: float = 0.0
    source: str = ""


class VoiceTransactionRequest(BaseModel):
    invoice: str
    product: str
    qty: int
    unit_price: int
    total: int | None = None
    customer: str = ""
    country: str = "Indonesia"


class VoiceTransactionResponse(BaseModel):
    ok: bool
    status: str
    reply: str
    invoice: str | None = None
    row_number: int | None = None


# ═══════════════════════════════════════════════════════════════
# v5.0 MVP — kontrak baru (additive). Status: 🟢 now · 🟡 thin · 🔵 v5.1
# ═══════════════════════════════════════════════════════════════


def _validate_past_date(v: str, field_name: str) -> str:
    """Pastikan string 'YYYY-MM-DD' valid & di masa lalu. Return ISO normalized."""
    try:
        d = date.fromisoformat(v.strip())
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{field_name} harus format YYYY-MM-DD.") from exc
    if d >= date.today():
        raise ValueError(f"{field_name} harus di masa lalu.")
    return d.isoformat()


# ── Customer Auth & Profile (🟢) — REQUIREMENTS §5.1 ──────────────

class CustomerBootstrapRequest(BaseModel):
    firebase_id_token: str = Field(min_length=10)
    username: str = Field(min_length=2, max_length=40)
    birth_date: str  # "YYYY-MM-DD"

    @field_validator("username")
    @classmethod
    def _trim_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("username minimal 2 karakter.")
        return v

    @field_validator("birth_date")
    @classmethod
    def _check_birth_date(cls, v: str) -> str:
        return _validate_past_date(v, "birth_date")


class CustomerProfile(BaseModel):
    customer_user_id: str
    username: str
    phone_number: str = ""
    birth_date: str = ""
    created_at: str = ""


class CustomerBootstrapResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "customer"
    is_new_user: bool = False
    profile: CustomerProfile


class CustomerProfileUpdate(BaseModel):
    username: str | None = Field(default=None, max_length=40)
    birth_date: str | None = None

    @field_validator("username")
    @classmethod
    def _trim_username(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("username minimal 2 karakter.")
        return v

    @field_validator("birth_date")
    @classmethod
    def _check_birth_date(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _validate_past_date(v, "birth_date")
