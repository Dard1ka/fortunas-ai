# Handoff Day 14 — Kategori Produk (Mobile UI) (#2, Fase 1.2b)

**Dev hari ini:** Go Steven Sanjaya
**Tanggal:** 2026-07-21
**Branch:** `feat/mobile-product-categories` (dari `main` @ `10614ba`) → PR #22

---

## ✅ Kategori Produk — Mobile UI (Fase 1.2b)

Melengkapi Fase 1.2: UMKM bisa **pilih kategori saat tambah produk** + **kelola kategori** (tambah/lihat/hapus) dari app Flutter. Mengonsumsi endpoint backend Fase 1.2a (PR #21) — **tidak ada perubahan backend** di slice ini.

### File yang ditambahkan / diubah

| File | Keterangan |
|---|---|
| `mobile/lib/api/models.dart` | `Category` + `CategoryListResponse` + `fromJson`; `ProductItem.categoryId` (int?) |
| `mobile/lib/api/client.dart` | `listCategories`/`createCategory`/`deleteCategory`(→Map)/`setProductCategory`; `createProduct(..., categoryId)`; `hide Category` di import foundation.dart (hindari bentrok kelas anotasi Flutter) |
| `mobile/lib/products/category_controller.dart` (baru) | `CategoryController` (AutoDisposeNotifier): load/create/remove; `categoryControllerProvider` |
| `mobile/lib/products/product_controller.dart` | `create(..., int? categoryId)` diteruskan ke createProduct |
| `mobile/lib/screens/products_screen.dart` | Dropdown "Kategori (opsional)" di form tambah; label kategori di kartu produk; entry "Kategori" → sheet **Kelola Kategori** (tambah/list/hapus + dialog konfirmasi-jumlah) |
| `mobile/test/support/fakes.dart` | FakeApi: override kategori (+ `lastCreateCategoryName`/`lastDeleteCategoryId`/`lastSetProductCategory`/`lastCreateCategoryIdOnProduct`) |
| `mobile/test/products/category_controller_test.dart`, `mobile/test/screens/products_categories_test.dart`, `mobile/test/screens/categories_manage_test.dart` (baru) | Controller + dropdown/label + Kelola Kategori (add/list/delete confirm-count/Batal) |

**NOL dep baru. Tidak menyentuh backend/Python.**

### Keputusan desain
| Topik | Keputusan |
|---|---|
| Pilih kategori | Dropdown **opsional** di form tambah produk; default "Tanpa kategori" (null) |
| Label kartu | Nama kategori di-resolve dari list kategori termuat; skip bila tak ketemu |
| Hapus kategori | Dialog konfirmasi menyebut **jumlah produk terdampak** (dihitung lokal dari product list — cocok dgn backend SET NULL yang unpaginated); Batal = no-op; konfirmasi → delete + refresh product list |
| Create+category | Diuji di level `ProductController` (image_picker blok submit form penuh di widget test) |

### Verifikasi (proven — output firsthand)
- `flutter test` → **146 passed** (baseline 133 + 13 baru).
- `flutter analyze --no-fatal-infos` → **7 issues** (pre-existing infos), **0 baru**.
- Final whole-branch review (opus): **Ready to merge = YES**, no Critical/Important; 6 cross-cutting checks PASS.

## 🔴 Blocker
- TIDAK ADA.

## 📌 Out-of-scope / deferred
- **Edit kategori produk yang SUDAH ada** (`setProductCategory` sudah ada di client + fake, belum di-wire ke UI) → follow-up slice.
- **Follow-up minor (dari review, non-blocking):** (1) pill kategori pakai warna sama dgn badge "Tak dilacak" (`surfaceSoft`) → ganti ke `violetSoft` biar beda (paling kelihatan, 1 baris); (2) form re-load kategori tiap buka (jadikan `if(cats.isEmpty)`); (3) factor `_pill()` helper (dedup boilerplate); (4) label "Kategori" vs judul sheet "Kelola Kategori".
- **Menu self-order per-kategori** → **Fase 3**.
- **GATE proyek (Fase 0):** VPS = backend only; backend main sudah current (stok+kategori). Steven redeploy sendiri via `Fortunas/REDEPLOY_VPS_RUNBOOK.md`; verifikasi live sebelum merge Fase 3.
