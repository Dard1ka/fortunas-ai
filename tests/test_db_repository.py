"""TDD lapisan DB: round-trip tenant/user di SQLite in-memory (lewat wrapper db.py)."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import db
from app.db_pg import SessionLocal
from app.models import TenantSettings


def test_create_and_get_tenant_roundtrip():
    tid = db.create_tenant("Kopi Budi", "kopibudi", {"jenis": "kafe"})
    t = db.get_tenant(tid)
    assert t is not None
    assert t["name"] == "Kopi Budi"
    assert t["table_prefix"] == "kopibudi"
    assert t["business_profile"] == {"jenis": "kafe"}
    assert t["created_at"]  # ISO string terisi


def test_get_tenant_by_prefix():
    db.create_tenant("Toko A", "tokoa")
    assert db.get_tenant_by_prefix("tokoa")["name"] == "Toko A"
    assert db.get_tenant_by_prefix("nope") is None


def test_create_tenant_seeds_default_loyalty_settings():
    tid = db.create_tenant("Warung", "warung")
    with SessionLocal() as s:
        settings = s.get(TenantSettings, tid)
    assert settings is not None
    assert settings.loyalty["min_points_to_generate_promo"] == 30
    total = sum(seg["probability"] for seg in settings.loyalty["spin_wheel"])
    assert abs(total - 1.0) < 1e-6


def test_invalid_prefix_rejected():
    with pytest.raises(ValueError):
        db.create_tenant("Bad", "1bad")  # mulai angka → invalid


def test_create_user_and_lookup_lowercases_email():
    tid = db.create_tenant("Biz", "biz")
    uid = db.create_user("OWNER@Biz.com", "hash123", tid)
    u = db.get_user_by_email("owner@biz.com")
    assert u["id"] == uid
    assert u["email"] == "owner@biz.com"
    assert u["password_hash"] == "hash123"
    assert u["tenant_id"] == tid


def test_duplicate_email_violates_unique():
    tid = db.create_tenant("Biz2", "biz2")
    db.create_user("dup@biz.com", "h", tid)
    with pytest.raises(IntegrityError):
        db.create_user("dup@biz.com", "h2", tid)


def test_duplicate_prefix_violates_unique():
    db.create_tenant("One", "samepref")
    with pytest.raises(IntegrityError):
        db.create_tenant("Two", "samepref")


def test_select_smoke_after_create():
    db.create_tenant("Smoke", "smoke")
    with SessionLocal() as s:
        from app.models import Tenant
        names = s.scalars(select(Tenant.name)).all()
    assert "Smoke" in names
