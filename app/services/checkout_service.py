"""Checkout multi-item → BigQuery + opt-in loyalty link (reuse QR Day 4).

Sale = sumber kebenaran; loyalty best-effort SETELAH sale.
BigQuery di belakang satu seam lazy (`persist_basket`) supaya modul ini
import bersih di CI (tanpa google-cloud). Pola lazy = firebase_auth/pipeline.
"""
from __future__ import annotations

import os
from typing import Any

from app import customer_repo, loyalty_repo, points_repo, product_repo, promo_repo
from app.core.tenancy import TenantContext
from app.qr_nonce_repo import consume_nonce
from app.schemas import CheckoutConfirmRequest, CheckoutConfirmResponse, CheckoutLineItem
from app.services.promo_service import verify_promo_qr
from app.services.qr_service import verify_qr


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
    tenant_id: int | None = None,
) -> dict:
    # Normalisasi invoice ke digit (konsisten dgn voice to_wa_payload yang strip non-digit),
    # supaya dup-check int(inv) tidak pernah crash & invoice di response = yang tersimpan di BQ.
    digits = "".join(ch for ch in (invoice or "") if ch.isdigit())
    explicit = bool(digits)
    inv = digits or str(_bq_next_invoice(tx_table))
    cid = _bq_resolve_customer_id(customer_name, customers_table, tx_table)
    cid_str = "" if cid is None else str(cid)

    rows: list[dict] = []
    matched: list[str] = []  # nama produk yang terdeteksi ada di Kelola Produk
    try:
        for it in items:
            # Deteksi barang pesanan di katalog tenant: kalau terdaftar, pakai
            # stock_code katalog (ko-001) supaya histori transaksi UMKM
            # tertaut ke produknya. Kalau tidak, fallback kode turunan nama.
            catalog_code = None
            if tenant_id is not None:
                try:
                    prod = product_repo.find_by_name(tenant_id, it.product)
                    if prod is not None:
                        catalog_code = prod["stock_code"]
                        matched.append(prod["name"])
                except Exception:
                    catalog_code = None  # lookup gagal → jangan gagalkan penjualan
            structured = {
                "invoice": inv,
                "product": it.product,
                "qty": it.qty,
                "unit_price": it.unit_price,
                "customer": cid_str,
                "country": country,
            }
            if catalog_code:
                structured["stock_code"] = catalog_code
            rows.append(_bq_validate_row(structured))
    except CheckoutValidationError as exc:
        return {"invoice": inv, "inserted": 0, "errors": [str(exc)], "status": "validation_error"}

    # Idempotency guard HANYA saat invoice eksplisit dikirim klien.
    if explicit and rows and all(_bq_check_duplicate(int(inv), r["StockCode"], tx_table) for r in rows):
        return {"invoice": inv, "inserted": 0, "errors": [], "status": "duplicate"}

    inserted, errors = _bq_insert(rows, tx_table)
    if errors or inserted < len(rows):
        return {"invoice": inv, "inserted": inserted, "errors": errors,
                "status": "bq_error", "matched_products": matched}
    return {"invoice": inv, "inserted": inserted, "errors": [],
            "status": "ok", "matched_products": matched}


def persist_completed_order(order: dict, tenant: TenantContext) -> dict:
    """Jembatani pesanan online yang SELESAI ke BigQuery (reuse `persist_basket`).

    Dipanggil dari `routes/orders.complete_order` tepat setelah status pindah ke
    `completed` — titik di mana barang benar-benar diserahkan ke pelanggan.
    Sebelum jembatan ini, penjualan jalur pesan-online tak pernah masuk BigQuery,
    padahal 11 analisis + /ask + /briefing + riwayat semuanya baca BigQuery — jadi
    omzet online ter-underreport total: hanya checkout kasir walk-in yang terhitung
    di top_product, revenue_trend, peak_hour, dst.

    Me-reuse `persist_basket` PERSIS seperti jalur walk-in, jadi penautan katalog
    (stock_code), penomoran invoice, dan validasi baris identik. `customer_user_id`
    (terisi hanya bila pelanggan kebetulan login saat memesan) menaut penjualan ke
    akun lewat riwayat produk loyalty — cermin `confirm_checkout`: best-effort,
    kegagalan loyalty tak membatalkan pencatatan penjualan.

    SELURUHNYA best-effort: pesanan SUDAH `completed` (barang sudah pindah tangan),
    jadi kegagalan BigQuery TIDAK boleh membatalkan penyelesaian — underreport satu
    pesanan jauh lebih ringan daripada memblokir tombol Selesai. Return hasil
    `persist_basket` (atau penanda dry_run/empty/bq_exception) untuk observabilitas.
    """
    if _dry_run_enabled():
        return {"status": "dry_run", "inserted": 0}

    items = [
        CheckoutLineItem(
            product=it["name"], qty=it["qty"],
            unit_price=it["unit_price"], total=it.get("subtotal"),
        )
        for it in (order.get("items") or [])
    ]
    if not items:
        return {"status": "empty", "inserted": 0}

    # ── SALE → BigQuery (seam yang sama dengan walk-in) ──
    # invoice=None → persist_basket auto-generate nomor invoice berikutnya.
    try:
        res = persist_basket(
            items, order.get("customer_name") or "", "Indonesia", None,
            tenant.table("transactions"), tenant.table("customers"),
            tenant_id=tenant.tenant_id,
        )
    except Exception as exc:  # BQ kredensial/jaringan — jangan patahkan completion
        return {"status": "bq_exception", "inserted": 0, "errors": [str(exc)]}

    # ── Tautan loyalty (SETELAH sale sukses, best-effort) ──
    cid = order.get("customer_user_id")
    if cid and res.get("status") == "ok":
        try:
            customer_repo.ensure_membership(cid, tenant.tenant_id)
            for it in items:
                product_repo.record_purchase(
                    cid, tenant.tenant_id, product_name=it.product,
                    amount=(it.total or it.qty * it.unit_price), count=1,
                )
        except Exception:
            pass  # loyalty tak pernah membatalkan pencatatan penjualan
    return res


def _rupiah(n: int) -> str:
    return ("Rp{:,.0f}".format(n)).replace(",", ".")


def _dry_run_enabled() -> bool:
    """CHECKOUT_DRY_RUN=true → validasi alur tanpa tulis BigQuery (cermin VOICE_DRY_RUN)."""
    return os.getenv("CHECKOUT_DRY_RUN", "false").lower() == "true"


def _earned_points(settings: dict, grand_total: int) -> int:
    """Hitung poin sesuai points_earning_rule tenant (REQUIREMENTS §6.4)."""
    rule = settings.get("points_earning_rule") or {}
    if rule.get("type") == "per_invoice":
        return int(rule.get("points_per_invoice", 1))
    per_amount = int(rule.get("points_per_amount", 10_000)) or 10_000
    return grand_total // per_amount


def _resolve_promo(req_promo_code: str | None, tenant_id: int) -> tuple[dict | None, str]:
    """Terima kode 'FTN-…' ATAU JWT QR promo. Return (promo, note_gagal)."""
    if not req_promo_code:
        return None, ""
    raw = req_promo_code.strip()
    promo = None
    if raw.count(".") == 2:  # bentuk JWT dari scan QR promo
        verified = verify_promo_qr(raw)
        if not verified["valid"]:
            return None, " (QR promo tidak valid/kedaluwarsa.)"
        promo = promo_repo.get_promo(verified["promo_id"])
    else:
        promo = promo_repo.get_promo_by_code(raw.upper())
    if promo is None:
        return None, " (Kode promo tidak ditemukan.)"
    if promo["tenant_id"] != tenant_id:
        return None, " (Promo bukan milik toko ini.)"
    if promo["status"] != "generated":
        return None, f" (Promo sudah {promo['status']}.)"
    return promo, ""


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
        tenant_id=tenant.tenant_id,
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
    points_earned = None
    promo_redeemed = None
    if qr is not None:  # QR valid + customer ada
        if consume_nonce(qr["nonce"], qr["expires_at"]):
            membership, is_new = customer_repo.ensure_membership(
                qr["customer_user_id"], tenant.tenant_id
            )
            customer_user_id = qr["customer_user_id"]
            is_new_member = is_new
            member_since = membership["member_since"]
            link_note = f" Pelanggan {qr_username} terhubung."

            # Earn points sesuai rule tenant (§6.4) — best-effort.
            try:
                settings = loyalty_repo.get_loyalty(tenant.tenant_id)
                pts = _earned_points(settings, grand_total)
                if pts > 0:
                    points_repo.add_entry(
                        customer_user_id, event_type="earn", points_delta=pts,
                        tenant_id=tenant.tenant_id, invoice=str(res["invoice"]),
                    )
                    points_earned = pts
                    link_note += f" +{pts} poin."
            except Exception:
                link_note += " (Poin gagal dicatat.)"

            # Riwayat belanja per-barang di akun pelanggan (Indomaret Point) —
            # best-effort; kegagalan tidak membatalkan checkout.
            try:
                for it in req.items:
                    product_repo.record_purchase(
                        customer_user_id, tenant.tenant_id,
                        product_name=it.product,
                        amount=(it.total or it.qty * it.unit_price),
                        count=1,
                    )
            except Exception:
                pass
        else:
            link_note = " (QR sudah dipakai — poin tidak terhubung.)"

    # ── Promo redemption (§7.6) — hanya bila kode/QR promo dikirim kasir ──
    if req.promo_code:
        promo, promo_note = _resolve_promo(req.promo_code, tenant.tenant_id)
        if promo is not None:
            redeemed = promo_repo.redeem_promo(promo["promo_id"], invoice=str(res["invoice"]))
            if redeemed is not None:
                promo_redeemed = redeemed["promo_id"]
                disc = _rupiah(redeemed["discount_amount"])
                link_note += f" Promo {redeemed['code']} ({disc}) dipakai."
            else:
                link_note += " (Promo gagal dipakai — sudah terpakai/kedaluwarsa.)"
        else:
            link_note += promo_note

    # ── Stock decrement (kasir = warning; best-effort SETELAH sale sukses) ──
    # Tak pernah membatalkan sale; item non-katalog/tak-dilacak dilewati oleh repo.
    try:
        stock_report = product_repo.apply_decrement(
            tenant.tenant_id, req.items, allow_oversell=True)
        for w in stock_report["warnings"]:
            link_note += " " + w
    except Exception:
        pass

    # Beri tahu kasir barang mana yang cocok dengan katalog Kelola Produk.
    matched = res.get("matched_products") or []
    if matched:
        link_note += (f" Produk terdaftar: {', '.join(matched)}."
                      if len(matched) > 1 else f" Produk terdaftar: {matched[0]}.")

    return CheckoutConfirmResponse(
        ok=True, status="ok", reply=base_reply + link_note,
        invoice=res["invoice"], item_count=item_count, grand_total=grand_total,
        customer_user_id=customer_user_id, is_new_member=is_new_member, member_since=member_since,
        points_earned=points_earned, promo_redeemed=promo_redeemed,
    )
