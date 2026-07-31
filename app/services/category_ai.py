"""AI auto-kategorisasi produk UMKM.

Alur:
  1. `suggest_category_name(name, description, existing)` → nama kategori terbaik.
     Utamakan salah satu kategori yang SUDAH ada (existing); kalau tidak ada yang
     cocok, usulkan nama kategori baru yang ringkas (1-2 kata, Title Case, Bahasa
     Indonesia). Memakai LLM (app.llm_provider.llm_generate) dalam json_mode.
  2. Kalau LLM gagal / mati / mengembalikan hal aneh → fallback ke aturan keyword
     deterministik supaya fitur tetap jalan tanpa koneksi LLM (dan test cepat).

Orkestrasi (resolve nama → id → set ke produk) ada di `categorize_product` &
`categorize_all_uncategorized`, yang dipakai route.
"""
from __future__ import annotations

import json
import logging
import os

from app import category_repo, product_repo
from app.llm_provider import llm_generate

logger = logging.getLogger(__name__)

# Toggle global (mis. dimatikan di CI/offline). Default: aktif.
AI_AUTOCATEGORIZE = os.getenv("AI_AUTOCATEGORIZE", "1").strip().lower() not in {
    "0", "false", "no", "off"}

# Aturan fallback: kategori → keyword yang menandakannya. Dicek berurutan;
# kategori pertama yang keyword-nya muncul di nama/deskripsi produk yang menang.
# Fokus UMKM makanan/minuman (segmen utama aplikasi).
_KEYWORD_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Minuman", (
        "teh", "kopi", "coffee", "susu", "milk", "jus", "juice", "es ", "ice",
        "soda", "boba", "latte", "cappuccino", "capucino", "matcha", "lemon",
        "sirup", "air ", "mineral", "smoothie", "milo", "chocolatos",
        "americano", "espresso", "mojito", "yakult", "minum",
    )),
    ("Camilan", (
        "keripik", "kripik", "snack", "cemilan", "camilan", "gorengan",
        "kerupuk", "basreng", "makaroni", "cireng", "cimol", "seblak",
        "biskuit", "wafer", "coklat batang", "permen",
    )),
    ("Makanan", (
        "nasi", "mie", "mi ", "bakso", "ayam", "sate", "soto", "roti", "bakmi",
        "burger", "pizza", "kebab", "martabak", "geprek", "rendang", "gado",
        "bubur", "sosis", "telur", "ikan", "daging", "sayur", "lontong",
        "ketoprak", "pecel", "nugget", "dimsum", "siomay", "batagor", "makan",
    )),
    ("Dessert", (
        "kue", "cake", "donat", "donut", "puding", "pudding", "brownies",
        "brownie", "es krim", "ice cream", "pancake", "waffle", "croissant",
        "cheesecake", "tart", "pastry", "manis",
    )),
]


def _fallback_category(name: str, description: str, existing: list[str]) -> str:
    """Tebak kategori tanpa LLM. Utamakan kategori existing yang cocok keyword,
    lalu aturan keyword umum, terakhir 'Lainnya'."""
    text = f"{name} {description}".lower()

    # 1) Cocokkan ke aturan keyword. Kalau kategori standar itu sudah ada milik
    #    tenant, pakai ejaan versi existing supaya tak bikin duplikat beda kapital.
    existing_lower = {e.lower(): e for e in existing}
    for cat, keywords in _KEYWORD_RULES:
        if any(kw in text for kw in keywords):
            return existing_lower.get(cat.lower(), cat)

    # 2) Nama kategori existing muncul langsung di teks produk.
    for low, original in existing_lower.items():
        if low and low in text:
            return original

    return "Lainnya"


def _build_prompt(name: str, description: str, existing: list[str]) -> str:
    existing_block = (
        "\n".join(f"- {e}" for e in existing) if existing else "(belum ada)")
    return (
        "Kamu asisten yang mengelompokkan produk UMKM ke dalam satu kategori.\n"
        "Balas HANYA dalam format JSON: {\"category\": \"NamaKategori\"}.\n\n"
        "Aturan:\n"
        "- Utamakan memilih salah satu kategori yang SUDAH ADA di bawah bila cocok.\n"
        "- Kalau tidak ada yang cocok, usulkan nama kategori BARU yang ringkas "
        "(1-2 kata, Title Case, Bahasa Indonesia), contoh: Minuman, Makanan, "
        "Camilan, Dessert, Sembako, Alat Tulis.\n"
        "- Jangan mengarang deskripsi; cukup kategorikan.\n\n"
        f"Kategori yang sudah ada:\n{existing_block}\n\n"
        f"Nama produk: {name}\n"
        f"Deskripsi: {description or '(tidak ada)'}\n"
    )


def _normalize_name(raw: str) -> str:
    """Rapikan nama kategori dari LLM: trim, buang tanda kutip, batasi panjang."""
    clean = (raw or "").strip().strip('"').strip("'").strip()
    clean = " ".join(clean.split())  # collapse whitespace
    return clean[:60]


def suggest_category_name(
    name: str, description: str = "", existing: list[str] | None = None
) -> str:
    """Kembalikan nama kategori terbaik untuk sebuah produk.

    Selalu mengembalikan string tak-kosong (fallback 'Lainnya'). Tidak melempar
    exception — aman dipanggil best-effort saat create produk.
    """
    existing = existing or []
    prod_name = (name or "").strip()
    if not prod_name:
        return "Lainnya"

    if not AI_AUTOCATEGORIZE:
        return _fallback_category(prod_name, description, existing)

    try:
        raw = llm_generate(
            _build_prompt(prod_name, description, existing),
            json_mode=True, temperature=0.0, max_tokens=60, timeout=30,
        )
        parsed = json.loads(raw)
        suggested = _normalize_name(str(parsed.get("category", "")))
        if not suggested:
            raise ValueError("kategori kosong dari LLM")
        # Kalau LLM menyebut kategori existing (case-insensitive), pakai ejaan existing.
        for e in existing:
            if e.lower() == suggested.lower():
                return e
        return suggested
    except Exception as exc:  # noqa: BLE001 — best-effort, jangan ganggu create produk
        logger.warning("Auto-kategori LLM gagal (%s); pakai fallback keyword.", exc)
        return _fallback_category(prod_name, description, existing)


def categorize_product(tenant_id: int, product: dict) -> int | None:
    """Tentukan & set kategori untuk satu produk (dict dari product_repo).

    Return category_id yang di-set, atau None bila gagal/tak berubah.
    """
    existing = [c["name"] for c in category_repo.list_categories(tenant_id)]
    cat_name = suggest_category_name(
        product.get("name", ""), product.get("description", ""), existing)
    cat = category_repo.get_or_create_category(tenant_id, cat_name)
    if product_repo.set_category(tenant_id, product["id"], cat["id"]):
        return cat["id"]
    return None


def categorize_all_uncategorized(tenant_id: int) -> dict:
    """Auto-kategori semua produk milik tenant yang belum punya kategori.

    Return {"categorized": n, "total_uncategorized": m}.
    """
    products = product_repo.list_products(tenant_id)
    uncategorized = [p for p in products if p.get("category_id") is None]
    done = 0
    for p in uncategorized:
        if categorize_product(tenant_id, p) is not None:
            done += 1
    return {"categorized": done, "total_uncategorized": len(uncategorized)}
