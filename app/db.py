"""Metadata DB (SQLite) untuk multi-tenant: tabel `tenants` + `users`.

Dipakai untuk auth & registry tenant. Data BISNIS (transaksi, customers) tetap
di BigQuery; SQLite ini HANYA untuk akun/tenant. Pakai stdlib sqlite3 (tanpa
dependency tambahan). Koneksi dibuka per-operasi (aman untuk thread FastAPI).
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any

DB_PATH = os.getenv("FORTUNAS_DB_PATH", "./app/data/fortunas.db")

# table_prefix dipakai langsung di nama tabel BigQuery (di-interpolasi ke SQL),
# jadi WAJIB dibatasi ke karakter aman untuk cegah injeksi.
_PREFIX_RE = re.compile(r"^[a-z][a-z0-9_]{1,30}$")


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                table_prefix TEXT NOT NULL UNIQUE,
                business_profile TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                tenant_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'admin',
                created_at TEXT NOT NULL,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            );
            """
        )


def is_valid_prefix(prefix: str) -> bool:
    return bool(_PREFIX_RE.match(prefix or ""))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ───────────────────────── Tenants ─────────────────────────


def create_tenant(name: str, table_prefix: str, business_profile: dict | None = None) -> int:
    if not is_valid_prefix(table_prefix):
        raise ValueError(
            "table_prefix tidak valid (huruf kecil/angka/underscore, mulai huruf, maks 31)."
        )
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO tenants (name, table_prefix, business_profile, created_at) "
            "VALUES (?, ?, ?, ?)",
            (name, table_prefix, json.dumps(business_profile or {}, ensure_ascii=False), _now()),
        )
        return int(cur.lastrowid)


def _row_to_tenant(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    d = dict(row)
    try:
        d["business_profile"] = json.loads(d.get("business_profile") or "{}")
    except (ValueError, TypeError):
        d["business_profile"] = {}
    return d


def get_tenant(tenant_id: int) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,)).fetchone()
    return _row_to_tenant(row)


def get_tenant_by_prefix(table_prefix: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM tenants WHERE table_prefix = ?", (table_prefix,)
        ).fetchone()
    return _row_to_tenant(row)


# ───────────────────────── Users ─────────────────────────


def create_user(email: str, password_hash: str, tenant_id: int, role: str = "admin") -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO users (email, password_hash, tenant_id, role, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (email.strip().lower(), password_hash, tenant_id, role, _now()),
        )
        return int(cur.lastrowid)


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
    return dict(row) if row else None
