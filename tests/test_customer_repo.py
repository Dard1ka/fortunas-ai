"""Repo customer + membership. SQLite in-memory (conftest)."""
from __future__ import annotations

from app import customer_repo, db


def _seed_tenant() -> int:
    return db.create_tenant(name="Toko A", table_prefix="toko_a")


def test_upsert_new_then_existing_no_clobber():
    cust, is_new = customer_repo.upsert_customer(
        firebase_uid="fb1", phone_number="+628", username="Budi", birth_date="1995-08-17")
    assert is_new is True
    assert cust["customer_user_id"].startswith("cu_")

    again, is_new2 = customer_repo.upsert_customer(
        firebase_uid="fb1", phone_number="+628", username="GANTI", birth_date="1990-01-01")
    assert is_new2 is False
    assert again["customer_user_id"] == cust["customer_user_id"]
    assert again["username"] == "Budi"  # tak di-clobber


def test_update_customer():
    cust, _ = customer_repo.upsert_customer(
        firebase_uid="fb2", phone_number="+628", username="Budi", birth_date="1995-08-17")
    updated = customer_repo.update_customer(cust["customer_user_id"], username="Budi S")
    assert updated["username"] == "Budi S"
    assert updated["birth_date"] == "1995-08-17"


def test_ensure_membership_idempotent():
    tenant_id = _seed_tenant()
    cust, _ = customer_repo.upsert_customer(
        firebase_uid="fb3", phone_number="+628", username="Budi", birth_date="1995-08-17")
    m, is_new = customer_repo.ensure_membership(cust["customer_user_id"], tenant_id)
    assert is_new is True
    assert m["member_since"]
    m2, is_new2 = customer_repo.ensure_membership(cust["customer_user_id"], tenant_id)
    assert is_new2 is False
    assert m2["id"] == m["id"]
    assert customer_repo.get_membership(cust["customer_user_id"], tenant_id)["tenant_id"] == tenant_id
