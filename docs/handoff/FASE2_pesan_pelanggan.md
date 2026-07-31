# Handoff — Fase 2: Pesan Pelanggan + Checkout Berbayar

> Dokumen untuk developer yang melanjutkan fitur **"pesan pelanggan"** Fortunas.
> Status per 2026-07-28: **backend Fase 2 selesai & teruji (46 test hijau, belum di-commit)**.
> Sisa pekerjaan utama: **UI Flutter pelanggan (Slice 2e)**.

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
  `list_orders`, `set_status`, `mark_paid` (potong stok, **idempoten**).
  Status: `pending_payment → paid → accepted/rejected → completed` (juga `expired/cancelled`).

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
| GET | `/public/orders/{id}` | poll status pesanan |
| GET/POST | `/public/orders/{id}/simulate-pay` | mode simulasi: tandai lunas (ditolak bila Midtrans live) |
| POST | `/public/payment/webhook` | notifikasi Midtrans → verifikasi → update status + potong stok |

### Test
- `tests/test_umkm_code_and_public.py` — 7 test Fase 2 (menu harga, order+simulasi-bayar+potong-stok, tolak tanpa harga, stok kurang 409, webhook valid/invalid).
- **Semua hijau:** `pytest tests/test_umkm_code_and_public.py tests/test_products.py tests/test_products_routes.py` → 46 passed.

### Konfigurasi
- `.env.example` sudah didokumentasikan: `MIDTRANS_SERVER_KEY`, `MIDTRANS_CLIENT_KEY`, `MIDTRANS_IS_PRODUCTION`.

---

## 4. ⏳ TODO — Slice 2e: UI Flutter pelanggan (pekerjaan berikutnya)

Bangun alur publik `/order` (tanpa auth). Urutan layar:

1. **Input kode UMKM** → panggil `GET /public/umkm/{code}`.
2. **Menu** (grid/list produk bergambar + harga) → tambah ke keranjang, atur qty.
3. **Keranjang / Checkout** → ringkasan item + total, form nama & no. HP (opsional).
4. **Bayar** → `POST /public/umkm/{code}/orders`:
   - Bila `payment_provider == "midtrans"` → buka `payment_redirect_url` (Snap) **atau** pakai `payment_token` via Snap SDK. Butuh paket **`webview_flutter`** (atau `midtrans_sdk`).
   - Bila `payment_provider == "simulated"` → cukup panggil `payment_redirect_url` (`/public/orders/{id}/simulate-pay`) untuk demo.
5. **Status** → poll `GET /public/orders/{id}` sampai `paid` → layar sukses.

**Yang perlu ditambah di kode mobile:**
- `mobile/lib/api/models.dart`: `PublicUmkm`, `PublicMenuProduct`, `PublicOrder` (mirror JSON backend).
- `mobile/lib/api/client.dart`: `getPublicUmkm(code)`, `createPublicOrder(code, {name, phone, items})`, `getPublicOrder(id)`.
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

- **Inbox pesanan UMKM:** layar di app UMKM untuk lihat/terima/tolak/selesaikan order (`GET` list order + `PATCH` status). Backend `list_orders`/`set_status` sudah siap; tinggal endpoint UMKM (auth tenant) + UI.
- **Notifikasi UMKM** saat ada order baru masuk (FCM `device_tokens` sudah ada; lihat `notify_repo.py`).
- **Order → transaksi BigQuery** saat pesanan `completed` (reuse `checkout_service.persist_basket`) supaya masuk riwayat & analitik UMKM.
- **Kaitkan order ke loyalty** (poin) bila pelanggan punya akun.
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
