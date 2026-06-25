"""Pastikan 7 tabel metadata-store terdefinisi dengan kolom sesuai kontrak."""
from __future__ import annotations

from app import models  # noqa: F401 — registrasi tabel ke Base.metadata
from app.db_pg import Base


def test_seven_tables_registered():
    expected = {
        "tenants", "tenant_users", "tenant_settings", "customer_users",
        "customer_tenant_memberships", "tenant_dpa_policies", "device_tokens",
    }
    assert expected <= set(Base.metadata.tables)


def test_tenant_users_columns():
    cols = set(Base.metadata.tables["tenant_users"].columns.keys())
    assert {"id", "email", "password_hash", "tenant_id", "role", "created_at"} <= cols


def test_tenant_settings_matches_loyalty_contract():
    cols = set(Base.metadata.tables["tenant_settings"].columns.keys())
    assert {"tenant_id", "loyalty", "created_at", "updated_at"} <= cols


def test_customer_users_matches_profile_contract():
    cols = set(Base.metadata.tables["customer_users"].columns.keys())
    assert {"customer_user_id", "firebase_uid", "username", "phone_number",
            "birth_date", "created_at"} <= cols


def test_dpa_matches_contract():
    cols = set(Base.metadata.tables["tenant_dpa_policies"].columns.keys())
    assert {"raw_text", "allowed_rules", "forbidden_rules", "policy_summary",
            "version", "verified_at", "updated_at"} <= cols


def test_membership_unique_constraint_exists():
    t = Base.metadata.tables["customer_tenant_memberships"]
    uniques = [c for c in t.constraints if c.__class__.__name__ == "UniqueConstraint"]
    cols_sets = [set(c.columns.keys()) for c in uniques]
    assert {"customer_user_id", "tenant_id"} in cols_sets


def test_qr_nonces_registered_and_roundtrip():
    from app.db_pg import SessionLocal
    from app.models import QRNonce

    assert "qr_nonces" in Base.metadata.tables
    with SessionLocal() as s:
        s.add(QRNonce(nonce="abc", expires_at="2999-01-01T00:00:00+00:00",
                      created_at="2026-06-25T00:00:00+00:00"))
        s.commit()
    with SessionLocal() as s:
        row = s.get(QRNonce, "abc")
        assert row is not None
        assert row.expires_at.startswith("2999")
