# Handoff Day 13 — Kategori Produk (Backend) (#2, Fase 1.2a)

**Dev hari ini:** Go Steven Sanjaya
**Tanggal:** 2026-07-21
**Branch:** `feat/product-categories` (dari `main` @ `5955475`) → PR #<TBD>

---

## ✅ Kategori Produk — Backend (Fase 1.2a)

Menambah **kategori produk custom per-UMKM** (mis. Nasi, Mie, Minuman) agar produk bisa dikelompokkan. Prasyarat menu self-order (Fase 3) yang tampil per-kategori. Kategori hidup di **metadata store** (SQLAlchemy), sejajar `products`.

**Keputusan (brainstorming):**
- **Kategori opsional** — `products.category_id` nullable FK. Produk lama = "Tanpa kategori".
- **Unik per (tenant, name)** — cek case-insensitive di app + DB unique backstop + `IntegrityError→409` (aman race).
- **Hapus kategori = SET NULL** — produk di dalamnya di-set `category_id=NULL` (uncategorized), **tidak** ikut terhapus. Dilakukan di repo dalam **1 transaksi** (robust lintas SQLite/PG, tak andalkan PRAGMA). Return `{deleted, reassigned}` (reassigned = jumlah produk terdampak, untuk konfirmasi UI).
- **Cross-tenant category_id ditolak** di **create DAN PATCH** (400).

### File yang ditambahkan / diubah

| File | Keterangan |
|---|---|
| `app/models.py` | `ProductCategory` (tenant-scoped, unique (tenant_id,name)); `Product.category_id` (nullable FK, ondelete SET NULL) |
| `app/migrations/versions/007_product_categories.py` | Tabel `product_categories` + kolom `products.category_id` (batch_alter untuk SQLite); reversible |
| `app/category_repo.py` (baru) | `create_category` (dup guard + IntegrityError→ValueError), `list_categories`, `count_products_in_category`, `delete_category` (SET NULL 1 txn) |
| `app/product_repo.py` | `create_product(..., category_id)` + validasi ownership (tolak nonexistent/cross-tenant → ValueError); `set_category`; `_product_to_dict` sertakan `category_id` |
| `app/schemas.py` | `Category`, `CategoryListResponse`, `CategoryCreateRequest`, `CategoryUpdateRequest`; `Product.category_id` |
| `app/api/routes/categories.py` (baru) | `POST` (201/409 dup) · `GET` · `DELETE /umkm/categories/{id}` (200 {deleted,reassigned}/404) |
| `app/api/routes/products.py` | Form `category_id` di create (400 bila invalid) + `PATCH /umkm/products/{id}/category` |
| `app/main.py` | Register `categories` router |
| `tests/test_categories.py`, `tests/test_categories_routes.py` (baru) | Repo + route: CRUD, dup 409, delete SET NULL + reassigned, cross-tenant isolation (create+PATCH+delete), assign |

**Tidak ada dep baru. Tidak menyentuh BigQuery/chromadb/gspread (test CI-clean).**

### Verifikasi (proven — output firsthand)
- `python -m pytest tests/ -q` → **202 passed**.
- `ruff check app tests --extend-exclude=app/migrations` → **All checks passed!**
- `alembic upgrade head && alembic downgrade -1 && alembic upgrade head` → **007 reversible** (batch_alter).
- Final whole-branch review (opus): **Ready to merge = YES**, no Critical/Important; 6 cross-cutting checks PASS (tenant isolation semua path, SET NULL atomik, migrasi reversible, backward-compat).

## 🔴 Blocker
- TIDAK ADA.

## 📌 Out-of-scope / deferred
- **UI mobile kategori** (kelola kategori + dropdown pilih kategori di form + edit + dialog konfirmasi-count saat hapus) → **Fase 1.2b** (plan terpisah).
- **Menu self-order per-kategori** → **Fase 3**.
- **Follow-up minor (dari review, non-blocking):** (1) gambar produk ter-orphan bila create ditolak karena kategori invalid (validasi kategori SEBELUM simpan gambar, atau hapus file di except) — TODO; (2) `category_id` belum ada index (tambah saat ada query filter-by-category); (3) PATCH category balikan 400 untuk produk tak ada (vs 404 di stock) — konsistensi API; (4) DB unique kategori case-sensitive vs app case-insensitive (functional lower() index nanti); (5) rename kategori (YAGNI).
- **GATE proyek (Fase 0):** redeploy `main` → VPS + verifikasi live (11 analisis/briefing/ask/sheets) **sebelum merge Fase 3**. (Steven akan redeploy sendiri — lihat runbook.)
