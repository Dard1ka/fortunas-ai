from app.services.pipeline import (
    build_deterministic_executive_summary,
    enabled_analyses,
)


def test_top_product_enabled_in_briefing():
    keys = [key for key, _ in enabled_analyses()]
    assert "top_product" in keys


def test_exec_summary_includes_top_product():
    sections = [
        {
            "analysis_type": "top_product",
            "status": "success",
            "summary": "Produk A juara omzet.",
        },
    ]
    out = build_deterministic_executive_summary(sections)
    assert "Produk A juara omzet." in out
