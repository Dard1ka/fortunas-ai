from app.prompt_builder import build_llm_prompt

ROWS = [
    {"description": "KOPI SACHET", "total_qty": 500, "total_omzet": 1250000.0},
    {"description": "GULA 1KG", "total_qty": 300, "total_omzet": 900000.0},
    {"description": "TEH CELUP", "total_qty": 200, "total_omzet": 400000.0},
]


def test_top_product_prompt_mentions_omzet_and_explanation():
    prompt = build_llm_prompt("produk terlaris apa", "top_product", ROWS)
    assert "total_omzet" in prompt
    assert "produk dengan kontribusi omzet tertinggi" in prompt
