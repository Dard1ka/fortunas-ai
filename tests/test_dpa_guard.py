from app.services import dpa_guard


def test_normalize_rules_trims_lowercases_dedupes():
    assert dpa_guard.normalize_rules([" Rokok ", "rokok", "", "Tembakau"]) == ["rokok", "tembakau"]


def test_find_violations_case_insensitive():
    assert dpa_guard.find_violations("Mau PROMO Rokok murah", ["rokok"]) == ["rokok"]


def test_find_violations_word_boundary_no_false_positive():
    # 'babi' menempel di 'kababil' → bukan pelanggaran (word boundary)
    assert dpa_guard.find_violations("beli kababil", ["babi"]) == []
    assert dpa_guard.find_violations("sate babi enak", ["babi"]) == ["babi"]


def test_find_violations_multiword_phrase():
    assert dpa_guard.find_violations("jual daging babi segar", ["daging babi"]) == ["daging babi"]


def test_find_violations_empty_inputs():
    assert dpa_guard.find_violations("", ["rokok"]) == []
    assert dpa_guard.find_violations("apa saja", []) == []
    assert dpa_guard.find_violations("apa saja", None) == []


def test_check_answer_scans_all_fields():
    out = {"summary": "Top produk aman", "top_findings": ["ada rokok di sini"], "recommendation": []}
    assert dpa_guard.check_answer(out, ["rokok"]) == ["rokok"]


def test_check_answer_none_safe():
    assert dpa_guard.check_answer(None, ["rokok"]) == []


def test_build_refusal_mentions_topic_and_tenant():
    msg = dpa_guard.build_refusal(["rokok"], tenant_name="Toko Sehat")
    assert "rokok" in msg
    assert "Toko Sehat" in msg
