# Handoff — Fase 2: Pesan Pelanggan + Checkout Berbayar

> Dokumen untuk developer yang melanjutkan fitur **"pesan pelanggan"** Fortunas.
> Status per 2026-07-28: **backend Fase 2 selesai & teruji (46 test hijau, belum di-commit)**.
> Update 2026-08-03: **Slice 2 (jembatan BigQuery) & Slice 2e (UI Flutter pelanggan) SELESAI.**
> UI pelanggan: route publik `/order` (`screens/public_order_screen.dart` +
> `public_order/public_order_controller.dart`), entry "Pesan tanpa akun" di login,
> `AuthInterceptor` skip `/public/*`, 4 method client `/public/*`. Alur: kode → menu grid
> bergambar + cari client-side → keranjang → checkout (nama/HP) → bayar (simulasi) → pantau status.

---

## 1. Konteks fitur

Pelanggan memesan ke UMKM lewat **KODE UMKM** (mis. `KDS-001`) — **tanpa scan QR, tanpa buat akun**.

- **Fase 1 (selesai, commit `7721f41`):** backend `GET /public/umkm/{code}` → info toko + daftar menu (produk bergambar).
- **Fase 2 (dokumen ini):** pelanggan **checkout & bayar online**. Pesanan tersimpan, stok dipotong saat lunas.

**Keputusan produk (dari owner, 2026-07-28):**
1. UI pelanggan dibangun sebagai **screen baru di app Flutter** (bukan web terpisah).
2. **Pembayaran online**, provider = **Midtrans Snap** (standar Indonesia, sandbox gratis).
   Ada **fallback "simulasi"** supaya alur bisa diuji tanpa uang/kredensial nyata.

---

## 2. Arsitektur & konvensi yang WAJIB diikuti

- **Backend:** FastAPI. Akun/tenant/produk/order di **SQLite/Postgres** (SQLAlchemy, `app/db_pg.py`).
  Transaksi bisnis final tetap di **BigQuery** (`checkout_service.py`) — **order publik TIDAK** di BigQuery,
  ia state operasional pra-transaksi → simpan di tabel relasional `public_orders`.
- **Pola repo:** modul-level function, `SessionLocal`, return `dict` (lihat `app/product_repo.py`, `app/order_repo.py`).
- **Uang (Rupiah):** integer bulat (tanpa desimal). Kolom `price`, `total`, `unit_price` semua `int`.
- **Migrasi:** Alembic di `app/migrations/versions/NNN_*.py`, berantai lewat `down_revision`.
  ⚠️ **Dev pakai `Base.metadata.create_all` (`db.init_db()`)**, jadi tabel BARU sudah dibuat create_all →
  `alembic upgrade` bentrok ("table already exists"). **Solusi dev:** `alembic stamp <rev>`.
  Migrasi tetap benar untuk DB fresh/produksi (sudah diverifikasi `001→009` jalan mulus di DB kosong).
- **Mobile:** Flutter + Riverpod + go_router. Model di `mobile/lib/api/models.dart`,
  HTTP di `mobile/lib/api/client.dart`, controller per-fitur, tema di `mobile/lib/theme/tokens.dart`.
- **GateGuard:** ada hook yang minta "fact-forcing" tiap edit file baru. Untuk kerja lancar:
  jalankan sesi dengan env `ECC_GATEGUARD=off`.

---

## 3. Yang SUDAH selesai (Slice 2a–2d)

### 2a — Harga produk
- `app/models.py`: `Product.price` (Integer, nullable — `NULL` = harga belum diset).
- Migrasi `app/migrations/versions/008_product_price.py`.
- `app/product_repo.py`: `price` di `_product_to_dict`, param `price` di `create_product`, fungsi `set_price`, `get_product(tenant_id, id)`, `decrement_by_ids(...)`.
- `app/schemas.py`: `Product.price`, `PriceUpdateRequest`.
- `app/api/routes/products.py`: `price` di `POST /umkm/products`, endpoint `PATCH /umkm/products/{id}/price`.
- `app/api/routes/public.py`: `price` ikut di menu publik.
- **Mobile (sisi UMKM):** `ProductItem.price`, `client.createProduct(price:)` + `client.setPrice()`,
  `product_controller.create(price:)` + `setPrice()`, form **Kelola Produk** ada field Harga + badge harga + tombol edit harga.

### 2b — Storage order
- `app/models.py`: `PublicOrder` (tabel `public_orders`) — `items` (JSON: `[{product_id,name,qty,unit_price,subtotal}]`),
  `total`, `status`, `payment_provider/order_id/token/redirect_url/status`, timestamps.
- Migrasi `009_public_orders.py`.
- `app/order_repo.py`: `create_order`, `attach_payment`, `get_order`, `get_by_payment_order_id`,
  `list_orders`, `get_order_for_tenant`, `apply_action`, `mark_paid` (potong stok, **idempoten**),
  `restore_stock`, `cancel_by_gateway`.
  Status: `pending_payment → paid → accepted/rejected → completed` (juga `expired/cancelled`).
  **Perubahan status pesanan WAJIB lewat `apply_action`** (compare-and-set: `UPDATE ... WHERE status IN (...)`
  lalu periksa `rowcount`), **bukan** `set_status`. `set_status` masih ada di modul tapi menulis status **tanpa
  syarat** — tepat cacat yang CAS ini ganti (lihat day-15 §Utang #4) — dan sudah tak punya pemanggil produksi.

### 2c — Payment service
- `app/services/payment.py`:
  - `create_charge(order)` → Snap token + redirect_url (atau redirect simulasi bila key kosong).
  - `verify_notification(payload)` → validasi signature Midtrans `sha512(order_id+status_code+gross_amount+server_key)`.
  - `client_config()`, `is_live()`.
  - **Mode simulasi** aktif otomatis saat `MIDTRANS_SERVER_KEY` kosong.

### 2d — Endpoint publik (`app/api/routes/public.py`)
| Method | Path | Fungsi |
|---|---|---|
| POST | `/public/umkm/{code}/orders` | validasi (produk milik UMKM, ada harga, stok cukup) → buat order → inisiasi bayar |
| GET | `/public/orders/{payment_order_id}` | poll status pesanan |
| GET/POST | `/public/orders/{payment_order_id}/simulate-pay` | mode simulasi: tandai lunas (ditolak bila Midtrans live) |
| POST | `/public/payment/webhook` | notifikasi Midtrans → verifikasi → update status + potong stok |

> ⚠️ **Kunci publik = `payment_order_id`** (string), **bukan** `id` sekuensial platform-wide. `payment_order_id`
> ikut dikembalikan di respons `POST /public/umkm/{code}/orders` — itu satu-satunya cara pelanggan tahu
> URL status pesanannya. (Kunci `id` int sempat dipakai, mati sejak Task 5 slice `umkm-order-inbox`.)

### Test
- `tests/test_umkm_code_and_public.py` — 7 test Fase 2 (menu harga, order+simulasi-bayar+potong-stok, tolak tanpa harga, stok kurang 409, webhook valid/invalid).
- **Semua hijau:** `pytest tests/test_umkm_code_and_public.py tests/test_products.py tests/test_products_routes.py` → 46 passed.

### Konfigurasi
- `.env.example` sudah didokumentasikan: `MIDTRANS_SERVER_KEY`, `MIDTRANS_CLIENT_KEY`, `MIDTRANS_IS_PRODUCTION`.

---

## 4. ✅ SELESAI — Slice 2e: UI Flutter pelanggan (2026-08-03)

Terbangun sesuai rencana di bawah. File: `mobile/lib/screens/public_order_screen.dart`
(satu layar, 3 fase), `mobile/lib/public_order/public_order_controller.dart` (Riverpod),
4 method `/public/*` di `mobile/lib/api/client.dart`, `AuthInterceptor` skip `/public/*`,
route `/order` di `app.dart` + whitelist `authRedirect`, entry "Pesan tanpa akun" di
`login_screen.dart`. **Pembayaran hanya mode simulasi** — Midtrans Snap (webview) masih TODO;
pesanan `midtrans` menampilkan pesan "lanjutkan lewat tautan toko". Tes: `test/public_order/`,
`test/api/auth_interceptor_test.dart`, `test/auth/auth_redirect_test.dart`.

Rencana asli (arsip):

Bangun alur publik `/order` (tanpa auth). Urutan layar:

1. **Input kode UMKM** → panggil `GET /public/umkm/{code}`.
2. **Menu** (grid/list produk bergambar + harga) → tambah ke keranjang, atur qty.
3. **Keranjang / Checkout** → ringkasan item + total, form nama & no. HP (opsional).
4. **Bayar** → `POST /public/umkm/{code}/orders`:
   - Bila `payment_provider == "midtrans"` → buka `payment_redirect_url` (Snap) **atau** pakai `payment_token` via Snap SDK. Butuh paket **`webview_flutter`** (atau `midtrans_sdk`).
   - Bila `payment_provider == "simulated"` → cukup panggil `payment_redirect_url` (`/public/orders/{payment_order_id}/simulate-pay`) untuk demo.
5. **Status** → poll `GET /public/orders/{payment_order_id}` sampai `paid` → layar sukses.

**Yang perlu ditambah di kode mobile:**
- `mobile/lib/api/models.dart`: `PublicUmkm`, `PublicMenuProduct`, `PublicOrder` (mirror JSON backend).
- `mobile/lib/api/client.dart`: `getPublicUmkm(code)`, `createPublicOrder(code, {name, phone, items})`, `getPublicOrder(paymentOrderId)`.
  ⚠️ Endpoint publik **tanpa** header Authorization — pastikan interceptor auth tidak memaksa token untuk `/public/*`.
- Controller keranjang (Riverpod) + screens: `order_code_screen`, `order_menu_screen`, `order_cart_screen`, `order_pay_screen`, `order_status_screen`.
- Routing di `mobile/lib/app.dart`: rute `/order` (public, di luar shell auth). Entry point: tombol di login screen ("Pesan tanpa akun").
- Reuse `theme/tokens.dart` + `ui/screen_header.dart` biar konsisten.

**Verifikasi 2e:** jalankan backend (`scripts/start.ps1` / `start.bat`) + `flutter run`, uji end-to-end di mode simulasi (tanpa key Midtrans).

---

## 5. Setup Midtrans (untuk pembayaran nyata)

1. Daftar **Midtrans Sandbox** (gratis): <https://dashboard.sandbox.midtrans.com>.
2. Settings → Access Keys → salin **Server Key** & **Client Key**.
3. Isi di `.env`:
   ```
   MIDTRANS_SERVER_KEY=SB-Mid-server-xxxx
   MIDTRANS_CLIENT_KEY=SB-Mid-client-xxxx
   MIDTRANS_IS_PRODUCTION=false
   ```
4. Settings → Configuration → **Payment Notification URL** = `<BASE_URL>/public/payment/webhook`
   (untuk lokal pakai tunnel, mis. ngrok/cloudflared).
5. Uji dengan kartu/e-wallet sandbox Midtrans. Kosongkan key → balik ke mode simulasi.

---

## 6. Fase 3 & seterusnya (backlog usulan)

- ~~**Inbox pesanan UMKM**~~ — **SUDAH DIBANGUN di Slice 1 (day-15)**, backend + Flutter. Endpoint-nya sudah ada
  (auth tenant): `GET /umkm/orders` (tanpa filter → `paid` + `accepted`; `?status=all`; `?status=<x>`) plus tiga
  endpoint per-aksi `POST /umkm/orders/{id}/accept|reject|complete`. Sengaja **bukan** `PATCH {status}` generik —
  itu akan membuat klien bisa mengirim `expired`/`cancelled` yang hak sistem. Kalau menambah transisi baru:
  lewat `order_repo.apply_action` (compare-and-set) + tabel `_ALLOWED_FROM`, **jangan** `set_status` yang
  menulis tanpa syarat. Lihat `docs/handoff/day-15.md`.
- **Notifikasi UMKM** saat ada order baru masuk (FCM `device_tokens` sudah ada; lihat `notify_repo.py`).
- ~~**Order → transaksi BigQuery** saat pesanan `completed` (reuse `checkout_service.persist_basket`)~~ —
  **SELESAI (Slice 2, 2026-08-03):** `checkout_service.persist_completed_order`, dipanggil dari
  `routes/orders.complete_order`. Sekarang masuk riwayat & analitik UMKM.
- **Kaitkan order ke loyalty** (poin) bila pelanggan punya akun. **Sebagian:** riwayat produk (`record_purchase`)
  + membership sudah ditaut saat `completed` bila pelanggan login (Slice 2); **earning poin belum** — masih TODO.
- **Expiry order** `pending_payment` yang tak dibayar (job/cron) → status `expired`, kembalikan reservasi.
- **Menu self-order per-kategori** (disebut di handoff day-14 sebagai Fase 3).

---

## 7. Perintah cepat

```bash
# Backend
cd fortunas-ai
.venv/Scripts/python.exe -m pytest tests/test_umkm_code_and_public.py -q      # test Fase 2
.venv/Scripts/python.exe -m alembic upgrade head                              # migrasi (DB fresh)
.venv/Scripts/python.exe -m alembic stamp 009                                 # dev (tabel sudah ada via create_all)

# Mobile
cd fortunas-ai/mobile
flutter analyze lib
flutter run
```

**File inti Fase 2:** `app/order_repo.py`, `app/services/payment.py`, `app/api/routes/public.py`,
`app/models.py` (`Product.price`, `PublicOrder`), `app/migrations/versions/00[89]_*.py`,
`tests/test_umkm_code_and_public.py`.
