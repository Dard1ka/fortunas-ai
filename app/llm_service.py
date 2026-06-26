import json
import re
from dotenv import load_dotenv

from app.llm_provider import check_llm_health, llm_generate

load_dotenv()


def extract_json_object(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return None


def check_ollama_health() -> dict:
    # Nama dipertahankan untuk kompatibilitas; sekarang provider-aware.
    return check_llm_health()


def _as_clean_str(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_clean_list(value) -> list[str]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = [value]
    else:
        items = []

    cleaned = []
    for item in items:
        text = _as_clean_str(item)
        if text:
            cleaned.append(text)
    return cleaned


def _join_id(items: list[str]) -> str:
    """Join list secara natural: 'a', 'a dan b', 'a, b, dan c'."""
    items = [str(x) for x in items if x is not None and str(x) != ""]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} dan {items[1]}"
    return ", ".join(items[:-1]) + f", dan {items[-1]}"


def _fmt_customer(row: dict) -> str:
    """Format pelanggan: 'nama (id)' kalau customer_name ada, selain itu 'id' saja."""
    cid = row.get("customer_id")
    name = (row.get("customer_name") or "").strip()
    return f"{name} ({cid})" if name else str(cid)


def _build_summary_from_rows(mapped_analysis: str, rows: list) -> str:
    top = rows[:3]
    if not top:
        return "Belum ada data yang cukup untuk dianalisis pada kategori ini."

    n = len(top)

    if mapped_analysis == "repeat_customer":
        ids = _join_id([_fmt_customer(r) for r in top])
        orders = _join_id([r.get("total_orders") for r in top])
        tail = "pelanggan paling loyal" if n == 1 else "pelanggan loyal teratas"
        return (
            f"{ids} merupakan {tail} berdasarkan total_orders {orders}."
        )

    if mapped_analysis == "high_value_customer":
        ids = _join_id([_fmt_customer(r) for r in top])
        spents = _join_id([r.get("total_spent") for r in top])
        tail = "pelanggan paling bernilai" if n == 1 else "pelanggan paling bernilai teratas"
        return (
            f"{ids} merupakan {tail} berdasarkan total_spent {spents}."
        )

    if mapped_analysis == "peak_hour":
        hours = _join_id([r.get("purchase_hour") for r in top])
        orders = _join_id([r.get("total_orders") for r in top])
        tail = "jam transaksi paling ramai" if n == 1 else "jam transaksi paling ramai"
        return (
            f"Jam {hours} merupakan {tail} berdasarkan total_orders {orders}."
        )

    if mapped_analysis == "bundle_opportunity":
        pairs = _join_id([f"{r.get('product_A')} + {r.get('product_B')}" for r in top])
        freqs = _join_id([r.get("bundle_frequency") for r in top])
        tail = "pasangan yang paling sering dibeli bersama"
        return (
            f"Pasangan produk {pairs} merupakan {tail} berdasarkan bundle_frequency {freqs}."
        )

    if mapped_analysis == "top_product":
        names = _join_id([str(r.get("description")) for r in top])
        omzets = _join_id([r.get("total_omzet") for r in top])
        return (
            f"{names} merupakan produk dengan omzet tertinggi berdasarkan total_omzet {omzets}."
        )

    return "Data berhasil dianalisis berdasarkan hasil yang tersedia."


def _build_top_findings_from_rows(mapped_analysis: str, rows: list) -> list[str]:
    top3 = rows[:3]
    findings = []

    if mapped_analysis == "repeat_customer":
        for idx, row in enumerate(top3, start=1):
            findings.append(
                f"Peringkat {idx} adalah {_fmt_customer(row)} dengan total_orders {row['total_orders']}, "
                f"total_spent {row['total_spent']}, dan top_products: {row.get('top_products', '')}."
            )

    elif mapped_analysis == "high_value_customer":
        for idx, row in enumerate(top3, start=1):
            findings.append(
                f"Peringkat {idx} adalah {_fmt_customer(row)} dengan total_spent {row['total_spent']}, "
                f"total_orders {row['total_orders']}, avg_order_value {row.get('avg_order_value', '')}, "
                f"dan top_products: {row.get('top_products', '')}."
            )

    elif mapped_analysis == "peak_hour":
        for idx, row in enumerate(top3, start=1):
            findings.append(
                f"Peringkat {idx} adalah jam {row['purchase_hour']} dengan total_orders {row['total_orders']} "
                f"dan top_products: {row.get('top_products', '')}."
            )

    elif mapped_analysis == "bundle_opportunity":
        for idx, row in enumerate(top3, start=1):
            findings.append(
                f"Peringkat {idx} adalah pasangan produk {row['product_A']} dan {row['product_B']} "
                f"dengan bundle_frequency {row['bundle_frequency']}."
            )

    elif mapped_analysis == "top_product":
        for idx, row in enumerate(top3, start=1):
            findings.append(
                f"Peringkat {idx} adalah {row['description']} dengan total_omzet {row['total_omzet']} "
                f"dan total_qty {row['total_qty']}."
            )

    while len(findings) < 3:
        findings.append("")

    return findings[:3]


def _build_recommendations_from_rows(mapped_analysis: str, rows: list) -> list[str]:
    top3 = rows[:3]

    if mapped_analysis == "repeat_customer":
        ids = [_fmt_customer(r) for r in top3 if "customer_id" in r]
        joined = ", ".join(ids[:3]) if ids else "pelanggan teratas"
        return [
            f"Kasih promo ringan yang beda untuk {joined} supaya mereka makin sering belanja.",
            "Gunakan produk yang paling sering mereka beli sebagai dasar promo atau rekomendasi berikutnya.",
            "Jaga komunikasi tetap simpel, sopan, dan relevan supaya pelanggan merasa diperhatikan, bukan dikejar-kejar."
        ]

    if mapped_analysis == "high_value_customer":
        ids = [_fmt_customer(r) for r in top3 if "customer_id" in r]
        joined = ", ".join(ids[:3]) if ids else "pelanggan utama"
        return [
            f"Utamakan {joined} untuk penawaran yang lebih personal karena nilai belanjanya paling besar.",
            "Coba beri benefit sederhana seperti bonus kecil, akses promo lebih dulu, atau penawaran khusus tanpa harus diskon besar.",
            "Jaga komunikasi tetap relevan dan tidak terlalu sering supaya pelanggan utama tetap nyaman."
        ]

    if mapped_analysis == "peak_hour":
        hours = [str(r["purchase_hour"]) for r in top3 if "purchase_hour" in r]
        joined = ", ".join(hours[:3]) if hours else "jam ramai"
        return [
            f"Siapkan stok, display, dan alur transaksi sebelum jam {joined} karena itu periode paling ramai.",
            "Taruh produk yang paling laku di area yang mudah diambil supaya pelanggan bisa belanja lebih cepat saat toko sedang padat.",
            "Kalau mau kasih promo, buat yang sederhana dan mudah dipahami pelanggan sebelum atau saat jam ramai."
        ]

    if mapped_analysis == "bundle_opportunity":
        if len(top3) >= 3:
            r1, r2, r3 = top3[0], top3[1], top3[2]
            return [
                f"Coba buat paket hemat untuk {r1['product_A']} dan {r1['product_B']} karena pasangan ini paling sering dibeli bareng.",
                f"Taruh {r2['product_A']} dan {r2['product_B']} berdekatan di etalase atau katalog supaya pelanggan lebih gampang ambil dua-duanya.",
                f"Gunakan bundling ringan untuk {r3['product_A']} dan {r3['product_B']} selama stok aman supaya nilai belanja bisa naik tanpa bikin promo terlalu rumit."
            ]

        return [
            "Coba buat paket hemat untuk pasangan produk yang paling sering dibeli bareng.",
            "Taruh produk yang cocok dijual paket secara berdampingan di etalase atau katalog.",
            "Gunakan bundling ringan selama stok aman supaya nilai belanja bisa naik."
        ]

    if mapped_analysis == "top_product":
        names = [str(r.get("description")) for r in top3 if r.get("description")]
        joined = ", ".join(names[:3]) if names else "produk terlaris"
        return [
            f"Pastikan stok {joined} selalu aman karena produk ini penyumbang omzet terbesar.",
            "Jadikan produk omzet tertinggi sebagai andalan promo atau display utama.",
            "Pantau tren penjualannya supaya bisa antisipasi lonjakan permintaan tanpa kehabisan stok."
        ]

    return [
        "Gunakan hasil analisis ini untuk bikin promo yang lebih tepat sasaran.",
        "Fokuskan strategi ke tiga hasil teratas dari data yang ada.",
        "Coba jalankan dulu dalam skala kecil lalu lihat hasilnya sebelum diperluas."
    ]


def _repair_output(parsed: dict, mapped_analysis: str | None = None, rows: list | None = None) -> dict:
    if mapped_analysis is None and rows is None and "executive_summary" in parsed:
        return {
            "executive_summary": _as_clean_str(parsed.get("executive_summary"))
        }

    summary = _as_clean_str(parsed.get("summary") or parsed.get("insight", ""))
    top_findings = _as_clean_list(parsed.get("top_findings", []))
    recommendation = _as_clean_list(parsed.get("recommendation", []))

    # UTAMAKAN output LLM (sudah di-ground ke rows[0..] oleh prompt). Template
    # deterministik dari data hanya dipakai sebagai FALLBACK kalau LLM kosong —
    # supaya jawaban tetap muncul & akurat meski LLM gagal.
    if mapped_analysis and rows:
        if not summary:
            summary = _build_summary_from_rows(mapped_analysis, rows)
        if not top_findings:
            top_findings = _build_top_findings_from_rows(mapped_analysis, rows)
        if not recommendation:
            recommendation = _build_recommendations_from_rows(mapped_analysis, rows)

    if not summary:
        summary = "Insight berhasil dibuat berdasarkan hasil analisis yang tersedia."

    # Buang item kosong supaya tidak ada kartu kosong di UI.
    top_findings = [f for f in top_findings if f][:3]
    recommendation = [r for r in recommendation if r][:3]

    return {
        "summary": summary.strip(),
        "top_findings": top_findings,
        "recommendation": recommendation,
    }


def call_ollama(prompt: str, mapped_analysis: str | None = None, rows: list | None = None) -> dict:
    # Nama dipertahankan untuk kompatibilitas; routing via LLM_PROVIDER (ollama/openai).
    raw_text = llm_generate(
        prompt, json_mode=True, temperature=0.1, max_tokens=1000, timeout=300
    )

    if not raw_text:
        raise ValueError("LLM mengembalikan response kosong.")

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        extracted = extract_json_object(raw_text)
        if extracted:
            try:
                parsed = json.loads(extracted)
            except json.JSONDecodeError:
                raise ValueError(f"Output Ollama bukan JSON valid: {raw_text}")
        else:
            raise ValueError(f"Tidak ditemukan object JSON dalam output Ollama: {raw_text}")

    if not isinstance(parsed, dict):
        raise ValueError(f"Output Ollama bukan object JSON: {parsed}")

    return _repair_output(parsed, mapped_analysis=mapped_analysis, rows=rows)