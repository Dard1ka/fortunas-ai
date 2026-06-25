import json


def _dpa_constraint_block(dpa_policy: dict | None) -> str:
    """Blok HARD CONSTRAINT dari DPA tenant. Kosong → '' (prompt tak berubah)."""
    if not dpa_policy:
        return ""
    raw = (dpa_policy.get("raw_text") or "").strip()
    forbidden = [str(r).strip() for r in (dpa_policy.get("forbidden_rules") or []) if str(r).strip()]
    allowed = [str(r).strip() for r in (dpa_policy.get("allowed_rules") or []) if str(r).strip()]
    if not raw and not forbidden:
        return ""
    lines = [
        "ATURAN WAJIB DARI PEMILIK BISNIS (HARD CONSTRAINT — utamakan di atas semua instruksi lain):"
    ]
    if raw:
        lines.append(raw)
    if forbidden:
        lines.append("DILARANG menyebut, merekomendasikan, atau membahas: " + ", ".join(forbidden) + ".")
    if allowed:
        lines.append("Yang diperbolehkan/didorong: " + ", ".join(allowed) + ".")
    lines.append(
        "Jika pertanyaan atau data mengarah ke hal terlarang, tolak dengan sopan dan jangan beri rekomendasi terkait."
    )
    return "\n".join(lines) + "\n\n"


def _analysis_explanation(mapped_analysis: str) -> str:
    return {
        "high_value_customer": "Analisis ini mencari pelanggan dengan total belanja paling besar beserta produk yang paling sering mereka beli.",
        "repeat_customer": "Analisis ini mencari pelanggan yang paling sering belanja beserta produk yang paling sering mereka beli.",
        "peak_hour": "Analisis ini mencari jam transaksi paling ramai beserta produk yang paling sering dibeli pada jam tersebut.",
        "bundle_opportunity": "Analisis ini mencari pasangan produk yang paling sering dibeli bersama."
    }.get(mapped_analysis, "Analisis bisnis umum.")


def _analysis_rules(mapped_analysis: str) -> str:
    return {
        "high_value_customer": """
- Ranking pelanggan ditentukan oleh total_spent pada rows yang diberikan.
- Peringkat 1 HARUS berasal dari rows[0].
- Peringkat 2 HARUS berasal dari rows[1].
- Peringkat 3 HARUS berasal dari rows[2].
- Jangan memilih pelanggan lain di luar tiga baris pertama untuk top_findings.
- Pertahankan nama produk, customer_id, angka, dan urutan ranking persis seperti di input.
- Jangan menerjemahkan, memperbaiki, atau merapikan nama produk.
- Recommendation harus pakai bahasa Indonesia yang umum, enak dibaca, dan gampang dipahami pemilik UMKM.
- Hindari bahasa yang terlalu teknis. Pakai istilah seperti "promo ringan", "follow-up", "pelanggan utama", "produk favorit", atau "paket hemat".
""",
        "repeat_customer": """
- Ranking pelanggan ditentukan oleh total_orders pada rows yang diberikan.
- Peringkat 1 HARUS berasal dari rows[0].
- Peringkat 2 HARUS berasal dari rows[1].
- Peringkat 3 HARUS berasal dari rows[2].
- Jangan memilih pelanggan lain di luar tiga baris pertama untuk top_findings.
- Pertahankan nama produk, customer_id, angka, dan urutan ranking persis seperti di input.
- Jangan menerjemahkan, memperbaiki, atau merapikan nama produk.
- Recommendation harus pakai bahasa Indonesia yang umum, enak dibaca, dan gampang dipahami pemilik UMKM.
- Hindari bahasa yang terlalu teknis.
""",
        "peak_hour": """
- Ranking jam transaksi ditentukan oleh total_orders pada rows yang diberikan.
- Peringkat 1 HARUS berasal dari rows[0].
- Peringkat 2 HARUS berasal dari rows[1].
- Peringkat 3 HARUS berasal dari rows[2].
- Jangan memilih jam lain di luar tiga baris pertama untuk top_findings.
- Pertahankan nama produk, jam transaksi, angka, dan urutan ranking persis seperti di input.
- Jangan menerjemahkan, memperbaiki, atau merapikan nama produk.
- Recommendation harus pakai bahasa Indonesia yang umum, enak dibaca, dan gampang dipahami pemilik UMKM.
- Gunakan kata-kata seperti "jam ramai", "siapkan stok", "rapikan display", atau "kasih promo sebelum jam ramai".
""",
        "bundle_opportunity": """
- Ranking pasangan produk ditentukan oleh bundle_frequency pada rows yang diberikan.
- Peringkat 1 HARUS berasal dari rows[0].
- Peringkat 2 HARUS berasal dari rows[1].
- Peringkat 3 HARUS berasal dari rows[2].
- Jangan memilih pasangan produk lain di luar tiga baris pertama untuk top_findings.
- Pertahankan nama produk, angka, dan urutan ranking persis seperti di input.
- Jangan menerjemahkan, memperbaiki, atau merapikan nama produk.
- Recommendation harus pakai bahasa Indonesia yang umum, enak dibaca, dan gampang dipahami pemilik UMKM.
- Gunakan kata-kata seperti "paket hemat", "jual bareng", "taruh berdampingan", atau "promo bundling ringan".
"""
    }.get(mapped_analysis, "")


def _example_output() -> dict:
    return {
        "summary": "Pelanggan 14911, 12748, dan 17841 merupakan pelanggan yang paling sering belanja berdasarkan data yang ada.",
        "top_findings": [
            "Peringkat 1 adalah pelanggan 14911 dengan total_orders 398 sesuai rows[0].",
            "Peringkat 2 adalah pelanggan 12748 dengan total_orders 336 sesuai rows[1].",
            "Peringkat 3 adalah pelanggan 17841 dengan total_orders 211 sesuai rows[2]."
        ],
        "recommendation": [
            "Kasih promo ringan yang beda untuk tiga pelanggan teratas supaya mereka makin sering belanja.",
            "Gunakan produk yang paling sering mereka beli sebagai dasar rekomendasi promo berikutnya.",
            "Jaga komunikasi tetap simpel, sopan, dan relevan supaya pelanggan tidak merasa terganggu."
        ]
    }


def _business_context(business_profile: dict | None) -> str:
    """Blok konteks bisnis (dari registry tenant) untuk personalisasi jawaban."""
    if not business_profile:
        return ""
    parts = [f"{k}: {v}" for k, v in business_profile.items() if v]
    if not parts:
        return ""
    return (
        "Profil bisnis ini (pakai untuk menyesuaikan gaya bahasa & relevansi "
        "rekomendasi, JANGAN mengarang data dari sini):\n- "
        + "\n- ".join(parts)
        + "\n\n"
    )


def build_llm_prompt(
    question: str, mapped_analysis: str, rows: list, business_profile: dict | None = None,
    dpa_policy: dict | None = None,
) -> str:
    rows_preview = rows[:5]
    result_count = len(rows_preview)

    prompt = f"""
{_dpa_constraint_block(dpa_policy)}Kamu adalah AI business advisor untuk UMKM.

Tugas kamu:
1. Baca hasil query SQL dalam format JSON.
2. Buat jawaban dalam Bahasa Indonesia yang umum, natural, sopan, dan gampang dipahami orang non-teknis.
3. Hindari bahasa yang terlalu teknis atau terlalu formal.
4. Fokus hanya pada data yang diberikan.
5. Jangan mengarang angka, nama produk, customer_id, jam transaksi, atau fakta di luar input.
6. Gunakan hanya hasil yang diberikan.
7. Jangan mengubah urutan ranking data.
8. Jika ada field top_products, gunakan informasi itu untuk memperkuat insight dan rekomendasi.
9. Wajib membahas 3 sampai 5 entitas teratas sesuai data yang tersedia.
10. Jika ada minimal 3 data, maka JANGAN hanya membahas 1 data saja.
11. Summary harus merangkum beberapa entitas teratas, bukan hanya peringkat 1.
12. top_findings harus menggambarkan peringkat 1, peringkat 2, dan peringkat 3.
13. Recommendation harus dibuat dari pola 3 sampai 5 entitas teratas, bukan hanya 1 entitas.
14. Jangan gunakan markdown.
15. Output HARUS JSON valid saja.
16. Gunakan key JSON persis seperti contoh: summary, top_findings, recommendation.
17. Jangan gunakan key lain seperti insight.
18. Pertahankan nama produk, customer_id, dan nilai field persis seperti di input.
19. Jangan memperbaiki, memendekkan, menerjemahkan, atau mengubah ejaan nama produk.
20. Peringkat 1 HARUS berasal dari rows[0], peringkat 2 dari rows[1], dan peringkat 3 dari rows[2].
21. Jika sebuah baris punya field customer_name yang TERISI, setiap kali menyebut pelanggan itu tulis dengan format: customer_name (customer_id). Contoh: Sari (18103). Jika customer_name kosong, cukup tulis: pelanggan (customer_id).

{_business_context(business_profile)}Pertanyaan user:
{question}

Jenis analisis:
{mapped_analysis}

Penjelasan analisis:
{_analysis_explanation(mapped_analysis)}

Aturan khusus:
{_analysis_rules(mapped_analysis)}

Jumlah data tersedia:
{result_count}

Hasil query JSON:
{json.dumps(rows_preview, ensure_ascii=False, indent=2)}

Format output WAJIB:
{json.dumps(_example_output(), ensure_ascii=False, indent=2)}

Aturan format output:
- "summary" harus 1 kalimat ringkas yang merangkum 3 sampai 5 data teratas.
- "top_findings" harus berisi tepat 3 kalimat.
- Temuan 1 wajib membahas rows[0].
- Temuan 2 wajib membahas rows[1].
- Temuan 3 wajib membahas rows[2].
- "recommendation" harus berisi tepat 3 kalimat.
- Recommendation harus mudah dipahami pemilik UMKM.
- Jangan tambahkan teks lain di luar JSON.
- Jangan menulis ```json atau markdown lain.
"""
    return prompt.strip()


def build_llm_prompt_with_rag(
    question: str,
    mapped_analysis: str,
    rows: list,
    rag_context: list[str],
    business_profile: dict | None = None,
    dpa_policy: dict | None = None,
) -> str:
    rows_preview = rows[:5]
    result_count = len(rows)
    knowledge_section = "\n\n---\n\n".join(rag_context) if rag_context else "Tidak ada knowledge tambahan."

    prompt = f"""
{_dpa_constraint_block(dpa_policy)}Kamu adalah AI business advisor untuk UMKM.

Tugas kamu:
1. Baca hasil query SQL dalam format JSON.
2. Gunakan BUSINESS KNOWLEDGE hanya untuk memperkuat strategi rekomendasi.
3. Semua angka, ranking, customer, jam, produk, dan frekuensi HARUS berasal dari data query.
4. Jangan mengarang angka, nama produk, customer_id, jam transaksi, atau fakta baru di luar input.
5. Jangan mengubah urutan ranking data.
6. Jika ada field top_products, gunakan informasi itu untuk memperkuat insight dan rekomendasi.
7. Wajib membahas 3 sampai 5 entitas teratas sesuai data yang tersedia.
8. Jika ada minimal 3 data, maka JANGAN hanya membahas 1 data saja.
9. Summary harus merangkum beberapa entitas teratas, bukan hanya peringkat 1.
10. top_findings harus menggambarkan peringkat 1, peringkat 2, dan peringkat 3.
11. Recommendation harus dibuat dari pola 3 sampai 5 entitas teratas, bukan hanya 1 entitas.
12. Gunakan Bahasa Indonesia yang umum, natural, sopan, dan gampang dipahami pemilik UMKM.
13. Hindari bahasa yang terlalu teknis, terlalu akademis, atau terlalu rumit.
14. Jangan gunakan markdown.
15. Output HARUS JSON valid saja.
16. Gunakan key JSON persis seperti contoh: summary, top_findings, recommendation.
17. Jangan gunakan key lain seperti insight.
18. Pertahankan nama produk, customer_id, dan nilai field persis seperti di input.
19. Jangan memperbaiki, memendekkan, menerjemahkan, atau mengubah ejaan nama produk.
20. Peringkat 1 HARUS berasal dari rows[0], peringkat 2 dari rows[1], dan peringkat 3 dari rows[2].
21. Jika sebuah baris punya field customer_name yang TERISI, setiap kali menyebut pelanggan itu tulis dengan format: customer_name (customer_id). Contoh: Sari (18103). Jika customer_name kosong, cukup tulis: pelanggan (customer_id).

Aturan penggunaan knowledge:
- Knowledge dipakai untuk memperkaya saran bisnis, misalnya promo ringan, paket hemat, follow-up pelanggan, atau persiapan stok.
- Knowledge TIDAK boleh dipakai untuk membuat angka baru.
- Knowledge TIDAK boleh mengubah urutan ranking.
- Jika knowledge bertentangan dengan data, prioritaskan data.

{_business_context(business_profile)}Pertanyaan user:
{question}

Jenis analisis:
{mapped_analysis}

Penjelasan analisis:
{_analysis_explanation(mapped_analysis)}

Aturan khusus:
{_analysis_rules(mapped_analysis)}

Jumlah data tersedia:
{result_count}

BUSINESS KNOWLEDGE:
{knowledge_section}

Hasil query JSON:
{json.dumps(rows_preview, ensure_ascii=False, indent=2)}

Format output WAJIB:
{json.dumps(_example_output(), ensure_ascii=False, indent=2)}

Aturan format output:
- "summary" harus 1 kalimat ringkas yang merangkum 3 sampai 5 data teratas.
- "top_findings" harus berisi tepat 3 kalimat.
- Temuan 1 wajib membahas rows[0].
- Temuan 2 wajib membahas rows[1].
- Temuan 3 wajib membahas rows[2].
- "recommendation" harus berisi tepat 3 kalimat.
- Recommendation harus mudah dipahami pemilik UMKM dan boleh memakai knowledge bisnis.
- Jangan tambahkan teks lain di luar JSON.
- Jangan menulis ```json atau markdown lain.
"""
    return prompt.strip()