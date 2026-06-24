"""Test infra: paksa SQLite in-memory sebelum modul app meng-import db_pg.

Fixture skema fresh ditambahkan di Task 4 (setelah models ada).
"""
from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite://"  # in-memory; harus diset sebelum import app.db_pg
