from app.agents.insight_agent import InsightAgent

_ROWS = [{"customer_id": "1", "total_orders": 5}]


def test_build_prompt_threads_dpa_policy():
    agent = InsightAgent(rag_agent=None)
    dpa = {"raw_text": "tidak jual rokok", "forbidden_rules": ["rokok"], "allowed_rules": []}
    prompt = agent.build_prompt(
        question="q", analysis_key="repeat_customer", rows=_ROWS, rag_context=[], dpa_policy=dpa,
    )
    assert "ATURAN WAJIB" in prompt
    assert "rokok" in prompt


def test_build_prompt_without_dpa_no_block():
    agent = InsightAgent(rag_agent=None)
    prompt = agent.build_prompt(
        question="q", analysis_key="repeat_customer", rows=_ROWS, rag_context=[],
    )
    assert "ATURAN WAJIB" not in prompt
