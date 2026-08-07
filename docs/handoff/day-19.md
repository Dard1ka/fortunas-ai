# Day 19 — R1b: Kasir/Checkout React + satu jalur tulis

**Tanggal:** 2026-08-08 · **Branch:** `feat/react-r1b-checkout` · Lanjutan day-18 (R1a).
Semua di `frontend/`; backend & `mobile/` tak disentuh.

## Yang berubah

1. **Layar Kasir `/checkout`** (acceptance MVP-4): multi-item (produk+qty+harga, tambah/hapus
   baris), grand total live (Rupiah id-ID), autocomplete produk via `GET /umkm/products/search`
   (debounce 250ms; tetap jalan tanpa katalog), nama pelanggan opsional, **token QR customer
   opsional → dikirim MENTAH di `customer_qr_token` `POST /checkout/confirm`**.
2. **Keputusan desain penting — JANGAN "diperbaiki":** TIDAK ada pre-validate token via
   `/umkm/customer/scan/validate`. Token QR single-use + TTL 90 detik; scan/validate
   MENGONSUMSI nonce, sehingga pre-validate membuat attach di checkout gagal DIAM-DIAM
   (backend tetap `ok:true`). Deteksi gagal-attach di UI: token terkirim tapi
   `customer_user_id` null → warning `role=alert` berisi `reply` backend. Ada test yang
   mengunci perilaku ini (`CheckoutScreen.test.jsx`).
3. **Voice → satu jalur tulis (K5/ADR-0002):** konfirmasi VoiceFlow kini menulis via
   `/checkout/confirm` (bukan `/voice/transaction`). Riwayat voice lokal tetap. Method client
   `voiceTransaction` dihapus (nol pemakai); endpoint backend-nya tetap ada (legacy).
4. Home dapat aksi cepat **Kasir** di bawah aksi voice.

## Angka

32 test (12 file) · lint 0 · js 92,51 KB gzip (budget ≤300 KB) · lockfile tak berubah.

## Konvensi/perhatian untuk dev berikutnya

- Kalau `package.json` berubah: regenerate lock via `npx npm@10 install --package-lock-only`
  dan bukti `npx npm@10 ci` — lock buatan npm 11 pernah menjatuhkan CI (day-18/PR #28).
- Verifikasi manual di preview: SW autoUpdate bisa menyajikan build LAMA di kunjungan pertama
  setelah deploy baru (update terpasang di kunjungan berikutnya) — bukan bug; hard-refresh
  atau unregister SW saat butuh bundle terbaru seketika.
- Voice masih single-item (sesuai K5); port parser multi-item = wajib pra-Gate D, bukan pra-submission.

## Berikutnya

**R1c — DPA screen** (`/dpa` dari Profile; GET/PUT `/umkm/dpa`, konfirmasi password, 403 →
pesan BI) · lalu **R1d — Wave B customer** (phone→OTP dev-token→bootstrap, QR 90s, scan token
manual, shell customer minimal — kunci token TERPISAH dari token UMKM).
