from app.prompt_builder import build_llm_prompt, build_llm_prompt_with_rag

_ROWS = [{"customer_id": "1", "total_orders": 5}]


def test_prompt_no_dpa_has_no_constraint_block():
    p = build_llm_prompt("q", "repeat_customer", _ROWS)
    assert "ATURAN WAJIB" not in p


def test_prompt_with_dpa_injects_constraint():
    dpa = {"raw_text": "tidak jual rokok", "forbidden_rules": ["rokok"], "allowed_rules": []}
    p = build_llm_prompt("q", "repeat_customer", _ROWS, dpa_policy=dpa)
    assert "ATURAN WAJIB" in p
    assert "rokok" in p
    assert "tidak jual rokok" in p


def test_prompt_with_rag_injects_constraint():
    dpa = {"raw_text": "", "forbidden_rules": ["tembakau"], "allowed_rules": []}
    p = build_llm_prompt_with_rag("q", "repeat_customer", _ROWS, rag_context=["k"], dpa_policy=dpa)
    assert "ATURAN WAJIB" in p
    assert "tembakau" in p


def test_empty_dpa_no_block():
    dpa = {"raw_text": "", "forbidden_rules": [], "allowed_rules": []}
    p = build_llm_prompt("q", "repeat_customer", _ROWS, dpa_policy=dpa)
    assert "ATURAN WAJIB" not in p
