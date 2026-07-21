# Handoff Day 11 — Stok Produk (Backend) (#1, Fase 1.1a)

**Dev hari ini:** Go Steven Sanjaya
**Tanggal:** 2026-07-21
**Branch:** `feat/product-stock` (dari `main` @ `c9f1cc0`) → PR #19

---

## ✅ Stok / Quantity Produk — Backend (Fase 1.1a)

Menambah kuantitas stok **opsional** per produk katalog (dibangun di atas katalog produk PR #18). Tujuan: UMKM tahu sisa barang, order divalidasi terhadap stok, stok berkurang saat transaksi dikonfirmasi. Prasyarat menu self-order (Fase 3).

**Enforcement (keputusan brainstorming):**
- **Self-order → BLOKIR** kalau stok kurang (customer tak lihat barang fisik).
- **Kasir walk-in → WARNING** (tetap boleh jual; stok turun, floor di 0; peringatan di balasan).

Stok hidup di **metadata store** (SQLAlchemy `products.stock`), bukan BigQuery. Sale tetap di BigQuery (primary); decrement kasir = best-effort SETELAH sale, tak pernah membatalkan sale.

### File yang ditambahkan / diubah

| File | Keterangan |
|---|---|
| `app/models.py` | `Product.stock` — `Column(Integer, nullable=True)`. NULL = tak-dilacak; >=0 = dilacak |
| `app/migrations/versions/006_product_stock.py` | Migrasi add/drop kolom `stock` (down_revision 005; reversible) |
| `app/product_repo.py` | `stock` di `create_product`/`_product_to_dict`; `set_stock`; `check_stock`; `apply_decrement`; `_find_product_obj`; konstanta `LOW_STOCK_THRESHOLD=5` |
| `app/schemas.py` | `Product.stock: int \| None`; `StockUpdateRequest{stock: int\|None, ge=0}` |
| `app/api/routes/products.py` | `POST /umkm/products` terima Form `stock`; `PATCH /umkm/products/{id}/stock` (set/restock) |
| `app/services/checkout_service.py` | Kasir: `apply_decrement(allow_oversell=True)` best-effort pasca-sale + peringatan stok di `reply` |
| `tests/test_products.py` | Unit repo: set/check/decrement (tracked/untracked, atomik-insufficient, oversell-floor, cross-item rollback, duplicate-line, stock=0) |
| `tests/test_products_routes.py` (baru) | Route: stok di create/list, PATCH update/negatif-422/404, cross-tenant-404 |
| `tests/test_checkout_routes.py` | Kasir decrement + peringatan "tinggal N" / "habis" (oversell) |

**Tidak ada dep baru. Tidak menyentuh BigQuery/chromadb/gspread (test CI-clean).**

### Keputusan desain

| Topik | Keputusan |
|---|---|
| Cakupan stok | **Opsional per produk** — kolom `stock` nullable. NULL = tak-dilacak (mis. F&B masak on-demand), tak pernah memblokir/di-decrement |
| Decrement | **Pendekatan A**: metadata store + kasir best-effort pasca-sale (floor 0) + self-order pre-check atomik. Bukan 2-phase commit |
| Self-order block | Decrement **atomik bersyarat** (`UPDATE … WHERE stock >= qty`, cek rowcount, rollback batch bila ada yang kurang) — anti-race item terakhir |
| Ambang "menipis" | Konstanta `LOW_STOCK_THRESHOLD=5` (bukan kolom) |
| Konsistensi | Kasir decrement gagal → di-swallow, sale tetap sukses (pola best-effort seperti loyalty/points) |

### Catatan teknis
- **Seam self-order dibangun & diuji** (`check_stock` + `apply_decrement(allow_oversell=False)`), tapi **belum di-wire ke endpoint mana pun** — konsumen live = **Fase 3** (route self-order). Ini batas scope 1.1a yang disengaja.
- Duplicate baris produk sama terakumulasi benar di kedua path (self-order: WHERE in-transaction; kasir: SQLAlchemy identity-map + autoflush) — di-pin oleh test regresi.
- `apply_decrement` melewati item non-katalog / tak-dilacak (barang walk-in free-text tak ber-stok).

### Verifikasi (proven — output firsthand)
- `python -m pytest tests/ -q` → **189 passed** (baseline 184 + 5 regresi hardening).
- `ruff check app tests --extend-exclude=app/migrations` → **All checks passed!**
- `alembic downgrade -1 && alembic upgrade head` → **006 reversible**, current = `006 (head)`.
- Final whole-branch review (opus): **Ready to merge = YES**, no Critical/Important.

## 🔴 Blocker
- TIDAK ADA.

## 📌 Out-of-scope / deferred
- **Mobile UI stok** (field stok, badge Menipis/Habis/Tak-dilacak, edit/restock) → **Fase 1.1b** (plan terpisah).
- **Blokir self-order end-to-end** → **Fase 3** (route self-order memanggil seam yang sudah dibangun di sini).
- Histori pergerakan stok (audit), stok per-varian, sinkron stok ke BigQuery → nanti (YAGNI).
- **GATE proyek (Fase 0):** redeploy `main` → VPS + verifikasi live briefing/ask/sheets + 11 analisis **sebelum merge Fase 3**. Baseline live saat cek 2026-07-21 masih 4-analisis (deploy lama).
