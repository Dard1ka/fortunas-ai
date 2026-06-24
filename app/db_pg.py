"""SQLAlchemy engine + session + Base untuk metadata-store.

DATABASE_URL default ke SQLite (perilaku lama tetap jalan kalau env tak diset);
set ke postgresql+psycopg2://... untuk cutover. Baca env langsung (bukan via
config.get_settings) untuk hindari import-cycle.
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app/data/fortunas.db")

_connect_args: dict = {}
_engine_kwargs: dict = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
    # In-memory (test) butuh StaticPool agar satu DB dibagi lintas koneksi.
    if DATABASE_URL in ("sqlite://", "sqlite:///:memory:"):
        _engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, connect_args=_connect_args, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()
