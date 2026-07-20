"""Promo generator: eligibility deterministik + spin wheel server-side + DPA guard.

REQUIREMENTS §6.5: backend memutuskan eligibility, biaya poin, produk favorit,
hasil spin (weighted random server-side), expiry, dan kepatuhan DPA — LLM hanya
copywriting (di MVP ini deterministik, tanpa panggilan LLM).

Favorite product (≥10 invoice berbeda) butuh BigQuery → dibungkus seam lazy
(pola checkout_service) dan best-effort: gagal → voucher random tanpa target.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app import dpa_repo, loyalty_repo, points_repo, promo_repo
from app.core.auth import JWT_ALGORITHM, JWT_SECRET
from app.services.dpa_guard import find_violations

FAVORITE_MIN_INVOICES = 10


class PromoEligibilityError(ValueError):
    """Customer tidak memenuhi syarat generate promo (pesan aman untuk user)."""


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


def spin_wheel(segments: list[dict]) -> dict:
    """Weighted random server-side (secrets = CSPRNG, tidak bisa ditebak klien)."""
    total = sum(s["probability"] for s in segments)
    roll = secrets.randbelow(1_000_000) / 1_000_000 * total
    acc = 0.0
    for seg in segments:
        acc += seg["probability"]
        if roll < acc:
            return seg
    return segments[-1]


def _bq_favorite_product(customer_username: str, tx_table: str,
                         customers_table: str) -> str | None:  # pragma: no cover
    """Produk yang dibeli customer di ≥10 invoice berbeda (terbanyak). Butuh BQ."""
    from google.cloud import bigquery

    from app.services.wa_pipeline_structured import resolve_customer_id
    cid = resolve_customer_id(customer_username, customers_table, tx_table)
    if cid is None:
        return None
    client = bigquery.Client()
    sql = f"""
        SELECT Description, COUNT(DISTINCT Invoice) AS invoices
        FROM `{tx_table}`
        WHERE `Customer ID` = @cid
        GROUP BY Description
        HAVING invoices >= {FAVORITE_MIN_INVOICES}
        ORDER BY invoices DESC
        LIMIT 1
    """
    job = client.query(sql, job_config=bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("cid", "INT64", cid)]))
    rows = list(job.result())
    return rows[0]["Description"] if rows else None


def favorite_product(customer_username: str, tx_table: str, customers_table: str) -> str | None:
    """Best-effort: kegagalan BQ tidak boleh menggagalkan generate promo."""
    try:
        return _bq_favorite_product(customer_username, tx_table, customers_table)
    except Exception:
        return None


def _promo_qr_payload(promo_id: str, expires_at: str) -> str:
    exp = datetime.fromisoformat(expires_at)
    return jwt.encode(
        {"promo_id": promo_id, "typ": "promo", "iat": _now_dt(), "exp": exp},
        JWT_SECRET, algorithm=JWT_ALGORITHM,
    )


def verify_promo_qr(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return {"valid": False, "reason": "expired"}
    except jwt.PyJWTError:
        return {"valid": False, "reason": "tampered"}
    if payload.get("typ") != "promo" or not payload.get("promo_id"):
        return {"valid": False, "reason": "tampered"}
    return {"valid": True, "promo_id": payload["promo_id"], "reason": None}


def generate_promo(
    *,
    customer_user_id: str,
    customer_username: str,
    tenant_id: int,
    tenant_name: str,
    tx_table: str | None = None,
    customers_table: str | None = None,
) -> dict:
    """Alur §6.5: cek membership→poin→DPA→favorit→spin→ledger→promo. Return {promo, spin_result}."""
    from app import customer_repo  # hindari import cycle di module load

    if customer_repo.get_membership(customer_user_id, tenant_id) is None:
        raise PromoEligibilityError(
            "Kamu belum menjadi pelanggan UMKM ini. Lakukan transaksi dulu.")

    settings = loyalty_repo.get_loyalty(tenant_id)
    min_points = settings["min_points_to_generate_promo"]
    balance = points_repo.get_balance(customer_user_id)
    if balance < min_points:
        raise PromoEligibilityError(
            f"Poin belum cukup: butuh {min_points}, saldo kamu {balance}.")

    # DPA guard: target produk & copy tidak boleh melanggar forbidden rules tenant.
    dpa = dpa_repo.get_dpa(tenant_id)
    forbidden = dpa.get("forbidden_rules") or []

    target = None
    if tx_table and customers_table:
        target = favorite_product(customer_username, tx_table, customers_table)
    if target and find_violations(target, forbidden):
        target = None  # produk favorit melanggar DPA → fallback voucher generik

    seg = spin_wheel(settings["spin_wheel"])
    amount = seg["discount_amount"]

    if target:
        name = f"Diskon Rp{amount:,} untuk {target}".replace(",", ".")
        description = (f"Voucher spesial {tenant_name}: potongan Rp{amount:,} "
                       f"untuk pembelian {target} favoritmu.").replace(",", ".")
    else:
        name = f"Voucher Diskon Rp{amount:,}".replace(",", ".")
        description = (f"Voucher {tenant_name}: potongan Rp{amount:,} "
                       f"untuk transaksi berikutnya.").replace(",", ".")
    if find_violations(name + " " + description, forbidden):
        raise PromoEligibilityError(
            "Promo tidak dapat dibuat karena melanggar kebijakan toko (DPA).")

    expires_at = (_now_dt() + timedelta(days=settings["promo_valid_days"])
                  ).isoformat(timespec="seconds")

    promo = promo_repo.create_promo(
        customer_user_id=customer_user_id,
        tenant_id=tenant_id,
        name=name,
        description=description,
        discount_amount=amount,
        target_product=target,
        points_cost=min_points,
        expires_at=expires_at,
    )
    # Deduct SETELAH promo tercatat; promo_id jadi jejak audit di ledger.
    points_repo.add_entry(
        customer_user_id, event_type="redeem", points_delta=-min_points,
        tenant_id=tenant_id, promo_id=promo["promo_id"],
    )
    promo["qr_payload"] = _promo_qr_payload(promo["promo_id"], expires_at)
    return {"promo": promo, "spin_result": seg}
