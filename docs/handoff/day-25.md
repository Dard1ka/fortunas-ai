# Day 25 — Wave C: Paritas Penuh React (Satu PR)

**Tanggal:** 2026-08-08 · **Branch:** `feat/wave-c-react-parity` · **Backend:** TIDAK disentuh · **`mobile/`:** TIDAK disentuh · **Dependency baru:** NOL (`package.json` tidak berubah)

## Apa yang mendarat

Seluruh gap fitur Flutter → React ditutup dalam satu PR (permintaan Steven), berdasarkan
inventaris Wave C 7-agen (endpoint diverifikasi ke backend `main@844a8a4`). Setelah PR ini
terbukti live, prasyarat (a) Gate D — "Wave C ter-port penuh & terbukti" — terpenuhi;
sisanya ratifikasi ADR-0002 + penukaran required checks oleh admin (Dard1ka).

## Tabel paritas per area

| Area | Sumber Flutter | Padanan React baru | Test |
|---|---|---|---|
| A. Katalog produk | `products_screen.dart` (889) + 2 controller | `screens/products/` (ProductsScreen, ProductForm, CategoryManager) + route `/products` + tombol "Kelola Produk" di Profil | 9 (dipetakan dari 402 baris test Flutter) |
| B. Inbox pesanan | `orders_screen.dart` (217) + controller + home card | `OrdersScreen.jsx` + route `/orders` + kartu Home ber-badge (count `status=paid`, tanpa polling) | 7 + 2 (HomeScreen) |
| C. Order publik + QRIS | `public_order_screen.dart` (614) + controller (204) | `PublicOrderScreen.jsx` (1 route `/order`, 3 fase state) + gate App.jsx + tombol "Pesan tanpa akun" di Login + `public/payments/` (README; PNG dipasang manual — lihat catatan QRIS) | 9 (dari 9 test controller Flutter + gate) |
| D. Loyalty customer | `customer_points/promo/history_screen.dart` (514) + controllers (148) | `CustomerPointsScreen`, `CustomerPromoScreen` (roda SVG, rute `/customer/promo/:tenantId`), `CustomerHistoryScreen`, home penuh (promo/transaksi terakhir + Buat Promo), menu 2 tile, nav 3→5 tab | 11 (Flutter TIDAK punya test area ini) |
| E. Parser suara multi-item | `transaction_parser.dart` (353, NOL test) | `voice/transactionParser.js` (modul murni, `now` injectable) + VoiceFlow/VoiceParsed/VoiceSuccess multi-item | 37 parser + 4 flow |
| F. Fondasi client | `client.dart` L157-352 | 21 method baru di `api/client.js`, opsi `form:true` (multipart tanpa Content-Type manual), `/public/*` `auth:false`, proxy dev `/media` | 6 roles + 2 form |

Total test frontend: **48 → 139** (23 file). Lint 0. Build sukses (index 109,8 KB gzip, sebelumnya ~88 KB).

## Aturan bisnis penting yang dipertahankan

- Tri-state null: stok/harga/kategori kosong = `null`, bukan 0 (`parseIntOrNull`).
- Badge stok: null→Tak dilacak · 0→Habis · ≤5→Menipis · else Stok: N (ambang = `LOW_STOCK_THRESHOLD`).
- Order: aksi ketat per status (paid→Terima/Tolak; accepted→Selesai), NON-optimistis (reload server; 409 = normal), busy per-kartu, dialog tolak menyebut stok otomatis + uang manual, peringatan refund dari `payment_status`.
- `/order`: `orderable = price != null && (stock == null || stock > 0)`; increment dibatasi stok; total dihitung dari harga menu server; token TIDAK menempel di `/public/*` (dites di roles.test.js); QRIS hanya saat `pending_payment`; konfirmasi bayar = POST lalu GET (server = kebenaran).
- Loyalty: roda berhenti di segmen hasil SERVER; eligibility 422 tampil apa adanya; QR promo hanya dari respons generate; pola "data basi menang" di semua layar customer.
- Riwayat: render apa adanya (sort & cap server); empty state pakai `message` server (BigQuery best-effort — kosong ≠ gagal).

## Deviasi sadar (bukan salinan buta — semua tercatat di spec4 §3)

1. **Rupiah diseragamkan** ke konvensi React existing (`Rp 1.250.000`); Flutter tidak konsisten.
2. **Label status promo di-BI-kan** (`generated`→Aktif, `redeemed`→Terpakai, `expired`→Kedaluwarsa); Flutter membocorkan string mentah.
3. **Hapus produk pakai dialog konfirmasi**; Flutter menghapus tanpa konfirmasi (asimetri vs hapus kategori dinilai luput, bukan desain).
4. **Parser: bug C1/C2/C3 diperbaiki** di commit terpisah setelah baseline paritas (`seratus lima puluh`=150; `1.250.000` utuh; qty telanjang >100 tidak hilang). C4–C9 dipertahankan sebagai known-quirk + test.
5. **Voice menyimpan SATU request multi-item** via `/checkout/confirm`; Flutter loop satu request per item (jalur tulis React memang sudah multi-item sejak K5/ADR-0002).
6. **Rute promo pakai `/customer/promo/:tenantId`** (tahan reload PWA); Flutter mengoper objek via GoRouter `extra`.
7. **Roda: nilai di luar segmen berhenti di segmen TERDEKAT** (Flutter mendarat salah di 100rb); kartu menang selalu menampilkan angka server.
8. **Fallback QRIS no-leak** ("Kode QRIS belum tersedia…"); copy Flutter membocorkan path dev.

## ⚠️ Catatan QRIS (keputusan keamanan, temuan review pra-push)

Gambar QRIS **TIDAK di-commit**: QR yang tersedia adalah QRIS GoPay NYATA atas
nama pribadi (nama + merchant ID + NMID terdekode dari payload) dan repo ini
PUBLIK — meng-commit-nya = mempublikasikan identitas pembayaran permanen di
riwayat git. Mengikuti pola `mobile/assets/payments/` (folder di-track, file
manual): `frontend/public/payments/` hanya berisi README + guard .gitignore.
**Langkah deploy:** salin `qris-statis.png` ke
`/var/www/fortunas/payments/qris-statis.png` di VPS setelah tiap deploy dist/
(lihat README folder tsb). Tanpa file, UI jatuh ke fallback sopan, bukan error.

## Cara verifikasi live (setelah merge + deploy)

1. Unregister service worker + clear site data dulu (SW menyajikan build lama).
2. UMKM: Profil → Kelola Produk → tambah produk (gambar wajib) → cek badge stok/harga → Kasir: autocomplete menyarankan produk baru.
3. Publik (tanpa login): `/order` → kode publik toko → menu → keranjang → data pemesan → QRIS tampil → "Saya sudah bayar".
4. UMKM: Home badge "1 pesanan menunggu diterima" → `/orders` → Terima → Selesai (jembatan BQ best-effort).
5. Customer: login HP → home (Buat Promo) → roda berhenti sesuai hasil → poin berkurang 30 → tab Poin & Riwayat terisi (riwayat butuh kredensial BQ; kosong + pesan server = normal).
6. Voice (mic butuh HTTPS): ucapkan 2 produk sekaligus → layar konfirmasi 2 baris → simpan → History.

## Follow-up (di luar PR ini)

- **Redeem promo sisi kasir** (`POST /checkout/promo-scan/validate` + field `promo_code` di checkout) — belum pernah ada di klien mana pun; pelanggan bisa dapat promo tapi kasir belum punya UI menukarkannya.
- QRIS per-toko (sekarang satu gambar statis untuk semua tenant) — keputusan produk.
- Firebase OTP sungguhan (SDK belum ada; token dev masih dipakai) — `PENDING_EXTERNAL_SETUP.md`.
- Gate D: hapus `mobile/` + tukar required checks (admin) + ratifikasi ADR-0002.
