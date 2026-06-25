"""TDD dpa_repo: round-trip DPA policy di SQLite in-memory."""
from __future__ import annotations

from app import dpa_repo


def test_get_dpa_default_when_absent():
    d = dpa_repo.get_dpa(999)
    assert d["version"] == 0
    assert d["raw_text"] == ""
    assert d["allowed_rules"] == []
    assert d["forbidden_rules"] == []
    assert d["policy_summary"] is None
    assert d["verified_at"] is None
    assert d["updated_at"] is None


def test_upsert_creates_version_1():
    d = dpa_repo.upsert_dpa(
        1, raw_text="tidak jual rokok",
        allowed_rules=["diskon makanan"], forbidden_rules=["rokok", "tembakau"],
    )
    assert d["version"] == 1
    assert d["raw_text"] == "tidak jual rokok"
    assert d["forbidden_rules"] == ["rokok", "tembakau"]
    assert d["allowed_rules"] == ["diskon makanan"]
    assert d["updated_at"] == d["verified_at"]
    assert "T" in d["updated_at"]


def test_upsert_again_increments_and_persists():
    dpa_repo.upsert_dpa(7, raw_text="a", allowed_rules=[], forbidden_rules=["x"])
    d2 = dpa_repo.upsert_dpa(7, raw_text="b", allowed_rules=["ok"], forbidden_rules=["y", "z"])
    assert d2["version"] == 2
    assert d2["raw_text"] == "b"
    assert d2["forbidden_rules"] == ["y", "z"]
    got = dpa_repo.get_dpa(7)
    assert got["version"] == 2
    assert got["raw_text"] == "b"
    assert got["allowed_rules"] == ["ok"]
