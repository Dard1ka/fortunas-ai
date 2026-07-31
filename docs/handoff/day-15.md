# Handoff Day 15 — Inbox Pesanan UMKM + Hardening Jalur Publik (Slice 1, Task 1–11)

**Dev slice ini:** Go Steven Sanjaya (rotasi 3-dev via agen, estafet task 1–10; Task 11 = gate verifikasi + handoff)
**Tanggal:** 2026-07-31
**Branch:** `feat/umkm-order-inbox` (dari `main` @ `9526ffc`) — 23 commit, HEAD `544abf2` + 1 commit dokumentasi (Task 11)
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
   webhook melapor `failed`/`refund`/`chargeback` pada pesanan yang sudah pernah lunas.

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
- Backfill migrasi: baris lama berstatus `paid`/`accepted`/`rejected`/`completed` diberi `paid_at = updated_at`
  — tanpa ini, order lama yang di-replay webhook-nya akan lolos guard `paid_at is None` dan stoknya terpotong
  ulang.
- Baik `mark_paid` maupun `restore_stock` memakai **compare-and-set** (baca-cek-tulis dilipat jadi satu
  `UPDATE ... WHERE paid_at IS NULL` / `WHERE stock_restored_at IS NULL`), bukan read-then-write — ini
  keputusan eksplisit Steven (lihat Utang, bagian race, untuk konsekuensi lanjutannya).

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
  `pytest tests/ -q` → **268 passed** (baseline 232 + 36 baru dari slice ini).
- **Mobile:** `flutter analyze --no-fatal-infos` → **7 info** (semua pre-existing, exit 0, nol baru).
  `flutter test` → **170 passed** (baseline 146 + 24 baru dari slice ini).
- **Migrasi 010 di DB kosong (SQLite fresh, bukan in-memory test):** `alembic upgrade head` jalan mulus dari
  revisi kosong sampai `010` (`alembic current`/`alembic heads` keduanya `010 (head)`, single head, exit 0).
  Kolom `public_orders` pasca-migrasi memuat `paid_at` dan `stock_restored_at`, dikonfirmasi lewat
  introspeksi SQLAlchemy langsung. Ini penting karena **test suite tidak pernah menjalankan Alembic** —
  test pakai SQLite in-memory + `Base.metadata.create_all()`, jadi jalur migrasi murni cuma teruji manual.

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
4. **Race accept-vs-refund dijaga bentuk kode saja, TIDAK ADA test yang mengcovernya.** Skenario: UMKM menekan
   Terima tepat saat webhook Midtrans melapor refund/chargeback untuk pesanan yang sama. `cancel_by_gateway`
   memakai compare-and-set yang digating pada **status** (`_GATEWAY_CANCELLABLE = {pending_payment, paid}`,
   bukan `accepted`) — begitu status sudah `accepted`, gateway tidak bisa lagi menimpanya jadi `cancelled`.
   Ini benar secara desain, tapi **dua writer bersamaan tidak praktis direproduksi lewat `TestClient` di atas
   SQLite** (butuh dua thread/proses sungguhan menulis bersamaan), jadi tidak ada test yang benar-benar
   membuktikan atomisitasnya di bawah beban race nyata. Test `refund-after-accept` yang ada **tetap hijau**
   bahkan terhadap versi read-then-write yang racy (diverifikasi reviewer Task 5) — jadi kehijauan test itu
   **bukan bukti** jaminan race, hanya bukti bahwa urutan sekuensial (bukan konkuren) sudah benar. Jaminan
   sesungguhnya bersandar pada bentuk `UPDATE ... WHERE status IN (...)` atomik di level SQL, bukan pada
   sesuatu yang pernah diuji berjalan konkuren.

### Catatan tambahan (minor, untuk konteks — lihat ledger untuk daftar lengkap)
- `GET /public/orders/{payment_order_id}` (poll status) tidak punya rate limiter sendiri — risiko PII sudah
  ditutup oleh entropi 128 bit, sisanya adalah permukaan DoS generik (lookup DB tanpa auth) yang idealnya
  ditangani di reverse proxy.
- Keying rate-limit per-IP diam-diam bergantung pada konfigurasi proxy (`X-Forwarded-For` dipercaya dari
  `127.0.0.1`). Sudah benar untuk deploy hari ini, tapi berubah kalau `--no-proxy-headers` atau ada hop CDN
  baru — akan meruntuhkan semua pelanggan ke satu ember rate-limit.
- Docstring `order_repo._update` masih mengklaim satu-satunya penulis baris pesanan, padahal `mark_paid` &
  `restore_stock` kini punya jalur compare-and-set sendiri di luar `_update` — kosmetik, belum diperbaiki.

---

## Files yang diubah (Task 11 saja)

- `docs/handoff/FASE2_pesan_pelanggan.md` — kontrak `id` → `payment_order_id` (2 baris tabel endpoint + 2
  baris TODO Slice 2e + 1 baris signature client mobile + 1 catatan baru).
- `docs/handoff/day-15.md` — dokumen ini (baru).

Task 1–10 (kode fitur & fix) sudah di-commit sebelumnya di 23 commit HEAD `544abf2` — lihat daftar commit di
`git log 9526ffc..544abf2` dan detail per-task di `progress.md`.
