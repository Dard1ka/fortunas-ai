"""Copy data metadata-store dari SQLite lama → target DATABASE_URL (Postgres).

Defensif: file SQLite tak ada / tak ada tabel tenants&users → no-op, exit 0.
Idempotent: lewati email/table_prefix yang sudah ada di target.
Pakai:
    DATABASE_URL=postgresql+psycopg2://... python scripts/migrate_sqlite_to_pg.py [sqlite_path]
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

from sqlalchemy import select

from app.db_pg import Base, SessionLocal, engine
from app.models import Tenant, TenantSettings, TenantUser
from app.schemas import LoyaltySettings


def migrate(sqlite_path: str) -> dict[str, int]:
    summary = {"tenants": 0, "users": 0, "skipped_tenants": 0, "skipped_users": 0}
    if not os.path.exists(sqlite_path):
        print(f"[migrate] SQLite '{sqlite_path}' tidak ada -> nothing to migrate.")
        return summary

    Base.metadata.create_all(bind=engine)  # pastikan tabel target ada
    src = sqlite3.connect(sqlite_path)
    src.row_factory = sqlite3.Row
    try:
        tables = {
            r["name"]
            for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if "tenants" not in tables and "users" not in tables:
            print("[migrate] Tak ada tabel tenants/users di source -> nothing to migrate.")
            return summary

        with SessionLocal() as s:
            old_to_new: dict[int, int] = {}
            if "tenants" in tables:
                for row in src.execute("SELECT * FROM tenants"):
                    existing = s.scalar(
                        select(Tenant).where(Tenant.table_prefix == row["table_prefix"])
                    )
                    if existing:
                        old_to_new[row["id"]] = existing.id
                        summary["skipped_tenants"] += 1
                        continue
                    try:
                        bp = json.loads(row["business_profile"] or "{}")
                    except (ValueError, TypeError):
                        bp = {}
                    t = Tenant(
                        name=row["name"],
                        table_prefix=row["table_prefix"],
                        business_profile=bp,
                        created_at=row["created_at"],
                    )
                    s.add(t)
                    s.flush()
                    old_to_new[row["id"]] = t.id
                    s.add(
                        TenantSettings(
                            tenant_id=t.id,
                            loyalty=LoyaltySettings().model_dump(),
                            created_at=row["created_at"],
                            updated_at=row["created_at"],
                        )
                    )
                    summary["tenants"] += 1
            if "users" in tables:
                for row in src.execute("SELECT * FROM users"):
                    if s.scalar(select(TenantUser).where(TenantUser.email == row["email"])):
                        summary["skipped_users"] += 1
                        continue
                    new_tid = old_to_new.get(row["tenant_id"])
                    if new_tid is None:
                        # Tenant tak ter-resolusi (orphan / tabel tenants tak ada) -> lewati defensif.
                        summary["skipped_users"] += 1
                        continue
                    s.add(
                        TenantUser(
                            email=row["email"],
                            password_hash=row["password_hash"],
                            tenant_id=new_tid,
                            role=row["role"],
                            created_at=row["created_at"],
                        )
                    )
                    summary["users"] += 1
            s.commit()
    finally:
        src.close()
    print(f"[migrate] done: {summary}")
    return summary


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.getenv(
        "FORTUNAS_DB_PATH", "./app/data/fortunas.db"
    )
    migrate(path)
