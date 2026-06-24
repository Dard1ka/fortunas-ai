"""db_pg: engine terbentuk dari DATABASE_URL dan bisa eksekusi query."""
from __future__ import annotations

from sqlalchemy import text

from app.db_pg import SessionLocal, engine


def test_engine_uses_test_database_url():
    # conftest memaksa sqlite:// (in-memory) untuk test.
    assert engine.url.get_backend_name() == "sqlite"


def test_session_executes_select_one():
    with SessionLocal() as s:
        assert s.execute(text("SELECT 1")).scalar() == 1
