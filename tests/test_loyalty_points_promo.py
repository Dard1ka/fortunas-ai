"""Tests loyalty settings, points ledger, dan promo generator (offline, in-memory DB)."""
from __future__ import annotations

import pytest

from app import customer_repo, db, loyalty_repo, points_repo, promo_repo
from app.schemas import LoyaltySettings
from app.services.promo_service import (
    PromoEligibilityError,
    generate_promo,
    spin_wheel,
    verify_promo_qr,
)


def _seed_customer_and_tenant() -> tuple[str, int]:
    tenant_id = db.create_tenant("Kopi Tuku", "kopi_tuku")
    cust, _ = customer_repo.upsert_customer(
        firebase_uid="fb_test_1", phone_number="+628123",
        username="andi", birth_date="2000-01-01")
    return cust["customer_user_id"], tenant_id


# ── Loyalty settings ─────────────────────────────────────────────

def test_loyalty_defaults_when_missing():
    tenant_id = db.create_tenant("Toko A", "toko_a")
    s = loyalty_repo.get_loyalty(tenant_id)
    assert s["min_points_to_generate_promo"] == 30
    assert s["promo_valid_days"] == 7
    assert abs(sum(seg["probability"] for seg in s["spin_wheel"]) - 1.0) < 0.001


def test_loyalty_put_roundtrip():
    tenant_id = db.create_tenant("Toko B", "toko_b")
    new = LoyaltySettings(min_points_to_generate_promo=50, promo_valid_days=3)
    loyalty_repo.put_loyalty(tenant_id, new)
    got = loyalty_repo.get_loyalty(tenant_id)
    assert got["min_points_to_generate_promo"] == 50
    assert got["promo_valid_days"] == 3


def test_loyalty_rejects_bad_probabilities():
    with pytest.raises(ValueError):
        LoyaltySettings(spin_wheel=[{"discount_amount": 1000, "probability": 0.5}])


# ── Points ledger ────────────────────────────────────────────────

def test_points_earn_and_balance():
    cid, tenant_id = _seed_customer_and_tenant()
    res = points_repo.add_entry(cid, event_type="earn", points_delta=5,
                                tenant_id=tenant_id, invoice="100")
    assert res["balance"] == 5
    assert points_repo.get_balance(cid) == 5
    entries = points_repo.recent_entries(cid)
    assert entries[0]["event_type"] == "earn"
    assert entries[0]["points_delta"] == 5


def test_points_cannot_go_negative():
    cid, _ = _seed_customer_and_tenant()
    with pytest.raises(ValueError):
        points_repo.add_entry(cid, event_type="redeem", points_delta=-10)


# ── Spin wheel ───────────────────────────────────────────────────

def test_spin_wheel_returns_valid_segment():
    segments = [{"discount_amount": 10_000, "probability": 0.6},
                {"discount_amount": 100_000, "probability": 0.4}]
    for _ in range(50):
        seg = spin_wheel(segments)
        assert seg["discount_amount"] in (10_000, 100_000)


# ── Promo generate ───────────────────────────────────────────────

def test_generate_promo_requires_membership():
    cid, tenant_id = _seed_customer_and_tenant()
    with pytest.raises(PromoEligibilityError, match="belum menjadi pelanggan"):
        generate_promo(customer_user_id=cid, customer_username="andi",
                       tenant_id=tenant_id, tenant_name="Kopi Tuku")


def test_generate_promo_requires_points():
    cid, tenant_id = _seed_customer_and_tenant()
    customer_repo.ensure_membership(cid, tenant_id)
    with pytest.raises(PromoEligibilityError, match="Poin belum cukup"):
        generate_promo(customer_user_id=cid, customer_username="andi",
                       tenant_id=tenant_id, tenant_name="Kopi Tuku")


def test_generate_promo_happy_path_deducts_points():
    cid, tenant_id = _seed_customer_and_tenant()
    customer_repo.ensure_membership(cid, tenant_id)
    points_repo.add_entry(cid, event_type="earn", points_delta=30, tenant_id=tenant_id)

    result = generate_promo(customer_user_id=cid, customer_username="andi",
                            tenant_id=tenant_id, tenant_name="Kopi Tuku")
    promo = result["promo"]
    assert promo["status"] == "generated"
    assert promo["points_cost"] == 30
    assert promo["discount_amount"] == result["spin_result"]["discount_amount"]
    assert points_repo.get_balance(cid) == 0
    # QR payload valid & merefer promo yang sama
    verified = verify_promo_qr(promo["qr_payload"])
    assert verified["valid"] and verified["promo_id"] == promo["promo_id"]


def test_promo_redeem_lifecycle():
    cid, tenant_id = _seed_customer_and_tenant()
    customer_repo.ensure_membership(cid, tenant_id)
    points_repo.add_entry(cid, event_type="earn", points_delta=30, tenant_id=tenant_id)
    promo = generate_promo(customer_user_id=cid, customer_username="andi",
                           tenant_id=tenant_id, tenant_name="Kopi Tuku")["promo"]

    redeemed = promo_repo.redeem_promo(promo["promo_id"], invoice="555")
    assert redeemed is not None and redeemed["status"] == "redeemed"
    assert redeemed["redeemed_invoice"] == "555"
    # Redeem kedua kali harus gagal (anti-replay)
    assert promo_repo.redeem_promo(promo["promo_id"], invoice="556") is None
