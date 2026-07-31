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


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    """Kosongkan penampung rate limit order publik sebelum tiap test.

    `public._order_hits` adalah state module-level yang hidup selama proses, dan
    `TestClient` selalu memakai host `testclient` — tanpa reset ini SELURUH suite
    berbagi satu ember 10-per-60-detik, jadi POST order ke-11 mana pun di satu
    sesi pytest balas 429 dan test yang tumbang bergantung pada urutan koleksi
    pytest. Import di dalam fungsi supaya permukaan import-time conftest tidak
    tumbuh (lihat Global Constraints soal dep minimal CI).
    """
    from app.api.routes import public

    public._order_hits.clear()
    yield
