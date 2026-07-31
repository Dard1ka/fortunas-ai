# Handoff Day 15 — Inbox Pesanan UMKM + Hardening Jalur Publik (Slice 1, Task 1–11)

**Dev slice ini:** Go Steven Sanjaya (rotasi 3-dev via agen, estafet task 1–10; Task 11 = gate verifikasi + handoff)
**Tanggal:** 2026-07-31
**Branch:** `feat/umkm-order-inbox` (dari `main` @ `9526ffc`) — 23 commit fitur (HEAD `544abf2`) + 1 commit
dokumentasi (Task 11, `9f2a68d`) + 1 commit ronde perbaikan review akhir (§Ronde perbaikan review akhir)
**PR:** belum dibuka — Step 6–8 (verifikasi akun `gh`, push, buka PR, tunggu CI) dipegang controller, bukan Task 11.

---

## Apa yang dibangun

**Masalah yang ditutup:** pelanggan bisa memesan lewat kode UMKM dan bayar online (Fase 2, PR #23), tapi UMKM
tidak punya cara melihat pesanan itu masuk, apalagi menerima/menolaknya. Uang bisa masuk, barang tidak pernah
keluar. Slice ini menutup loop tersebut dengan **inbox pesanan** (backend + Flutter), dan sekalian
mengeraskan (harden) empat titik lemah di jalur publik yang sudah ada sejak Fase 2.

### 1. Inbox pesanan (fitur utama)
- Backend: router baru `app/api/routes/orders.py` (`GET/POST /umkm/orders/...`, ber-auth tenant).
- Mobile: modul `mobile/lib/orders/` (state + `OrderController` Riverpod) + layar `OrdersScreen` di
  route `/orders` + kartu **"Pesanan Masuk"** dengan badge jumlah di home (`OrdersHomeCard`,
  `pendingOrderCountProvider`).
- UMKM sekarang bisa: lihat pesanan yang butuh tindakan, **Terima**, **Tolak**, **Selesaikan**.

### 2. Empat perbaikan (hardening) yang dibonceng bareng
Keempatnya diperlukan supaya inbox yang baru dibangun tidak berdiri di atas jalur publik yang rapuh:

1. **Idempotensi `mark_paid`** (§2.1) — kolom penanda `paid_at` + compare-and-set, supaya webhook Midtrans
   yang dikirim ulang tidak memotong stok dua kali.
2. **PII lookup publik** (§2.2) — `payment_order_id` naik dari `token_hex(4)` (32 bit) ke `token_hex(16)`
   (128 bit), menutup risiko enumerasi URL status yang membocorkan nama & no. HP pelanggan.
3. **Guard webhook + `compare_digest`** (§2.3) — signature Midtrans dibandingkan sebagai bytes (`hmac.compare_digest`),
   dan payload sembarang (bukan JSON, bukan objek, `signature_key` non-ASCII/lone-surrogate) dibalas `400`,
   bukan `500` — endpoint ini tanpa auth, jadi crash tak tertangani = permukaan yang terbuka ke internet.
4. **Pengembalian stok otomatis** (§2.4) — `restore_stock` dipanggil saat UMKM menolak pesanan **dan** saat
   webhook melapor `failed`/`refund`/`chargeback` pada pesanan yang sudah pernah lunas — kecuali pesanan yang
   sudah `completed` (lihat ronde perbaikan review akhir #3).

### 3. Ronde perbaikan review akhir (review seluruh branch, sebelum PR)
Lima temuan dari review whole-branch, semuanya disetujui Steven:

1. **`apply_action` pindah ke compare-and-set** (§Race, Utang #4) — satu-satunya penulis status yang masih
   baca-lalu-tulis. Sekarang `UPDATE ... WHERE id AND tenant_id AND status IN (_ALLOWED_FROM[aksi])`, dan
   `reject` mengembalikan stok **hanya kalau klaimnya menang** (dulu: restore lebih dulu, tanpa syarat).
2. **Regresi test untuk filter default inbox** — `_ACTIONABLE` bisa dipangkas jadi `[STATUS_PAID]` dengan
   268/268 tetap hijau, padahal itu membuat pesanan hilang dari inbox begitu UMKM menekan Terima dan tombol
   **Selesai** tak pernah terjangkau. Sekarang dipin di `test_inbox_action_flow_paid_accept_complete`.
3. **Stok pesanan `completed` tidak lagi dikembalikan webhook** — chargeback pada pesanan yang barangnya sudah
   diserahkan dulu menambah stok yang tak pernah kembali. `cancel_by_gateway` memang membekukan *status*
   pesanan completed, tapi `restore_stock` jalan di panggilan terpisah dan butuh pagar sendiri.
   Sekalian didokumentasikan di kode: **`partial_refund` disengaja diperlakukan sebagai pembatalan penuh**
   untuk MVP (`payment._map_status` memetakan semua status tak dikenal ke `failed`), diterima karena
   pengembalian uang memang manual di luar sistem. Model mobile (`models.dart`) sudah mengenal
   `partial_refund`, jadi ketidaksepakatan backend↔klien ini sekarang tercatat, bukan implisit.
4. **Backfill migrasi 010 diperluas ke `cancelled`** — pesanan yang lunas lalu di-refund sebelum migrasi tetap
   `paid_at IS NULL`, jadi replay notifikasi settlement-nya masih bisa memotong stok dua kali. Dikerjakan
   sekarang justru karena migrasi 010 **belum pernah menyentuh produksi**; setelah deploy ini butuh migrasi 011.
5. **Klaim basi di dokumen ini** diperbaiki: Utang #4 (race dijamin "bentuk kode") ditulis ulang, dan catatan
   soal docstring `order_repo._update` dibuang — docstring itu sudah menggambarkan pemisahan CAS dengan benar,
   klaimnya tersalin dari catatan era sebelumnya tanpa dicek ulang. Ikut disegarkan: baris-baris yang jadi basi
   **karena perbaikan 1–4 di atas** (daftar penulis CAS, daftar status backfill, §2.4, angka verifikasi).
   Utang #5 baru ditambahkan (`paid_at` ≠ stok pernah dipotong).

---

## Endpoint baru & transisi status

| Method | Path | Aksi | Transisi status |
|---|---|---|---|
| GET | `/umkm/orders?status=` | List inbox (auth tenant) | tanpa filter → `paid` + `accepted` (yang butuh tindakan); `?status=all` → semua; `?status=<x>` → satu status |
| POST | `/umkm/orders/{order_id}/accept` | UMKM menyanggupi pesanan | `paid` → `accepted` |
| POST | `/umkm/orders/{order_id}/reject` | UMKM menolak pesanan | `paid` → `rejected` (+ `restore_stock` otomatis) |
| POST | `/umkm/orders/{order_id}/complete` | UMKM menandai selesai | `accepted` → `completed` |

Status penuh: `pending_payment → paid → accepted/rejected → completed` (plus `expired`/`cancelled` milik
sistem — job kedaluwarsa & webhook gateway, **bukan** aksi UMKM).

`404` dipakai untuk pesanan tak ada **maupun** milik tenant lain (bukan `403`) — `403` akan mengakui bahwa
pesanan itu ada, membocorkan keberadaannya lintas tenant.

---

## Dua kolom penanda: `paid_at` & `stock_restored_at`

Ditambahkan lewat migrasi `010_public_order_stock_markers.py`. Alasannya murni **idempotensi**:

- Tanpa `paid_at`, webhook Midtrans yang terkirim dua kali (retry gateway, at-least-once delivery) akan
  memanggil `mark_paid` dua kali → stok terpotong dua kali untuk satu pesanan.
- Tanpa `stock_restored_at`, kombinasi tolak-lalu-refund (atau refund ganda dari gateway) bisa mengembalikan
  stok lebih dari sekali → stok "gemuk" (lebih banyak dari yang sebenarnya ada).
- Backfill migrasi: baris lama berstatus `paid`/`accepted`/`rejected`/`completed`/`cancelled` diberi
  `paid_at = updated_at` — tanpa ini, order lama yang di-replay webhook-nya akan lolos guard `paid_at is None`
  dan stoknya terpotong ulang. `cancelled` ikut karena pesanan yang lunas lalu di-refund berakhir di status itu;
  konsekuensi & trade-off-nya ditulis di komentar migrasinya.
- **Keempat** penulis baris pesanan memakai **compare-and-set** (baca-cek-tulis dilipat jadi satu `UPDATE`
  bersyarat, bukan read-then-write) — ini keputusan eksplisit Steven, diterapkan berulang: `mark_paid`
  (`WHERE paid_at IS NULL`), `restore_stock` (`WHERE stock_restored_at IS NULL`), `cancel_by_gateway` dan
  `apply_action` (keduanya `WHERE status IN (...)`). Lihat Utang #4 untuk apa yang dijamin dan apa yang tidak.

## Keputusan: endpoint per-aksi, bukan `PATCH` generik

`orders.py` sengaja dibuat sebagai tiga endpoint (`/accept`, `/reject`, `/complete`), bukan satu
`PATCH /umkm/orders/{id}` yang menerima `{"status": ...}`. Dengan `PATCH` generik, UMKM (klien) bisa
mengirim `status=expired` atau `status=cancelled` — dua status yang seharusnya hak eksklusif sistem (job
kedaluwarsa pesanan & webhook gateway). Endpoint per-aksi memberi penyaringan itu gratis lewat routing, dan
tiap aksi punya prasyaratnya sendiri di `order_repo._ALLOWED_FROM` (satu sumber kebenaran tabel transisi).

---

## Perubahan BREAKING: kunci publik `payment_order_id`

`docs/handoff/FASE2_pesan_pelanggan.md` sebelumnya masih mendokumentasikan `GET /public/orders/{id}`
berkunci **id berurutan** (integer platform-wide). Kunci itu sudah mati sejak Task 5 slice ini — kunci nyata
sekarang adalah **`payment_order_id`** (string, `ORD-{id}-{32 hex}`, 128 bit acak sejak perbaikan #2 di atas).

**Slice 3 (UI pelanggan Flutter, belum dibangun) WAJIB memakai `payment_order_id`, bukan `id`, untuk:**
- `GET /public/orders/{payment_order_id}` (poll status)
- `GET|POST /public/orders/{payment_order_id}/simulate-pay` (mode simulasi)

`payment_order_id` ikut dikembalikan di respons `POST /public/umkm/{code}/orders` — **itu satu-satunya cara**
pelanggan tahu URL status pesanannya. Dokumen `FASE2_pesan_pelanggan.md` sudah diperbaiki di kedua tempat
(tabel endpoint + langkah "poll status" di TODO Slice 2e), plus satu catatan baru yang menjelaskan hal ini.
Kalau dibiarkan seperti sebelumnya, developer Slice 3 akan membangun UI di atas URL yang membalas `404`.

`PublicOrderResponse.id` (integer sekuensial) masih ikut di payload — sengaja tidak dibuang di slice ini,
tapi kandidat kuat untuk dihapus saat Slice 3 (nol klien yang membacanya hari ini; membocorkan hitungan
pesanan platform-wide ke pemanggil tanpa auth).

---

## Verifikasi (proven — output firsthand, venv CI-mirror)

- **Backend:** `ruff check app tests --extend-exclude=app/migrations` → `All checks passed!`.
  `pytest tests/ -q` → **271 passed** (baseline 232 + 36 dari slice ini + 3 dari ronde perbaikan review akhir).
- **Mobile:** `flutter analyze --no-fatal-infos` → **7 info** (semua pre-existing, exit 0, nol baru).
  `flutter test` → **170 passed** (baseline 146 + 24 baru dari slice ini). Ronde perbaikan review akhir tak
  menyentuh `mobile/` sama sekali, jadi kedua angka ini tidak berubah.
- **Migrasi 001→010 di DB kosong (SQLite fresh, bukan in-memory test):** `alembic upgrade head` jalan mulus dari
  revisi kosong sampai `010` (`alembic current`/`alembic heads` keduanya `010 (head)`, single head, exit 0).
  Kolom `public_orders` pasca-migrasi memuat `paid_at` dan `stock_restored_at`, dikonfirmasi lewat
  introspeksi SQLAlchemy langsung. Ini penting karena **test suite tidak pernah menjalankan Alembic** —
  test pakai SQLite in-memory + `Base.metadata.create_all()`, jadi jalur migrasi murni cuma teruji manual.
- **Backfill migrasi 010 di DB BERISI (baru, ronde perbaikan review akhir):** verifikasi DB-kosong di atas
  membuktikan DDL-nya jalan tapi **tidak pernah menyentuh satu baris pun** — nol baris, jadi predikat
  backfill-nya sendiri belum teruji. Diulang dengan benar: `upgrade 009` → seed satu baris per status → `upgrade
  head`. Hasilnya `paid`/`accepted`/`rejected`/`completed`/`cancelled` dapat `paid_at = updated_at`, sementara
  `pending_payment` dan `expired` tetap `NULL` — sesuai maksud. Dengan predikat lama (tanpa `cancelled`), baris
  `cancelled` tetap `NULL`, mengonfirmasi lubang yang perbaikan #4 tutup.

---

## 🔴 Blocker

- TIDAK ADA. Semua gate lokal (backend, mobile, migrasi) hijau.

---

## 📌 Utang yang diterima sadar (accepted debt)

Ditulis apa adanya sesuai ledger (`​.superpowers/sdd/2026-07-31-slice1-inbox-pesanan-umkm/progress.md`) —
kalau sesuatu tercatat di sana sebagai belum teruji atau trade sadar, begitu juga di sini.

1. **Analitik belum menghitung pesanan online.** `complete_order` (`accepted → completed`) belum menjembatani
   ke BigQuery (`checkout_service.py`) — itu scope **Slice 2**. Konsekuensinya: **omzet under-reported**
   sampai Slice 2 selesai; laporan analitik UMKM hari ini tidak melihat transaksi dari jalur pesan-online sama
   sekali, hanya dari checkout kasir langsung.
2. **Refund uang ke pelanggan = manual, pengembalian stok = otomatis.** Saat UMKM menekan Tolak (atau webhook
   melapor refund/chargeback), `restore_stock` jalan otomatis, tapi **tidak ada** alur pengembalian uang ke
   pelanggan — itu dilakukan manual di luar sistem (mis. transfer langsung oleh UMKM). Dialog tolak di mobile
   sudah menyebut ini eksplisit ("stok kembali otomatis, uang manual"), tapi tetap ini adalah kesenjangan
   proses, bukan hanya catatan UI.
3. **Rate limit order publik dihitung per uvicorn worker dan reset saat restart.** `_order_hits` adalah
   dict in-process (module-level), bukan penyimpanan bersama (Redis, dll). Dengan `--workers N`, batas efektif
   per IP jadi `~N × 10/menit`, bukan `10/menit` yang didokumentasikan di komentar kode. Ini didisklos di
   komentar `public.py`, dan dianggap cukup untuk skala MVP — tapi kalau VPS dinaikkan ke multi-worker tanpa
   penyesuaian, batas sebenarnya naik diam-diam.
4. **Race accept-vs-refund: dijaga `UPDATE` bersyarat, sudah dipin test — tapi bukan test konkurensi nyata.**
   Skenario: UMKM menekan Terima tepat saat webhook Midtrans melapor refund/chargeback untuk pesanan yang sama.
   **Yang menjamin sekarang** adalah compare-and-set: `cancel_by_gateway` **dan** `apply_action` (sejak ronde
   perbaikan review akhir) sama-sama menulis lewat satu `UPDATE ... WHERE status IN (...)` lalu memeriksa
   `rowcount`, jadi penulis yang statusnya sudah bergerak di bawahnya akan kalah klaim dan pulang tanpa efek.
   Sebelum ronde itu, `apply_action` masih baca-lalu-tulis tanpa syarat — jadi jaminannya memang cuma "bentuk
   kode", dan `accept` bisa menimpa pembatalan gateway.

   **Yang sudah dicover test:** dua test deterministik
   (`test_accept_does_not_overwrite_gateway_cancel_landing_mid_window`,
   `test_reject_does_not_restore_stock_when_claim_lost`) menaruh penulis lain PERSIS di jendela baca→tulis
   dengan mem-patch `get_order_for_tenant` supaya mengembalikan dict basi (pola sama dengan
   `test_sweep_survives_key_removed_during_iteration`). Keduanya **gagal** terhadap versi tulis-tanpa-syarat
   (status jadi `accepted` di atas baris `cancelled`; stok kembali walau klaim reject kalah) dan lulus setelah
   CAS — jadi kali ini kehijauannya memang bukti, bukan kebetulan.

   **Yang TIDAK dicover:** tetap tidak ada test dengan dua writer sungguhan berjalan bersamaan (SQLite +
   `TestClient` satu thread). Atomisitas `UPDATE`-nya sendiri adalah properti database, bukan sesuatu yang
   diverifikasi di sini, dan perilakunya di bawah locking Postgres nyata belum pernah dijalankan. Test yang ada
   membuktikan **urutan klaim-lalu-bertindak** benar dan tulisan yang kalah tidak punya efek; bukan bahwa
   database-nya benar. Catatan lama masih berlaku juga: `test_webhook_refund_after_accept_keeps_accepted_status`
   tetap hijau bahkan terhadap versi racy, jadi test itu sendiri bukan bukti apa pun soal race.

   Sisa inkonsistensi kecil: `cancel_by_gateway` memeriksa `rowcount == 1`, sementara `mark_paid` dan
   `apply_action` memakai `rowcount != 0`. `!= 0` yang dipilih untuk `apply_action` aman terhadap driver yang
   melaporkan `-1` ("tak tahu"); `== 1` di `cancel_by_gateway` akan menganggap setiap klaim kalah di driver
   semacam itu. Belum diseragamkan — tak ada driver seperti itu yang dipakai hari ini (SQLite & psycopg2
   keduanya melaporkan angka sesungguhnya).

5. **`paid_at` cuma berarti "klaim menang", BUKAN "stok pernah dipotong" → `restore_stock` bisa menambah stok
   yang tak pernah diambil.** `restore_stock` menggating pada `paid_at IS NOT NULL`, dan `paid_at` diisi oleh
   klaim CAS di `mark_paid` **sebelum** stok dipotong. Nilai balik `product_repo.decrement_by_ids` dibuang di
   `mark_paid` (tidak diperiksa, tidak dicatat), padahal `decrement_by_ids` mengembalikan `ok=False` dan
   **me-rollback seluruh pemotongan** begitu ada satu item yang stoknya kurang. Akibatnya pesanan bisa berdiri
   dengan `paid_at` terisi tapi stok tak pernah terpotong sama sekali — dan `reject` atau refund yang datang
   belakangan akan "mengembalikan" stok itu, menaikkan angka stok di atas yang sebenarnya ada. Jalur yang sama
   juga terbuka lewat backfill migrasi 010 untuk baris `cancelled` yang belum pernah lunas (lihat komentar di
   `010_public_order_stock_markers.py`).

   **Belum diperbaiki, sengaja.** Perbaikan yang benar adalah penanda KETIGA (`stock_decremented_at`, diisi
   hanya setelah `decrement_by_ids` melapor `ok=True`) + migrasi `011`, dan `restore_stock` menggating pada
   penanda itu, bukan pada `paid_at` — plus keputusan produk soal apa yang harus terjadi ketika pembayaran
   masuk tapi stok tak cukup (hari ini: senyap). Keputusan Steven: itu **slice sendiri**, bukan tempelan di
   slice ini.

### Catatan tambahan (minor, untuk konteks — lihat ledger untuk daftar lengkap)
- `GET /public/orders/{payment_order_id}` (poll status) tidak punya rate limiter sendiri — risiko PII sudah
  ditutup oleh entropi 128 bit, sisanya adalah permukaan DoS generik (lookup DB tanpa auth) yang idealnya
  ditangani di reverse proxy.
- Keying rate-limit per-IP diam-diam bergantung pada konfigurasi proxy (`X-Forwarded-For` dipercaya dari
  `127.0.0.1`). Sudah benar untuk deploy hari ini, tapi berubah kalau `--no-proxy-headers` atau ada hop CDN
  baru — akan meruntuhkan semua pelanggan ke satu ember rate-limit.
- `order_repo.set_status` kini **tak punya pemanggil produksi** sejak `apply_action` pindah ke compare-and-set.
  Dibiarkan ada (masih disebut di `FASE2_pesan_pelanggan.md` §repo), tapi docstring-nya sekarang memperingatkan
  eksplisit: jangan pakai untuk transisi — ia menulis status tanpa syarat. Penulis status berikutnya (mis. job
  kedaluwarsa pesanan yang belum dibangun) harus mengikuti pola CAS di `apply_action`, bukan memanggil ini.

---

## Files yang diubah (Task 11 saja)

- `docs/handoff/FASE2_pesan_pelanggan.md` — kontrak `id` → `payment_order_id` (2 baris tabel endpoint + 2
  baris TODO Slice 2e + 1 baris signature client mobile + 1 catatan baru).
- `docs/handoff/day-15.md` — dokumen ini (baru).

## Files yang diubah (ronde perbaikan review akhir)

- `app/order_repo.py` — `apply_action` ke compare-and-set + `reject` restore stok hanya bila klaim menang;
  docstring `_update` & `set_status` diselaraskan dengan kenyataan.
- `app/api/routes/public.py` — restore stok webhook `failed` digating `status != completed`; keputusan
  `partial_refund` didokumentasikan di titik kejadian.
- `app/migrations/versions/010_public_order_stock_markers.py` — backfill `_PAID_ONWARDS` + `cancelled`.
- `tests/test_umkm_orders.py` — 3 test baru (2 race `apply_action`, 1 chargeback pesanan completed) + pin
  filter default inbox di `test_inbox_action_flow_paid_accept_complete`.
- `docs/handoff/day-15.md` — Utang #4 ditulis ulang, Utang #5 baru, catatan `_update` dibuang, angka verifikasi
  diperbarui.

Task 1–10 (kode fitur & fix) sudah di-commit sebelumnya di 23 commit HEAD `544abf2` — lihat daftar commit di
`git log 9526ffc..544abf2` dan detail per-task di `progress.md`.
