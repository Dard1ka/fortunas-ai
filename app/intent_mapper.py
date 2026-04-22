import re


def normalize_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


INTENT_CONFIG = {
    "repeat_customer": {
        "strong_phrases": [
            "siapa customer yang paling sering beli",
            "siapa pelanggan yang paling sering beli",
            "siapa pelanggan loyal saya",
            "siapa customer loyal saya",
            "pelanggan loyal",
            "customer loyal",
            "repeat customer",
            "repeat order",
            "customer yang paling sering transaksi",
            "pelanggan yang paling sering transaksi",
            "customer yang paling sering beli",
            "pelanggan yang paling sering beli",
            "pelanggan mana yang paling sering belanja",
            "siapa pembeli paling loyal",
            "siapa pelanggan yang sering belanja",
        ],
        "keywords": [
            "loyal",
            "repeat",
            "sering beli",
            "sering transaksi",
            "transaksi terbanyak",
            "pelanggan tetap",
            "sering belanja",
        ],
    },
    "high_value_customer": {
        "strong_phrases": [
            "siapa customer yang paling bernilai",
            "siapa pelanggan yang paling bernilai",
            "customer paling bernilai",
            "pelanggan paling bernilai",
            "customer dengan total belanja terbesar",
            "pelanggan dengan total belanja terbesar",
            "customer dengan belanja terbesar",
            "pelanggan dengan belanja terbesar",
            "customer dengan spending tertinggi",
            "pelanggan dengan spending tertinggi",
            "customer dengan total spending tertinggi",
            "pelanggan dengan total spending tertinggi",
            "customer dengan nilai belanja tertinggi",
            "pelanggan dengan nilai belanja tertinggi",
            "high value customer",
            "siapa pembeli dengan nilai transaksi paling besar",
            "pelanggan mana yang belanjanya paling besar",
        ],
        "keywords": [
            "bernilai",
            "total belanja",
            "belanja terbesar",
            "spending tertinggi",
            "nilai belanja tertinggi",
            "total spending",
            "high value",
            "nilai transaksi",
            "belanja paling besar",
        ],
    },
    "peak_hour": {
        "strong_phrases": [
            "jam berapa transaksi paling ramai",
            "jam transaksi paling ramai",
            "kapan customer paling sering checkout",
            "kapan pelanggan paling sering checkout",
            "jam checkout paling ramai",
            "jam paling ramai",
            "jam paling sibuk",
            "kapan transaksi paling sering",
            "waktu transaksi paling ramai",
            "peak hour",
            "jam belanja paling padat",
            "jam belanja paling ramai",
            "kapan pembeli paling ramai",
        ],
        "keywords": [
            "checkout",
            "jam ramai",
            "jam sibuk",
            "transaksi paling ramai",
            "transaksi paling sering",
            "waktu ramai",
            "peak hour",
            "jam belanja",
            "padat",
        ],
    },
    "bundle_opportunity": {
        "strong_phrases": [
            "produk apa yang sering dibeli bersama",
            "barang apa yang cocok dibundling",
            "produk yang cocok dibundling",
            "barang yang cocok dibundling",
            "sering dibeli bersama",
            "sering dibeli bareng",
            "produk yang dibeli bersama",
            "bundle opportunity",
            "cross sell",
            "produk yang cocok untuk bundle",
            "produk mana yang paling cocok dijual paket",
            "barang yang sering laku bareng",
            "produk yang sering laku bareng",
        ],
        "keywords": [
            "dibundling",
            "bundling",
            "bundle",
            "dibeli bersama",
            "dibeli bareng",
            "cross sell",
            "produk pasangan",
            "produk pelengkap",
            "jual paket",
            "laku bareng",
        ],
    },
}


def _score_intent(normalized_question: str, intent_key: str) -> int:
    config = INTENT_CONFIG[intent_key]
    score = 0

    for phrase in config["strong_phrases"]:
        if phrase in normalized_question:
            score += 8

    for keyword in config["keywords"]:
        if keyword in normalized_question:
            score += 3

    tokens = set(normalized_question.split())

    if intent_key == "repeat_customer":
        if ("customer" in tokens or "pelanggan" in tokens or "pembeli" in tokens) and (
            "loyal" in tokens or "repeat" in tokens or "sering" in tokens or "tetap" in tokens
        ):
            score += 4
        if "transaksi" in tokens and ("terbanyak" in tokens or "sering" in tokens):
            score += 3

    elif intent_key == "high_value_customer":
        if ("customer" in tokens or "pelanggan" in tokens or "pembeli" in tokens) and (
            "bernilai" in tokens or "spending" in tokens or "belanja" in tokens
        ):
            score += 4
        if "total" in tokens and "belanja" in tokens:
            score += 4
        if "terbesar" in tokens and ("belanja" in tokens or "spending" in tokens or "nilai" in tokens):
            score += 4
        if "tertinggi" in tokens and ("belanja" in tokens or "spending" in tokens):
            score += 4

    elif intent_key == "peak_hour":
        if "checkout" in tokens:
            score += 4
        if "jam" in tokens and ("ramai" in tokens or "sibuk" in tokens or "padat" in tokens):
            score += 4
        if "transaksi" in tokens and ("ramai" in tokens or "sering" in tokens):
            score += 4
        if "belanja" in tokens and ("padat" in tokens or "ramai" in tokens):
            score += 4

    elif intent_key == "bundle_opportunity":
        if "bundling" in normalized_question or "dibundling" in normalized_question:
            score += 5
        if "dibeli bersama" in normalized_question or "dibeli bareng" in normalized_question:
            score += 5
        if "bundle" in tokens or "cross" in tokens or "sell" in tokens:
            score += 2
        if "paket" in tokens or "bareng" in tokens:
            score += 2

    return score


def map_question_to_analysis(question: str) -> str:
    normalized_question = normalize_text(question)

    if not normalized_question:
        return "unknown"

    scores = {
        intent_key: _score_intent(normalized_question, intent_key)
        for intent_key in INTENT_CONFIG.keys()
    }

    best_intent = max(scores, key=scores.get)
    best_score = scores[best_intent]

    if best_score < 3:
        return "unknown"

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_scores) > 1 and sorted_scores[0][1] == sorted_scores[1][1]:
        return "unknown"

    return best_intent