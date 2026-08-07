# Handoff Day 17 — Pesan Publik: QRIS Statis + Jembatan BigQuery + UI Pelanggan

**Dev slice ini:** Gregorius Darrel Andika Setya (`Dard1ka`)
**Tanggal:** 2026-08-07
**Branch:** `feat/public-order-qris`
**Commit kerja:** `4a84ef5` (28 file, +1854/-51) · **commit dokumen:** `5943661`
**PR:** **#25, sudah MERGED** ke `main` sebagai squash `5954796`.

> **Catatan penamaan berkas.** Dokumen ini ditulis dengan judul "Day 16" dan nama berkas
> `docs/handoff/day-16.md` di branch `feat/public-order-qris`. Nama itu **bertabrakan**:
> `main` sudah memiliki `docs/handoff/day-16.md` untuk slice paralel *PWA-only + Responsive
> Shell* (PR #26). Dua slice memang dikerjakan bersamaan oleh dua dev, dan keduanya
> menamai dirinya "day 16".
>
> Berkas ini di-rename jadi `day-17.md` saat dipindahkan (2026-08-07) karena tanggalnya
> memang satu hari setelah dokumen PWA (2026-08-06). **Isi dan penulisnya tidak diubah**
> — hanya encoding UTF-8 yang rusak diperbaiki, dan blok "Status setelah merge" di bawah
> ditambahkan. Slice PWA tetap di [`day-16.md`](day-16.md).

---

## 1. Apa yang dikerjakan di sesi ini

Tiga potong pekerjaan pada alur **pesan-publik pelanggan** (pelanggan memesan lewat
KODE UMKM, tanpa akun), semua di branch `feat/public-order-qris`:

### Slice 2 — Jembatan pesanan `completed` → BigQuery

Masalah: `public_orders` hidup di DB relasional, tapi 11 analisis + `/ask` + `/briefing`
+ riwayat semuanya baca BigQuery. Sebelumnya omzet pesan-online tak terhitung sama sekali.

- `app/services/checkout_service.py` — fungsi baru `persist_completed_order(order, tenant)`
  me-reuse `persist_basket`. Dipanggil dari `routes/orders.complete_order` setelah status
  jadi `completed`.
- `PublicOrder.customer_user_id` (nullable) + migrasi `011`. Ditangkap best-effort di
  `create_public_order` dari bearer pelanggan opsional (tamu tetap bisa pesan). Saat
  `completed` + login → `record_purchase` + `ensure_membership` (best-effort).
- Penulisan BigQuery **best-effort** (pesanan sudah completed dulu; kegagalan BQ tak
  membatalkan penyelesaian). Poin loyalti untuk pesanan online BELUM (backlog).

### Slice 2e — UI Flutter pelanggan (pesan tanpa akun)

- Route publik `/order` → `mobile/lib/screens/public_order_screen.dart` (satu layar, 3
  fase: kode → menu grid bergambar + cari client-side → keranjang → checkout → bayar → status)
  + `mobile/lib/public_order/public_order_controller.dart` (Riverpod).
- 4 method client `/public/*` di `mobile/lib/api/client.dart`; model `PublicUmkm`/
  `PublicMenuProduct`/`PublicOrder` di `models.dart`.
- `AuthInterceptor` skip `/public/*` (pelanggan anonim); entry "Pesan tanpa akun" di
  `login_screen.dart`; whitelist `/order` di `auth_redirect.dart`.

### Pivot pembayaran → QRIS STATIS (Midtrans = future scope)

- `payment.create_charge` sekarang SELALU `provider="qris_static"`, redirect ke
  `/public/orders/{poid}/confirm-payment`. Kode Midtrans disimpan dorman:
  `payment._create_charge_midtrans` + `verify_notification` + webhook route tetap ada.
- Endpoint `simulate-pay` → **`confirm-payment`**: pelanggan tekan "Saya sudah bayar" →
  `mark_paid`. **INI KLAIM, BUKAN BUKTI** — QRIS statis tak punya callback, jadi UMKM
  WAJIB verifikasi dana masuk di app QRIS-nya sebelum menekan Terima (Tolak → stok kembali).
- Mobile: layar order menampilkan `mobile/assets/payments/qr.jpeg` (Image.asset +
  placeholder errorBuilder bila file belum ada) + total + tombol "Saya sudah bayar".
- Webview Snap (`snap_payment_screen.dart`) + `webview_flutter` + `afterSnapReturn()`
  DISIMPAN dorman untuk future Midtrans (tak dirujuk layar sekarang).
- **Fix bug laten:** `mobile/android/app/src/main/AndroidManifest.xml` tambah izin
  `INTERNET` — tanpa ini RELEASE build tak punya akses jaringan sama sekali.

---

## 2. Status test (klaim penulis slice)

- Backend `pytest`: **276 passed**.
- Flutter `flutter test`: **186 passed**; `flutter analyze` bersih (2 *info* deprecation lama, bukan dari kerja ini).
- Migrasi alembic `001`–`011` jalan bersih di DB fresh.
- Smoke end-to-end aplikasi penuh: alur register → menu → pesan → bayar → accept → complete OK.

> Angka-angka ini **belum diverifikasi ulang** setelah `main` menggabungkan slice PWA
> (PR #26). Jalankan ulang sebelum menyandarkan apa pun padanya.

---

## 3. Arsitektur penting (biar tak salah asumsi)

**Multi-tenant, BUKAN database per-UMKM:**

- Data operasional (produk, pesanan, poin, dll) = **satu DB relasional bersama**
  (`DATABASE_URL`), dipisah per-UMKM lewat kolom **`tenant_id`** di tiap query.
- Produk ada di tabel `products`; pembeda antar-UMKM = `tenant_id`; `stock_code` unik
  per-tenant (`UniqueConstraint(tenant_id, stock_code)`). Gambar produk di disk
  `PRODUCT_IMAGE_DIR/{tenant_id}/`.
- Data transaksi/analitik = **BigQuery, satu dataset bersama, tabel ber-prefix per-UMKM**
  (`{project}.{dataset}.{table_prefix}_transactions|customers`).

**State pesanan publik:** `pending_payment → paid → accepted/rejected → completed`
(+ `expired`/`cancelled` milik sistem). Transisi aksi UMKM lewat
`order_repo.apply_action` (compare-and-set), JANGAN `set_status`. Stok dipotong saat `paid`
(`mark_paid`, idempoten via `paid_at`).

---

## 4. Backlog / belum dikerjakan

- **Poin loyalti** untuk pesanan online (sekarang baru `record_purchase`, poin belum).
- **Notifikasi FCM** UMKM saat order baru masuk (infra `device_tokens`/`notify_repo.py` ada).
- **Job expiry** `pending_payment` yang tak dibayar → `expired`.
- **Menu self-order per-kategori**.
- **Midtrans dinamis (future):** QRIS/Snap otomatis via aggregator — kode dorman tinggal diaktifkan.
- **QRIS per-UMKM:** sekarang `qr.jpeg` tunggal (satu QR untuk semua); idealnya QR per-tenant.
- Utang day-15: rate-limit multi-worker (Redis), retry tulis BigQuery, fallback webview Flutter Web.

---

## 5. Cara jalan lokal (setelah clone)

```bash
cd fortunas-ai
python -m venv .venv && .venv\Scripts\pip install -r requirements.txt
copy .env.example .env          # ISI dari HANDOVER.md / vault (JANGAN dari git)
# taruh credentials/fortunas-service-account.json (dari kanal aman)
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m pytest -q

cd mobile
flutter pub get
# taruh gambar QRIS toko di mobile/assets/payments/qr.jpeg
flutter test
flutter run --dart-define=FORTUNAS_API=http://10.0.2.2:8000   # emulator Android
```

---

## 6. Catatan penyerahan

- Credentials TIDAK di-commit (`.gitignore` menjaga `.env`, `credentials/`,
  `*service-account*.json`). Bagikan lewat vault/kanal terenkripsi.
- Detail hosting/domain/IP/cPanel ada di **`HANDOVER.md`**.

---

## 7. Status setelah merge (ditambahkan 2026-08-07 saat memindahkan dokumen)

Blok ini bukan tulisan penulis slice. Ditambahkan karena beberapa baris di atas sudah
basi begitu slice ini masuk `main`, dan dokumen handoff yang basi lebih berbahaya daripada
tidak ada dokumen.

| Baris asli | Status sebenarnya per 2026-08-07 |
|---|---|
| "Branch sudah di-push ke GitHub, **belum di-merge**" | **Sudah merged** — PR #25, squash `5954796` |
| "PR: buka di …/pull/new/feat/public-order-qris" | Sudah tidak berlaku; `main` @ `41d595f` sudah memuat kodenya |
| "`HANDOVER.md` yang di-gitignore" | ⚠️ **Tidak di-gitignore di `main`.** Baris `HANDOVER.md` ada di commit `5943661` yang tidak ikut ter-squash. `main` `.gitignore:76` hanya `HANDOVER.txt`. Repo ini **PUBLIC** |
| "`--dart-define=FORTUNAS_API=https://api.fortunas.id`" | Topologi diganti jadi `app.fortunas.id` **same-origin** (keputusan Steven 2026-08-07). Build web tidak perlu `--dart-define` — `client.dart` sudah memakai `/api` relatif sejak PR #26 |
| "VPS belum disediakan" (di `HANDOVER.md`) | VPS **sudah ada dan hidup**: `103.93.134.22`, nginx 1.24.0, backend jalan, Gemini aktif, RAG 56 dokumen |

**Sisa yang perlu diketahui dev berikutnya:**

1. **Backend live masih deploy LAMA** — `/analyses` mengembalikan **4**, sedangkan `main`
   punya **11**. Artinya seluruh kerja slice ini (pesan publik, jembatan BigQuery, QRIS)
   **belum aktif di server**. Runbook redeploy: `REDEPLOY_VPS_RUNBOOK.md` (folder induk).
2. **`mobile/assets/payments/qr.jpeg` masih belum ada** — folder itu hanya berisi
   `README.md`. Layar bayar akan menampilkan placeholder `errorBuilder`.
3. **VPS belum punya TLS** (port 443 timeout). Selama itu belum beres, PWA tidak bisa
   memanggil backend dari halaman HTTPS — browser mem-block sebagai *mixed content*.
4. **Branch `feat/public-order-qris` masih ada di remote** dan tinggal berisi commit
   dokumen `5943661`. Setelah dokumen ini masuk `main`, branch itu aman dihapus.
