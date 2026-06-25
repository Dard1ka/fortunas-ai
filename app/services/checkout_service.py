"""Checkout multi-item → BigQuery + opt-in loyalty link (reuse QR Day 4).

Sale = sumber kebenaran; loyalty best-effort SETELAH sale.
BigQuery di belakang satu seam lazy (`persist_basket`) supaya modul ini
import bersih di CI (tanpa google-cloud). Pola lazy = firebase_auth/pipeline.
"""
from __future__ import annotations

import os  # noqa: F401
from typing import Any  # noqa: F401

from app import customer_repo  # noqa: F401
from app.core.tenancy import TenantContext  # noqa: F401
from app.qr_nonce_repo import consume_nonce  # noqa: F401
from app.schemas import CheckoutConfirmRequest, CheckoutConfirmResponse  # noqa: F401
from app.services.qr_service import verify_qr  # noqa: F401


def resolve_bq_customer_name(req: CheckoutConfirmRequest, qr_username: str | None) -> str:
    """Unify, QR menang: identitas QR valid → username QR; else nama free-text request."""
    if qr_username:
        return qr_username
    return (req.customer or "").strip()


class CheckoutValidationError(ValueError):
    """Baris checkout gagal validasi BQ. Membungkus WaValidationError agar CI-clean
    (modul wa_validator menarik google.cloud, jadi tak bisa di-import di CI)."""


# ── Wrapper lazy: semua sentuhan BigQuery di sini (butuh kredensial → no cover) ──

def _bq_next_invoice(tx_table: str) -> int:  # pragma: no cover
    from app.services.wa_pipeline_structured import next_invoice_number
    return next_invoice_number(tx_table)


def _bq_resolve_customer_id(name: str, customers_table: str, tx_table: str) -> int | None:  # pragma: no cover
    from app.services.wa_pipeline_structured import resolve_customer_id
    return resolve_customer_id(name, customers_table, tx_table)


def _bq_validate_row(structured: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
    """Bangun + validasi 1 baris (reuse voice). Bungkus WaValidationError → CheckoutValidationError."""
    from app.services.wa_pipeline_structured import to_wa_payload
    from app.services.wa_validator import WaValidationError, validate_payload
    try:
        return validate_payload(to_wa_payload(structured))
    except WaValidationError as exc:
        raise CheckoutValidationError(str(exc)) from exc


def _bq_check_duplicate(invoice: int, stock_code: str, tx_table: str) -> bool:  # pragma: no cover
    from app.services.wa_validator import check_duplicate_in_bq
    return check_duplicate_in_bq(invoice, stock_code, tx_table)


def _bq_insert(rows: list[dict], tx_table: str) -> tuple[int, list[str]]:  # pragma: no cover
    from app.services.excel_upload import _insert_in_batches
    return _insert_in_batches(rows, table_ref=tx_table)


# ── Seam tunggal: orchestrasi BQ. Logika branching diuji offline via monkeypatch wrapper. ──

def persist_basket(
    items: list,
    customer_name: str,
    country: str,
    invoice: str | None,
    tx_table: str,
    customers_table: str,
) -> dict:
    explicit = bool((invoice or "").strip())
    inv = (invoice or "").strip() or str(_bq_next_invoice(tx_table))
    cid = _bq_resolve_customer_id(customer_name, customers_table, tx_table)
    cid_str = "" if cid is None else str(cid)

    rows: list[dict] = []
    try:
        for it in items:
            rows.append(_bq_validate_row({
                "invoice": inv,
                "product": it.product,
                "qty": it.qty,
                "unit_price": it.unit_price,
                "customer": cid_str,
                "country": country,
            }))
    except CheckoutValidationError as exc:
        return {"invoice": inv, "inserted": 0, "errors": [str(exc)], "status": "validation_error"}

    # Idempotency guard HANYA saat invoice eksplisit dikirim klien.
    if explicit and rows and all(_bq_check_duplicate(int(inv), r["StockCode"], tx_table) for r in rows):
        return {"invoice": inv, "inserted": 0, "errors": [], "status": "duplicate"}

    inserted, errors = _bq_insert(rows, tx_table)
    if errors or inserted < len(rows):
        return {"invoice": inv, "inserted": inserted, "errors": errors, "status": "bq_error"}
    return {"invoice": inv, "inserted": inserted, "errors": [], "status": "ok"}


def _rupiah(n: int) -> str:
    return ("Rp{:,.0f}".format(n)).replace(",", ".")


def _dry_run_enabled() -> bool:
    """CHECKOUT_DRY_RUN=true → validasi alur tanpa tulis BigQuery (cermin VOICE_DRY_RUN)."""
    return os.getenv("CHECKOUT_DRY_RUN", "false").lower() == "true"


def confirm_checkout(req: CheckoutConfirmRequest, tenant: TenantContext) -> CheckoutConfirmResponse:
    item_count = len(req.items)
    grand_total = req.grand_total
    base_reply = f"Tercatat {item_count} item, total {_rupiah(grand_total)}."

    if _dry_run_enabled():
        return CheckoutConfirmResponse(
            ok=True, status="dry_run",
            reply=f"(Mode uji) {base_reply} Penyimpanan BigQuery belum diaktifkan.",
            invoice=(req.invoice or None), item_count=item_count, grand_total=grand_total,
        )

    # QR pre-check (PURE, belum ada efek samping).
    qr = None
    qr_username = None
    link_note = ""
    if req.customer_qr_token:
        verified = verify_qr(req.customer_qr_token)
        if verified["valid"]:
            cust = customer_repo.get_customer(verified["customer_user_id"])
            if cust is not None:
                qr = verified
                qr_username = cust["username"]
            else:
                link_note = " (QR pelanggan tidak dikenali — poin tidak terhubung.)"
        else:
            link_note = " (QR pelanggan tidak valid/kedaluwarsa — poin tidak terhubung.)"

    name = resolve_bq_customer_name(req, qr_username)

    # ── SALE (primary) ──
    res = persist_basket(
        req.items, name, req.country, req.invoice,
        tenant.table("transactions"), tenant.table("customers"),
    )
    if res["status"] != "ok":
        msg = {
            "duplicate": f"Invoice {res['invoice']} sudah tercatat. Transaksi tidak digandakan.",
            "bq_error": f"Gagal menyimpan transaksi: {'; '.join(res['errors'][:2]) or 'kesalahan BigQuery'}.",
            "validation_error": f"Transaksi ditolak: {'; '.join(res['errors'][:2])}.",
        }.get(res["status"], "Transaksi gagal diproses.")
        return CheckoutConfirmResponse(
            ok=False, status=res["status"], reply=msg,
            invoice=(res["invoice"] if res["status"] == "duplicate" else None),
            item_count=item_count, grand_total=grand_total,
        )

    # ── Loyalty link (best-effort, SETELAH sale sukses) ──
    customer_user_id = None
    is_new_member = False
    member_since = None
    if qr is not None:  # QR valid + customer ada
        if consume_nonce(qr["nonce"], qr["expires_at"]):
            membership, is_new = customer_repo.ensure_membership(
                qr["customer_user_id"], tenant.tenant_id
            )
            customer_user_id = qr["customer_user_id"]
            is_new_member = is_new
            member_since = membership["member_since"]
            link_note = f" Pelanggan {qr_username} terhubung."
        else:
            link_note = " (QR sudah dipakai — poin tidak terhubung.)"

    return CheckoutConfirmResponse(
        ok=True, status="ok", reply=base_reply + link_note,
        invoice=res["invoice"], item_count=item_count, grand_total=grand_total,
        customer_user_id=customer_user_id, is_new_member=is_new_member, member_since=member_since,
        points_earned=None, promo_redeemed=None,
    )
