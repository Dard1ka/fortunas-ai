# Day 20 — R1c: Layar DPA "Pagar AI" React

**Tanggal:** 2026-08-08 · **Branch:** `feat/react-r1c-dpa` · Lanjutan day-19 (R1b).
Semua di `frontend/`; backend & `mobile/` tak disentuh.

## Yang berubah

1. **Layar `/dpa`** (acceptance MVP-5, paritas layar Flutter PR #12): view perjanjian +
   chips "AI boleh"/"AI tidak boleh" + meta versi; mode edit dengan chip editor
   (tambah/hapus) + textarea perjanjian + **konfirmasi password inline**
   (`PUT /umkm/dpa`; 403 "Konfirmasi password salah." → alert BI, **draft TIDAK hilang** —
   test-pinned); empty state mengajak isi pertama kali.
2. Entry dari Profile: tombol "Pagar AI (DPA)".
3. api client: `getDpa`, `putDpa`.

## Angka

37 test (13 file) · lint 0 · js 93,98 KB gzip.

## Status paritas skop-hibah (Wave A)

**Wave A SELESAI di sisi kode**: Checkout (R1b) + DPA (R1c). Kedua kriteria acceptance
MVP-4/MVP-5 sisi klien terpenuhi — verifikasi vs backend live menyusul di R2.

## Berikutnya

**R1d — Wave B customer (MVP-3):** phone → OTP (dev-token) → bootstrap
(`POST /customer/auth/bootstrap`) → shell customer minimal (home ringkas, QR 90 detik via lib
`qrcode`, menu) + layar Scan UMKM (`POST /umkm/customer/scan/validate`, input token manual).
PENTING: token customer disimpan TERPISAH dari token UMKM (kunci localStorage berbeda,
interceptor tidak boleh cross-attach) — lihat spec §3. Rute `/customer/*` sudah otomatis
phone-only (AppShell R1a).
