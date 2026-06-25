"""Integration run_ask Pre+Post DPA (fake agent, monkeypatch execute_analysis — no BQ/Gemini)."""
from __future__ import annotations

from app import dpa_repo
from app.core.tenancy import TenantContext
from app.services import pipeline
from app.services.pipeline import run_ask

_BUNDLE_ROWS = [
    {"product_A": "Kopi", "product_B": "Roti", "bundle_frequency": 10},
    {"product_A": "Teh", "product_B": "Donat", "bundle_frequency": 7},
    {"product_A": "Susu", "product_B": "Pisang", "bundle_frequency": 5},
]


class FakeInsightAgent:
    def __init__(self, output: dict):
        self._output = output
        self.called = False

    def generate(self, **kwargs):
        self.called = True
        return {"llm_output": self._output, "rag_context": [], "data_confidence": "high"}


def _ctx(tenant_id: int) -> TenantContext:
    return TenantContext(
        tenant_id=tenant_id, name="Toko Sehat", table_prefix="tokosehat",
        business_profile={}, email="o@x.com",
    )


def _clean_output() -> dict:
    return {
        "summary": "Pasangan produk aman.",
        "top_findings": ["Kopi + Roti"],
        "recommendation": ["Bundling ringan."],
        "data_confidence": "high",
    }


def test_no_dpa_passes_through(monkeypatch):
    monkeypatch.setattr(pipeline, "execute_analysis", lambda *a, **k: (_BUNDLE_ROWS, None))
    agent = FakeInsightAgent(_clean_output())
    result = run_ask("produk yang sering dibeli bersama", agent, None, _ctx(1))
    assert result["status"] == "success"
    assert result["llm_output"] is not None
    assert agent.called is True
    assert result["rows"] == _BUNDLE_ROWS


def test_pre_block_short_circuits(monkeypatch):
    calls = {"n": 0}

    def spy(*a, **k):
        calls["n"] += 1
        return (_BUNDLE_ROWS, None)

    monkeypatch.setattr(pipeline, "execute_analysis", spy)
    dpa_repo.upsert_dpa(2, raw_text="tidak jual rokok", allowed_rules=[], forbidden_rules=["rokok"])
    agent = FakeInsightAgent(_clean_output())
    result = run_ask("kasih ide promo rokok murah", agent, None, _ctx(2))
    assert result["status"] == "refused"
    assert result["rows"] == []
    assert result["llm_output"] is None
    assert agent.called is False        # Gemini tak dipanggil
    assert calls["n"] == 0              # BigQuery tak dipanggil


def test_post_block_suppresses_output_keeps_rows(monkeypatch):
    monkeypatch.setattr(pipeline, "execute_analysis", lambda *a, **k: (_BUNDLE_ROWS, None))
    dpa_repo.upsert_dpa(3, raw_text="tidak jual rokok", allowed_rules=[], forbidden_rules=["rokok"])
    bad = {"summary": "Coba bundling rokok dan korek.", "top_findings": [],
           "recommendation": [], "data_confidence": "high"}
    agent = FakeInsightAgent(bad)
    result = run_ask("produk yang sering dibeli bersama", agent, None, _ctx(3))
    assert result["status"] == "refused"
    assert result["llm_output"] is None
    assert result["rows"] == _BUNDLE_ROWS   # data faktual tetap ada
    assert agent.called is True
