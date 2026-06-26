import pytest

from app.intent_mapper import map_question_to_analysis


@pytest.mark.parametrize(
    "question",
    [
        "produk terlaris apa?",
        "barang paling laku",
        "omzet per produk",
        "produk yang paling banyak terjual",
        "best seller toko saya",
    ],
)
def test_top_product_positives(question):
    assert map_question_to_analysis(question) == "top_product"


def test_bundle_not_stolen_by_top_product():
    assert map_question_to_analysis("produk yang sering dibeli bersama") == "bundle_opportunity"


def test_existing_intents_regression():
    assert map_question_to_analysis("siapa pelanggan loyal saya") == "repeat_customer"
    assert map_question_to_analysis("siapa customer paling bernilai") == "high_value_customer"
    assert map_question_to_analysis("jam berapa transaksi paling ramai") == "peak_hour"
    assert map_question_to_analysis("barang apa yang cocok dibundling") == "bundle_opportunity"


def test_unknown_for_unrelated():
    assert map_question_to_analysis("") == "unknown"
    assert map_question_to_analysis("apa kabar hari ini") == "unknown"
