"""Test infra: paksa SQLite in-memory sebelum modul app meng-import db_pg.

Fixture skema fresh ditambahkan di Task 4 (setelah models ada).
"""
from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite://"  # in-memory; harus diset sebelum import app.db_pg

import pytest  # noqa: E402

from app import models  # noqa: E402,F401 — registrasi tabel
from app.db_pg import Base, engine  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_schema():
    """Skema fresh per test (in-memory)."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
