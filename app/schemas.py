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


# ── QR Identity + Validate (🟢) — REQUIREMENTS §6.3, REKOMENDASI A5 ──

class QRSessionResponse(BaseModel):
    qr_token: str
    nonce: str
    issued_at: str
    expires_at: str
    ttl_seconds: int = 90


class QRValidateRequest(BaseModel):
    customer_qr_token: str = Field(min_length=10)


class QRValidateResponse(BaseModel):
    valid: bool
    customer_user_id: str | None = None
    username: str | None = None
    is_new_member: bool = False
    member_since: str | None = None
    reason: str | None = None  # invalid: "expired" | "tampered" | "replayed"


# ── Checkout (multi-item, baru) (🟢) — REQUIREMENTS §7.6 ──────────

class CheckoutLineItem(BaseModel):
    product: str = Field(min_length=1)
    qty: int = Field(gt=0)
    unit_price: int = Field(ge=0)
    total: int | None = None

    @model_validator(mode="after")
    def _fill_total(self) -> "CheckoutLineItem":
        if self.total is None:
            self.total = self.qty * self.unit_price
        return self


class CheckoutConfirmRequest(BaseModel):
    items: list[CheckoutLineItem] = Field(min_length=1)
    customer: str = ""
    country: str = "Indonesia"
    invoice: str | None = None  # auto kalau kosong
    customer_qr_token: str | None = None  # opt-in (REKOMENDASI A7)
    promo_code: str | None = None

    @property
    def grand_total(self) -> int:
        return sum((it.total or it.qty * it.unit_price) for it in self.items)


class CheckoutConfirmResponse(BaseModel):
    ok: bool
    status: str
    reply: str
    invoice: str | None = None
    item_count: int = 0
    grand_total: int = 0
    customer_user_id: str | None = None
    is_new_member: bool = False
    member_since: str | None = None
    points_earned: int | None = None  # 🟡 null di MVP-now
    promo_redeemed: str | None = None  # 🟡 promo_id kalau ada


# ── DPA Policy (guardrail) (🟢) — REQUIREMENTS §7.2, REKOMENDASI A4 ──

class DPAPayload(BaseModel):
    raw_text: str = ""
    allowed_rules: list[str] = Field(default_factory=list)
    forbidden_rules: list[str] = Field(default_factory=list)
    policy_summary: str | None = None
    version: int = 0
    verified_at: str | None = None
    updated_at: str | None = None


class DPAUpdateRequest(BaseModel):
    raw_text: str = Field(min_length=1)
    allowed_rules: list[str] = Field(default_factory=list)
    forbidden_rules: list[str] = Field(default_factory=list)
    password: str = Field(min_length=1)  # konfirmasi (MVP; email-OTP → v5.1)


# ── Device Token (FCM) (🔵 v5.1 — kontrak saja) — REQUIREMENTS §6.6/§7.4 ──

class DeviceTokenRequest(BaseModel):
    fcm_token: str = Field(min_length=10)
    platform: Literal["android", "ios", "web"]
    user_type: Literal["customer", "umkm"] | None = None


# ── Loyalty + Points + Promo (🟡 MVP-thin) — REQUIREMENTS §6.4/§6.5/§7.5 ──

class SpinWheelSegment(BaseModel):
    discount_amount: int = Field(ge=0)
    probability: float = Field(ge=0, le=1)


def _default_spin_wheel() -> list[SpinWheelSegment]:
    # EV = Rp22.250 (REKOMENDASI "Catatan Ekonomi"). Jangan ubah tanpa kalibrasi.
    return [
        SpinWheelSegment(discount_amount=100_000, probability=0.05),
        SpinWheelSegment(discount_amount=50_000, probability=0.10),
        SpinWheelSegment(discount_amount=25_000, probability=0.25),
        SpinWheelSegment(discount_amount=10_000, probability=0.60),
    ]


class PointsEarningRule(BaseModel):
    type: Literal["per_amount", "per_invoice"] = "per_amount"
    points_per_amount: int = 10_000  # 1 poin / Rp10.000 (REKOMENDASI A1)
    points_per_invoice: int = 1


class LoyaltySettings(BaseModel):
    min_points_to_generate_promo: int = 30
    spin_wheel: list[SpinWheelSegment] = Field(default_factory=_default_spin_wheel)
    promo_valid_days: int = 7
    points_earning_rule: PointsEarningRule = Field(default_factory=PointsEarningRule)

    @model_validator(mode="after")
    def _check_probabilities(self) -> "LoyaltySettings":
        total = sum(s.probability for s in self.spin_wheel)
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Total probability spin_wheel harus 1.0 (sekarang {total}).")
        return self


class PointsLedgerEntry(BaseModel):
    event_type: str  # "earn" | "redeem" | "expire" | "adjust"
    points_delta: int
    invoice: str | None = None
    promo_id: str | None = None
    tenant_id: int | None = None
    created_at: str = ""


class PointsBalanceResponse(BaseModel):
    customer_user_id: str
    balance: int = 0
    recent: list[PointsLedgerEntry] = Field(default_factory=list)


class PromoInstance(BaseModel):
    promo_id: str
    tenant_id: int
    name: str
    code: str
    description: str = ""
    discount_amount: int
    target_product: str | None = None
    status: str = "generated"  # "generated" | "redeemed" | "expired"
    points_cost: int = 0
    generated_at: str = ""
    expires_at: str = ""
    redeemed_at: str | None = None
    qr_payload: str | None = None


class PromoGenerateRequest(BaseModel):
    tenant_id: int


class PromoGenerateResponse(BaseModel):
    promo: PromoInstance
    spin_result: SpinWheelSegment


class PromoListResponse(BaseModel):
    promos: list[PromoInstance] = Field(default_factory=list)
