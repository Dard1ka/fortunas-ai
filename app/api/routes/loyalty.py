"""Loyalty routes: settings UMKM, points/promo customer, home, device token, internal jobs.

REQUIREMENTS §6.2/§6.4/§6.5/§6.7/§7.5 + §11. BigQuery dibungkus lazy best-effort
(pola checkout_service): kegagalan BQ tidak menggagalkan endpoint customer.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app import customer_repo, db, dpa_repo, loyalty_repo, notify_repo, points_repo, promo_repo
from app.core.customer_ctx import CustomerContext, get_current_customer
from app.core.tenancy import TenantContext, get_current_tenant
from app.schemas import (
    CustomerHomeResponse,
    CustomerTransactionsResponse,
    DeviceTokenRequest,
    InternalJobResponse,
    LoyaltySettings,
    MembershipSummary,
    PointsBalanceResponse,
    PointsLedgerEntry,
    PromoGenerateRequest,
    PromoGenerateResponse,
    PromoInstance,
    PromoListResponse,
    PromoScanValidateRequest,
    PromoScanValidateResponse,
    SpinWheelSegment,
)
from app.services.promo_service import (
    PromoEligibilityError,
    generate_promo,
    verify_promo_qr,
)

log = logging.getLogger("fortunas.loyalty")
router = APIRouter(tags=["loyalty"])


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


# ── UMKM: loyalty settings (§7.5) ────────────────────────────────

@router.get("/umkm/settings/loyalty", response_model=LoyaltySettings)
def get_loyalty_settings(tenant: TenantContext = Depends(get_current_tenant)) -> LoyaltySettings:
    return LoyaltySettings(**loyalty_repo.get_loyalty(tenant.tenant_id))


@router.put("/umkm/settings/loyalty", response_model=LoyaltySettings)
def put_loyalty_settings(payload: LoyaltySettings,
                         tenant: TenantContext = Depends(get_current_tenant)) -> LoyaltySettings:
    return LoyaltySettings(**loyalty_repo.put_loyalty(tenant.tenant_id, payload))


# ── Customer: points (§6.4) ──────────────────────────────────────

@router.get("/customer/points", response_model=PointsBalanceResponse)
def get_points(ctx: CustomerContext = Depends(get_current_customer)) -> PointsBalanceResponse:
    return PointsBalanceResponse(
        customer_user_id=ctx.customer_user_id,
        balance=points_repo.get_balance(ctx.customer_user_id),
        recent=[PointsLedgerEntry(**e) for e in points_repo.recent_entries(ctx.customer_user_id)],
    )


# ── Customer: promo generate/list (§6.5) ─────────────────────────

def _promo_out(p: dict) -> PromoInstance:
    return PromoInstance(**{k: v for k, v in p.items() if k in PromoInstance.model_fields})


@router.post("/customer/promos/generate", response_model=PromoGenerateResponse)
def promos_generate(payload: PromoGenerateRequest,
                    ctx: CustomerContext = Depends(get_current_customer)) -> PromoGenerateResponse:
    tenant = db.get_tenant(payload.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="UMKM tidak ditemukan.")
    from app.core.config import get_settings
    s = get_settings()
    prefix = f"{s.bigquery_project_id}.{s.bigquery_dataset}.{tenant['table_prefix']}"
    try:
        result = generate_promo(
            customer_user_id=ctx.customer_user_id,
            customer_username=ctx.username,
            tenant_id=tenant["id"],
            tenant_name=tenant["name"],
            tx_table=f"{prefix}_transactions",
            customers_table=f"{prefix}_customers",
        )
    except PromoEligibilityError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=str(exc)) from exc
    return PromoGenerateResponse(
        promo=_promo_out(result["promo"]),
        spin_result=SpinWheelSegment(**result["spin_result"]),
    )


@router.get("/customer/promos", response_model=PromoListResponse)
def promos_list(ctx: CustomerContext = Depends(get_current_customer)) -> PromoListResponse:
    return PromoListResponse(
        promos=[_promo_out(p) for p in promo_repo.list_promos(ctx.customer_user_id)])


# ── Customer: home + transactions (§6.2/§6.7) ────────────────────

def _bq_recent_transactions(username: str, tx_table: str, customers_table: str,
                            limit: int = 20) -> list[dict]:  # pragma: no cover
    from google.cloud import bigquery

    from app.services.wa_pipeline_structured import resolve_customer_id
    cid = resolve_customer_id(username, customers_table, tx_table)
    if cid is None:
        return []
    client = bigquery.Client()
    sql = f"""
        SELECT Invoice, Description, Quantity, Price, InvoiceDate
        FROM `{tx_table}`
        WHERE `Customer ID` = @cid
        ORDER BY InvoiceDate DESC
        LIMIT {int(limit)}
    """
    job = client.query(sql, job_config=bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("cid", "INT64", cid)]))
    return [dict(r) for r in job.result()]


def _safe_transactions(username: str, tenant: dict, limit: int = 20) -> list[dict]:
    """Best-effort BQ; gagal → [] (endpoint tetap hidup tanpa kredensial)."""
    from app.core.config import get_settings
    s = get_settings()
    prefix = f"{s.bigquery_project_id}.{s.bigquery_dataset}.{tenant['table_prefix']}"
    try:
        rows = _bq_recent_transactions(
            username, f"{prefix}_transactions", f"{prefix}_customers", limit)
        for r in rows:
            r["tenant_id"] = tenant["id"]
            r["tenant_name"] = tenant["name"]
            if r.get("InvoiceDate") is not None:
                r["InvoiceDate"] = str(r["InvoiceDate"])
        return rows
    except Exception as exc:
        log.warning("BQ transactions unavailable (tenant=%s): %s", tenant["id"], exc)
        return []


@router.get("/customer/home", response_model=CustomerHomeResponse)
def customer_home(ctx: CustomerContext = Depends(get_current_customer)) -> CustomerHomeResponse:
    memberships = customer_repo.list_memberships(ctx.customer_user_id)
    summaries: list[MembershipSummary] = []
    last_tx: dict | None = None
    for m in memberships:
        tenant = db.get_tenant(m["tenant_id"])
        if tenant is None:
            continue
        summaries.append(MembershipSummary(
            tenant_id=tenant["id"], tenant_name=tenant["name"],
            member_since=m["member_since"]))
        if last_tx is None:
            rows = _safe_transactions(ctx.username, tenant, limit=1)
            if rows:
                last_tx = rows[0]
    promos = promo_repo.list_promos(ctx.customer_user_id, limit=1)
    return CustomerHomeResponse(
        username=ctx.username,
        total_points=points_repo.get_balance(ctx.customer_user_id),
        memberships=summaries,
        last_transaction=last_tx,
        last_promo=_promo_out(promos[0]) if promos else None,
    )


@router.get("/customer/transactions", response_model=CustomerTransactionsResponse)
def customer_transactions(
        ctx: CustomerContext = Depends(get_current_customer)) -> CustomerTransactionsResponse:
    memberships = customer_repo.list_memberships(ctx.customer_user_id)
    all_rows: list[dict] = []
    for m in memberships:
        tenant = db.get_tenant(m["tenant_id"])
        if tenant is not None:
            all_rows.extend(_safe_transactions(ctx.username, tenant))
    all_rows.sort(key=lambda r: str(r.get("InvoiceDate", "")), reverse=True)
    msg = "" if all_rows else "Belum ada transaksi (atau data belum tersedia)."
    return CustomerTransactionsResponse(status="ok", message=msg, transactions=all_rows[:50])


# ── Device tokens (§6.6/§7.4) ────────────────────────────────────

@router.post("/customer/device-token")
def customer_device_token(payload: DeviceTokenRequest,
                          ctx: CustomerContext = Depends(get_current_customer)) -> dict:
    row = notify_repo.upsert_device_token(
        fcm_token=payload.fcm_token, platform=payload.platform,
        user_type="customer", owner_ref=ctx.customer_user_id)
    return {"status": "ok", "device": row}


@router.post("/umkm/device-token")
def umkm_device_token(payload: DeviceTokenRequest,
                      tenant: TenantContext = Depends(get_current_tenant)) -> dict:
    row = notify_repo.upsert_device_token(
        fcm_token=payload.fcm_token, platform=payload.platform,
        user_type="umkm", owner_ref=str(tenant.tenant_id))
    return {"status": "ok", "device": row}


# ── Checkout: promo scan validate (§7.6) ─────────────────────────

@router.post("/checkout/promo-scan/validate", response_model=PromoScanValidateResponse)
def promo_scan_validate(payload: PromoScanValidateRequest,
                        tenant: TenantContext = Depends(get_current_tenant)
                        ) -> PromoScanValidateResponse:
    promo = None
    if payload.promo_qr_token:
        verified = verify_promo_qr(payload.promo_qr_token)
        if not verified["valid"]:
            return PromoScanValidateResponse(valid=False, reason=verified["reason"])
        promo = promo_repo.get_promo(verified["promo_id"])
    elif payload.promo_code:
        promo = promo_repo.get_promo_by_code(payload.promo_code.strip().upper())

    if promo is None:
        return PromoScanValidateResponse(valid=False, reason="not_found")
    if promo["tenant_id"] != tenant.tenant_id:
        return PromoScanValidateResponse(valid=False, reason="wrong_tenant")
    if promo["status"] != "generated":
        return PromoScanValidateResponse(valid=False, reason=promo["status"])
    return PromoScanValidateResponse(valid=True, promo=_promo_out(promo))


# ── Internal jobs (§11) — Cloud Scheduler/Tasks / cron VPS ───────

def _require_internal_token(x_internal_token: str | None) -> None:
    expected = os.getenv("INTERNAL_JOB_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503,
                            detail="INTERNAL_JOB_TOKEN belum dikonfigurasi.")
    if x_internal_token != expected:
        raise HTTPException(status_code=401, detail="Service token tidak valid.")


@router.post("/internal/jobs/dpa-reminders", response_model=InternalJobResponse)
def job_dpa_reminders(x_internal_token: str | None = Header(default=None)) -> InternalJobResponse:
    _require_internal_token(x_internal_token)
    processed, details = 0, []
    for t in db.list_tenants():
        if dpa_repo.get_dpa(t["id"])["version"] > 0:
            continue
        if notify_repo.already_logged_today("umkm", str(t["id"]), "dpa_reminder"):
            continue
        notify_repo.log_notification(
            recipient_type="umkm", recipient_id=str(t["id"]), template="dpa_reminder",
            metadata={"date": _today(), "tenant_name": t["name"]})
        processed += 1
        details.append(f"tenant {t['id']} ({t['name']}): DPA belum diisi")
    return InternalJobResponse(status="ok", job="dpa-reminders",
                               processed=processed, details=details)


@router.post("/internal/jobs/promo-reminders", response_model=InternalJobResponse)
def job_promo_reminders(x_internal_token: str | None = Header(default=None)) -> InternalJobResponse:
    _require_internal_token(x_internal_token)
    processed, details = 0, []
    for p in promo_repo.unused_promos():
        if notify_repo.already_logged_today("customer", p["customer_user_id"], "promo_unused"):
            continue
        notify_repo.log_notification(
            recipient_type="customer", recipient_id=p["customer_user_id"],
            template="promo_unused",
            metadata={"date": _today(), "promo_id": p["promo_id"], "code": p["code"],
                      "expires_at": p["expires_at"]})
        processed += 1
        details.append(f"promo {p['code']} → customer {p['customer_user_id']}")
    return InternalJobResponse(status="ok", job="promo-reminders",
                               processed=processed, details=details)


@router.post("/internal/jobs/daily-briefing", response_model=InternalJobResponse)
def job_daily_briefing(x_internal_token: str | None = Header(default=None)) -> InternalJobResponse:
    _require_internal_token(x_internal_token)
    processed, details = 0, []
    for t in db.list_tenants():
        if notify_repo.already_logged_today("umkm", str(t["id"]), "daily_briefing"):
            continue
        notify_repo.log_notification(
            recipient_type="umkm", recipient_id=str(t["id"]), template="daily_briefing",
            metadata={"date": _today(), "tenant_name": t["name"],
                      "note": "briefing dijalankan on-demand via /report/daily/run"})
        processed += 1
        details.append(f"tenant {t['id']} ({t['name']}): briefing queued")
    return InternalJobResponse(status="ok", job="daily-briefing",
                               processed=processed, details=details)
