"""Migrate script: no-source no-op + happy path dari SQLite lama → target."""
from __future__ import annotations

import sqlite3

from sqlalchemy import select

from app.db_pg import SessionLocal
from app.models import Tenant, TenantUser
from scripts.migrate_sqlite_to_pg import migrate


def test_migrate_no_source_is_noop():
    summary = migrate("./does_not_exist_12345.db")
    assert summary == {"tenants": 0, "users": 0, "skipped_tenants": 0, "skipped_users": 0}


def test_migrate_copies_rows(tmp_path):
    old = tmp_path / "old.db"
    conn = sqlite3.connect(old)
    conn.executescript(
        """
        CREATE TABLE tenants (id INTEGER PRIMARY KEY, name TEXT, table_prefix TEXT,
            business_profile TEXT, created_at TEXT);
        CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, password_hash TEXT,
            tenant_id INTEGER, role TEXT, created_at TEXT);
        INSERT INTO tenants VALUES (1,'Lama','lama','{"x":1}','2026-01-01T00:00:00+00:00');
        INSERT INTO users VALUES (1,'a@lama.com','h',1,'admin','2026-01-01T00:00:00+00:00');
        """
    )
    conn.commit()
    conn.close()

    summary = migrate(str(old))
    assert summary["tenants"] == 1
    assert summary["users"] == 1

    with SessionLocal() as s:
        t = s.scalar(select(Tenant).where(Tenant.table_prefix == "lama"))
        assert t is not None and t.business_profile == {"x": 1}
        u = s.scalar(select(TenantUser).where(TenantUser.email == "a@lama.com"))
        assert u is not None and u.tenant_id == t.id


def test_migrate_idempotent_skips_existing(tmp_path):
    old = tmp_path / "old2.db"
    conn = sqlite3.connect(old)
    conn.executescript(
        """
        CREATE TABLE tenants (id INTEGER PRIMARY KEY, name TEXT, table_prefix TEXT,
            business_profile TEXT, created_at TEXT);
        CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, password_hash TEXT,
            tenant_id INTEGER, role TEXT, created_at TEXT);
        INSERT INTO tenants VALUES (1,'Dup','dup','{}','2026-01-01T00:00:00+00:00');
        INSERT INTO users VALUES (1,'d@dup.com','h',1,'admin','2026-01-01T00:00:00+00:00');
        """
    )
    conn.commit()
    conn.close()

    migrate(str(old))
    summary2 = migrate(str(old))  # run kedua
    assert summary2["skipped_tenants"] == 1
    assert summary2["skipped_users"] == 1
    assert summary2["tenants"] == 0
