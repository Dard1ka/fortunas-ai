# Handoff Day 12 — Stok Produk (Mobile UI) (#1, Fase 1.1b)

**Dev hari ini:** Go Steven Sanjaya
**Tanggal:** 2026-07-21
**Branch:** `feat/mobile-product-stock` (dari `main` @ `ab0cc7e`) → PR #<TBD>

---

## ✅ Stok / Quantity Produk — Mobile UI (Fase 1.1b)

Melengkapi vertical stok: UMKM kini bisa **set / lihat / edit** stok produk dari app Flutter (Kelola Produk). Mengonsumsi endpoint backend yang di-merge di **Fase 1.1a (PR #19)** — tidak ada perubahan backend/Python di slice ini.

Stok `int?`: `null` = tak-dilacak; `0` = Habis; `1..5` = Menipis; selain itu `Stok: N`.

### File yang ditambahkan / diubah

| File | Keterangan |
|---|---|
| `mobile/lib/api/models.dart` | `ProductItem.stock` (`int?`, parse `j['stock']`) |
| `mobile/lib/api/client.dart` | `createProduct({..., int? stock})` (Form; omit key bila null); `setStock(id, int?)` → `PATCH /umkm/products/{id}/stock` (JSON body `{stock: int\|null}`) |
| `mobile/lib/products/product_controller.dart` | `create({..., int? stock})`; `setStock(id, int?) -> Future<bool>` (submitting → reload → error, pola existing) |
| `mobile/lib/screens/products_screen.dart` | Form: field **"Stok (opsional)"**; kartu: badge status stok (Stok:N/Menipis/Habis/Tak-dilacak) di sebelah pill kode barang; ikon **edit** → dialog angka set/restock |
| `mobile/test/support/fakes.dart` | FakeApi: override `listProducts`/`createProduct`(+`lastCreateStock`)/`setStock`(+`lastSetStock`/`setStockError`) |
| `mobile/test/products/product_controller_test.dart` (baru) | create(stock) diteruskan; setStock sukses (reload+clear error) & error (pesan+false) |
| `mobile/test/screens/products_screen_test.dart` (baru) | form punya field stok; badge 4 state; edit dialog: save→setStock(id,N), Batal→no-op, kosong→setStock(id,null) |

**NOL dep baru. Tidak menyentuh backend/Python.**

### Keputusan desain

| Topik | Keputusan |
|---|---|
| Badge stok | `null`→Tak dilacak (netral), `0`→Habis (error), `≤5`→Menipis (warning), else `Stok: N` (lime). Urutan cek: null → 0 → ≤5 → else (0 tak ketelan ≤5) |
| Field form | **Opsional**; kosong → `null` (tak-dilacak). Non-numerik → `int.tryParse` → null |
| Edit/restock | **Dialog angka** (keputusan Steven, bukan stepper inline). Batal = no-op; field kosong disimpan = jadikan tak-dilacak |
| Transport null | create (multipart) **omit** key `stock` bila null; setStock (PATCH JSON) kirim `{"stock": null}` eksplisit — dua-duanya benar per kontrak backend (`Form(None)` vs `Field(default=None, ge=0)`) |

### Catatan teknis
- **Dialog `TextEditingController` di-dispose deferred satu frame** (`addPostFrameCallback`): pop-future AlertDialog resolve SEBELUM exit-transition selesai me-rebuild TextField, jadi `ctrl.dispose()` sinkron crash (ChangeNotifier used-after-dispose). Ada komentar eksplisit di kode supaya tak "disederhanakan" jadi dispose sinkron. Follow-up opsional: bungkus konten dialog jadi StatefulWidget yang own controller + dispose di `State.dispose()` (lebih robust, pola `voice_parsed.dart`).
- Enforcement stok (self-order blokir / kasir warning) **sudah di backend 1.1a**; UI ini murni menampilkan/mengatur — tak ada logika enforcement di client.
- Negative typed stock: tak ada guard client (soft-keyboard number saja); backend `ge=0` + create `stock<0` yang menolak. Spec-sanctioned.

### Verifikasi (proven — output firsthand)
- `flutter test` → **135 passed** (baseline 124 pra-slice + 11 baru/fix).
- `flutter analyze --no-fatal-infos` → **7 issues** (pre-existing infos: localeId deprecation + tool/parser_check print), **0 baru**.
- Final whole-branch review (opus): **Ready to merge = YES WITH FIXES**; fix-wave (dispose ctrl deferred + cancel/untracked tests) applied + re-review Approved; comment hardening added.

## 🔴 Blocker
- TIDAK ADA.

## 📌 Out-of-scope / deferred
- **Blokir self-order end-to-end** → **Fase 3** (route self-order memanggil seam backend 1.1a).
- Optimistic stock update (setStock kini full-reload); validasi input stok lebih ketat (decimal/paste → error) → follow-up bila perlu.
- **GATE proyek (Fase 0):** redeploy `main` → VPS + verifikasi live (11 analisis / briefing / ask / sheets) **sebelum merge Fase 3**. VPS saat cek 2026-07-21 masih deploy lama (4-analisis).
