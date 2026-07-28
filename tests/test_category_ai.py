"""Auto-kategori AI: service (fallback + LLM) & route (on-create + bulk)."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import auth, categories, products
from app.services import category_ai

_PNG = b"\x89PNG\r\n\x1a\nfake"


# ── Service unit tests ────────────────────────────────────────────

def test_fallback_keyword_when_llm_disabled(monkeypatch):
    monkeypatch.setattr(category_ai, "AI_AUTOCATEGORIZE", False)
    assert category_ai.suggest_category_name("Es Teh Manis") == "Minuman"
    assert category_ai.suggest_category_name("Nasi Goreng Spesial") == "Makanan"
    assert category_ai.suggest_category_name("Keripik Singkong") == "Camilan"
    assert category_ai.suggest_category_name("Donat Cokelat") == "Dessert"
    assert category_ai.suggest_category_name("Entah Apa Ini") == "Lainnya"


def test_fallback_reuses_existing_spelling(monkeypatch):
    monkeypatch.setattr(category_ai, "AI_AUTOCATEGORIZE", False)
    # existing pakai kapital beda → tetap dipakai (hindari duplikat).
    assert category_ai.suggest_category_name(
        "Kopi Susu", existing=["MINUMAN"]) == "MINUMAN"


def test_llm_path_used_when_enabled(monkeypatch):
    monkeypatch.setattr(category_ai, "AI_AUTOCATEGORIZE", True)
    monkeypatch.setattr(category_ai, "llm_generate",
                        lambda *a, **k: '{"category": "Kopi Spesial"}')
    assert category_ai.suggest_category_name("Latte") == "Kopi Spesial"


def test_llm_failure_falls_back(monkeypatch):
    monkeypatch.setattr(category_ai, "AI_AUTOCATEGORIZE", True)

    def _boom(*a, **k):
        raise RuntimeError("LLM mati")

    monkeypatch.setattr(category_ai, "llm_generate", _boom)
    assert category_ai.suggest_category_name("Es Teh") == "Minuman"


def test_llm_existing_match_uses_existing_spelling(monkeypatch):
    monkeypatch.setattr(category_ai, "AI_AUTOCATEGORIZE", True)
    monkeypatch.setattr(category_ai, "llm_generate",
                        lambda *a, **k: '{"category": "minuman"}')
    assert category_ai.suggest_category_name(
        "Teh", existing=["Minuman"]) == "Minuman"


# ── Route tests ──────────────────────────────────────────────────

def _client() -> TestClient:
    app = FastAPI()
    for r in (auth.router, products.router, categories.router):
        app.include_router(r)
    return TestClient(app)


def _tok(c) -> str:
    r = c.post("/auth/register",
               json={"email": "o@t.com", "password": "rahasia123", "business_name": "Toko"})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def test_create_product_auto_categorizes(monkeypatch, tmp_path):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    monkeypatch.setattr(category_ai, "AI_AUTOCATEGORIZE", False)  # pakai fallback
    c = _client()
    tok = _tok(c)

    r = c.post("/umkm/products", headers=_h(tok),
               data={"name": "Es Teh Manis"},
               files={"image": ("f.png", _PNG, "image/png")})
    assert r.status_code == 201, r.text
    cat_id = r.json()["category_id"]
    assert cat_id is not None  # otomatis diberi kategori

    cats = c.get("/umkm/categories", headers=_h(tok)).json()["categories"]
    assert any(x["id"] == cat_id and x["name"] == "Minuman" for x in cats)


def test_explicit_category_not_overridden(monkeypatch, tmp_path):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    monkeypatch.setattr(category_ai, "AI_AUTOCATEGORIZE", False)
    c = _client()
    tok = _tok(c)
    cid = c.post("/umkm/categories", headers=_h(tok),
                 json={"name": "Andalan"}).json()["id"]

    r = c.post("/umkm/products", headers=_h(tok),
               data={"name": "Es Teh", "category_id": str(cid)},
               files={"image": ("f.png", _PNG, "image/png")})
    assert r.status_code == 201, r.text
    assert r.json()["category_id"] == cid  # tidak ditimpa AI


def test_bulk_auto_categorize_uncategorized(monkeypatch, tmp_path):
    from app import product_repo
    monkeypatch.setattr(product_repo, "PRODUCT_IMAGE_DIR", str(tmp_path))
    # Matikan auto-kategori saat create supaya ada produk tanpa kategori dulu.
    monkeypatch.setattr(category_ai, "AI_AUTOCATEGORIZE", False)
    c = _client()
    tok = _tok(c)

    # Buat produk lalu paksa kategori None (simulasi produk lama tanpa kategori).
    for nm in ("Nasi Goreng", "Kopi Hitam"):
        pid = c.post("/umkm/products", headers=_h(tok), data={"name": nm},
                     files={"image": ("f.png", _PNG, "image/png")}).json()["id"]
        c.patch(f"/umkm/products/{pid}/category", headers=_h(tok),
                json={"category_id": None})

    r = c.post("/umkm/products/auto-categorize", headers=_h(tok))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_uncategorized"] == 2
    assert body["categorized"] == 2

    # Semua produk kini berkategori.
    prods = c.get("/umkm/products", headers=_h(tok)).json()["products"]
    assert all(p["category_id"] is not None for p in prods)

    # Idempotent: jalankan lagi → tak ada yang perlu dikategorikan.
    r2 = c.post("/umkm/products/auto-categorize", headers=_h(tok)).json()
    assert r2["total_uncategorized"] == 0
