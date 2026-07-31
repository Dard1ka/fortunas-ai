# Handoff — Fase 3: Penyempurnaan UI + Login OTP Nyata

> Lanjutan dari [FASE2_pesan_pelanggan.md](FASE2_pesan_pelanggan.md).
> Fase 3 = merapikan UI di sisi UMKM & pelanggan + membuat **login OTP benar-benar berfungsi**.
> Semua backend inti sudah ada sejak Fase 1–2; Fase 3 sebagian besar pekerjaan **Flutter**,
> kecuali OTP nyata yang butuh setup Firebase (client + backend).
>
> ⚠️ Baca dulu bagian **Konvensi** di FASE2 (repo pola, uang integer, GateGuard `ECC_GATEGUARD=off`,
> caveat migrasi `create_all` vs Alembic).

Ada 4 item. Kerjakan berurutan; item 1 & 3 kecil, item 2 & 4 besar.

---

## Item 1 — Field alamat + tampilkan KODE di akun UMKM

**Kenapa:** Kode UMKM (mis. `KDS-001`) adalah "alamat toko" yang dibagikan ke pelanggan untuk memesan (Fase 2).
UMKM harus bisa **melihat kode**-nya dan **mengubah alamat** (alamat → regenerasi kode via AI).

**Keadaan sekarang:**
- Backend SUDAH lengkap:
  - `GET /umkm/me` → `business_profile` berisi `code`, `address`, `city` (lihat `app/api/routes/auth.py`).
  - `PUT /umkm/address` (body `{address}`) → regenerasi `code`+`city` via `umkm_code.generate_umkm_code` → balas profil baru.
- Mobile:
  - `UmkmAccount.businessProfile` (Map) **sudah memuat** `code`/`address`/`city` (`mobile/lib/api/models.dart`).
  - `mobile/lib/screens/profile_screen.dart` **belum menampilkan** kode/alamat.
  - `mobile/lib/api/client.dart` **belum punya** method untuk `PUT /umkm/address`.

**Yang dikerjakan:**
1. `client.dart`: tambah `Future<UmkmAccount> setUmkmAddress(String address)` → `PUT /umkm/address`, parse balikan.
   (Backend membalas `{tenant_id, business_profile,...}` — sesuaikan parsing; boleh refetch `me()` bila lebih mudah.)
2. `profile_screen.dart`:
   - Kartu **"Kode Toko"** yang menonjol menampilkan `businessProfile['code']` (mis. badge besar `KDS-001`) + tombol **Salin** (`Clipboard.setData`) + kalimat "Bagikan kode ini ke pelanggan untuk memesan".
   - Baris **Alamat** menampilkan `businessProfile['address']` + tombol **Ubah** → dialog/sheet input alamat → panggil `setUmkmAddress` → refresh. Tampilkan kode baru bila berubah.
3. State: pakai controller profil yang sudah ada (atau `me()` provider); pastikan UI refresh setelah update.

**Acceptance:** UMKM buka Profil → lihat kode + alamat; ubah alamat → kode ter-update tampil; kode bisa disalin.

---

## Item 2 — Sisi pelanggan: grid menu bergambar + autokomplet + voice

**Konteks:** Ini memperkaya **Slice 2e** (UI pesan pelanggan) yang masih TODO di FASE2. Kalau 2e belum dibuat,
kerjakan 2e dulu (alur `/order`: kode → menu → keranjang → checkout → bayar → status), lalu tambahkan 3 hal ini.

### 2a. Grid menu bergambar
- Ganti list menu jadi **grid** (`GridView`, 2 kolom) kartu produk: gambar + nama + harga (`_rupiah`) + tombol tambah.
- Sumber data: `GET /public/umkm/{code}` (sudah mengembalikan `image_url`, `price`, `stock`, `category_id`).
- Gambar: URL relatif `image_url` di-prefix base API (lihat pola `_apiBase` + `Image.network` di `products_screen.dart`).
- Tampilkan badge "Habis" bila `stock == 0`; disable tambah bila habis atau `price == null`.
- Opsional: filter chip per **kategori** (butuh menu mengembalikan nama kategori — saat ini hanya `category_id`;
  bisa tambah endpoint publik kategori atau sertakan `category_name` di response menu).

### 2b. Autokomplet (cari produk)
- Backend: endpoint search yang ada (`GET /umkm/products/search`) **butuh auth UMKM** → tidak cocok untuk publik.
  Dua opsi:
  - **(disarankan, cepat)** Filter **client-side**: menu publik biasanya kecil; ambil semua produk sekali, saring di Flutter (`SearchAnchor`/`Autocomplete` widget) berdasarkan nama.
  - **(kalau katalog besar)** Tambah endpoint publik `GET /public/umkm/{code}/products/search?q=` di `app/api/routes/public.py` (mirror logika `products.search_products`, tanpa auth, scoped by code).
- UI: kotak cari di atas grid → hasil menyaring grid secara real-time (autocomplete bergambar).

### 2c. Voice order (pelanggan)
- Sudah ada **voice untuk kasir UMKM**: `mobile/lib/voice/voice_flow.dart` + backend `POST /voice/parse`
  (`app/api/routes/voice.py`) yang mengubah transkrip → item terstruktur.
- Untuk pelanggan: gunakan ulang komponen voice, tapi **map hasil ke keranjang order publik** (bukan checkout kasir).
  - Rekam suara → transkrip (paket STT yang sudah dipakai kasir) → `POST /voice/parse` → daftar `{product, qty}`.
  - Cocokkan `product` (nama) ke produk menu publik (case-insensitive) → tambah ke keranjang; item tak dikenal → tampilkan "tidak ditemukan".
  - ⚠️ `/voice/parse` saat ini kemungkinan butuh auth UMKM — cek; bila ya, buat varian publik atau lakukan parsing ke katalog `code` tertentu.
- Pertimbangkan izin mikrofon (`permission_handler` sudah ada di pubspec).

**Acceptance:** Pelanggan buka menu → grid bergambar, bisa cari cepat, bisa "ngomong" pesanan dan item masuk keranjang.

---

## Item 3 — Gambar produk di checkout & riwayat

**Keadaan sekarang:** `checkout_screen.dart` dan `history_screen.dart` **tidak menampilkan gambar produk**
(hanya nama/qty/harga). Produk sudah punya `image_url`.

**Yang dikerjakan:**
- **Checkout** (`mobile/lib/screens/checkout_screen.dart`): tiap baris item tampilkan thumbnail (`Image.network` prefix `_apiBase`),
  fallback ikon bila `image_url` kosong / gagal (`errorBuilder`). Samakan pola dengan tile di `products_screen.dart`.
  - Catatan: item checkout kasir mengacu produk by name; ambil `image_url` dengan mencocokkan ke katalog (`product_controller`/`listProducts`) atau sertakan `image_url` di line item saat dipilih.
- **Riwayat** (`mobile/lib/screens/history_screen.dart`): tampilkan thumbnail per item transaksi bila tersedia.
  - Riwayat server (BigQuery) mungkin **tidak menyimpan** `image_url` — solusi: lookup dari katalog by `stock_code`/nama saat render, atau simpan `image_url` di detail item lokal (`history/tx_store.dart`).
- Reuse helper: buat 1 widget `ProductThumb(imageUrl)` kecil yang dipakai di products/checkout/history/menu publik biar konsisten.

**Acceptance:** Baris item di checkout & riwayat menampilkan gambar produk (dengan fallback rapi).

---

## Item 4 — Login OTP nyata (agar berhasil)

**Keadaan sekarang (PENTING):** OTP masih **mode dev / "theatre"**:
- Mobile: `customer_otp_screen.dart` menerima **sembarang 6 angka** (`validateOtp`), lalu
  `customer_auth_controller.bootstrap()` mengirim token palsu `devFirebaseToken(phone)` = `"dev:<digits>:<digits>"`
  (`mobile/lib/customer/customer_auth_rules.dart`). **Tidak ada SMS asli, tidak ada `firebase_auth` di client.**
- Backend: `app/core/firebase_auth.verify_firebase_token`:
  - kalau ada kredensial (`FIREBASE_CREDENTIALS` / `credentials/firebase-admin.json`) → verifikasi `id_token` asli;
  - else kalau `FORTUNAS_DEV_AUTH=1` → terima token `dev:<uid>:<phone>`;
  - else → `503 FirebaseNotConfigured`.
- `.env` saat ini `FORTUNAS_DEV_AUTH=1` dan **belum ada `firebase-admin.json`** → jadi login dev **harusnya jalan**.

**Kalau "OTP tidak berhasil" di dev**, cek berurutan:
1. `FORTUNAS_DEV_AUTH=1` ter-load di proses backend (bukan cuma di file `.env` yang tak dibaca)?
2. Backend balas apa di `POST /customer/auth/bootstrap`? (503 = Firebase belum dikonfigurasi & dev-auth mati; 401 = token salah format).
3. `devFirebaseToken` mengirim `dev:<uid>:<phone>` dengan uid tak kosong (nomor min 8 digit — `validatePhone`).
4. Base URL API mobile benar (emulator vs device).

**Membuat OTP NYATA (produksi) — pekerjaan Fase 3:**

*Prasyarat Firebase:*
1. Buat/aktifkan **Firebase project**; **Authentication → Sign-in method → Phone** = enabled.
2. Daftarkan app Android/iOS di Firebase; unduh `google-services.json` / `GoogleService-Info.plist`.
3. Untuk nomor uji tanpa biaya: tambah **test phone numbers** di Firebase Console.

*Client (Flutter):*
4. Tambah paket `firebase_core` + `firebase_auth` (pubspec) + init `Firebase.initializeApp()` di `main`.
5. `customer_phone_screen`: panggil `FirebaseAuth.instance.verifyPhoneNumber(...)` → kirim SMS,
   simpan `verificationId` → pindah ke OTP screen.
6. `customer_otp_screen`: `PhoneAuthProvider.credential(verificationId, smsCode)` →
   `signInWithCredential` → ambil **real ID token** (`user.getIdToken()`).
7. `customer_auth_controller.bootstrap()`: kirim **ID token asli** (bukan `devFirebaseToken`) ke `POST /customer/auth/bootstrap`.
   - Pertahankan `devFirebaseToken` di balik flag build (dev) sebagai fallback CI/emulator.

*Backend:*
8. Sediakan kredensial admin: `credentials/firebase-admin.json` (service account **Firebase Admin**, bukan
   `fortunas-service-account.json` yang sekarang) atau set `FIREBASE_CREDENTIALS`.
   `_verify_real` sudah siap (`firebase_admin.auth.verify_id_token`).
9. **Matikan** `FORTUNAS_DEV_AUTH` di produksi (biar token dev ditolak).
10. Pastikan `firebase-admin` ada di `requirements.txt` untuk lingkungan produksi (lazy import, tak masuk CI).

**Acceptance:** Di device nyata, nomor HP → terima SMS OTP asli → masuk; token diverifikasi backend; dev token ditolak saat `FORTUNAS_DEV_AUTH` mati.

---

## Ringkasan file & endpoint terkait

| Item | Backend | Mobile |
|---|---|---|
| 1 Alamat+kode | `PUT /umkm/address`, `GET /umkm/me` (ada) | `client.dart` (+method), `profile_screen.dart`, `models.dart` |
| 2 Menu/cari/voice | `GET /public/umkm/{code}` (ada); opsional search publik + voice publik | screens `/order`, `voice_flow.dart` (adaptasi) |
| 3 Gambar | `image_url` sudah tersedia | `checkout_screen.dart`, `history_screen.dart`, `tx_store.dart`, widget `ProductThumb` |
| 4 OTP nyata | `app/core/firebase_auth.py` (ada), kredensial admin | `firebase_core`+`firebase_auth`, `customer_phone/otp_screen`, `customer_auth_controller` |

## Perintah cepat
```bash
cd fortunas-ai/mobile && flutter analyze lib && flutter run
cd fortunas-ai && .venv/Scripts/python.exe -m pytest -q
```

> Prinsip: jangan pecahkan yang sudah jalan. Backend Fase 1–2 stabil & teruji — Fase 3 menambah UI di atasnya.
> Setiap item punya **Acceptance**; anggap selesai saat acceptance terpenuhi + `flutter analyze` bersih.
