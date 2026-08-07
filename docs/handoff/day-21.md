# Day 21 — R1d: Wave B Customer + Scan — paritas skop-hibah TERCAPAI (sisi kode)

**Tanggal:** 2026-08-08 · **Branch:** `feat/react-r1d-customer` · Lanjutan day-20 (R1c).
Semua di `frontend/`; backend & `mobile/` tak disentuh.

## Yang berubah

1. **Sesi customer TERPISAH total dari UMKM** — kunci `fortunas_customer_token`; `request()`
   punya opsi `role`; 401 customer TIDAK menghapus sesi UMKM (dan sebaliknya) — dikunci
   `src/api/roles.test.js`. Ini regresi paling berbahaya di dual-auth; jangan disatukan.
2. **Alur auth customer** (paritas Flutter PR #15): `/customer/login` (HP) → `/customer/otp`
   (**dev-token**: 6 digit apa pun; teks jujur "mode pengembangan" — Firebase Phone Auth =
   item eksternal PENDING) → `/customer/profile` → `POST /customer/auth/bootstrap` dengan
   `firebase_id_token: "dev:<digits>:<phone>"`; 503 (belum dikonfigurasi) vs 401 dibedakan.
3. **Shell customer** (3 tab sendiri di dalam frame 430px): home minimal (poin + membership),
   **QR identitas** (paritas PR #16: lib `qrcode` sebagai chunk lazy, TTL 90 detik countdown +
   auto-refresh jelang kedaluwarsa, **token string + tombol Salin** — jembatan kasir tanpa
   kamera), menu+logout. Area customer bisa diakses TANPA login UMKM (gate App per-path).
4. **`/scan` UMKM** (paritas PR #17): validasi token manual → varian "member baru 🎉" /
   "member sejak …"; reason `expired/replayed/tampered` → pesan BI yang actionable.
   Entry: aksi cepat ketiga di Home.
5. Login UMKM punya link "Masuk sebagai pelanggan →".

## Angka

48 test (16 file) · lint 0 · js 97,04 KB gzip + lazy qrcode 8,85 KB · lockfile npm 10 terbukti.

## ⭐ Status besar: paritas skop-hibah SELESAI di sisi kode

R1a (hardening+PWA+shell) + Wave A (Kasir R1b, DPA R1c) + Wave B (customer R1d) — semua
kriteria acceptance MVP sisi klien (MVP-3/4/5 + auth MVP-1) kini ada di React. Yang TERSISA
menuju submission: **R2 verifikasi vs backend live** (butuh akun uji + izin tulis dari Steven)
→ **R3 deploy TLS `app.fortunas.id`** (DNS+certbot+redeploy backend — aksi Steven, runbook siap)
→ **R4 panduan cek manual**. Wave C (katalog/promo/poin/order/QRIS publik) = pasca-submission,
pra-Gate D (C-port, ADR-0002).

## Catatan QRIS (dari Steven, 2026-08-08)

Pembayaran tetap **QRIS statis** (Midtrans dorman — butuh badan usaha terdaftar; kode sudah
ada, aktif via `MIDTRANS_SERVER_KEY` kelak). Steven sudah menyediakan gambar QRIS asli
(GPN, a.n. GO, STEVEN SANJAYA) — disimpan di `Fortunas/assets-eksternal/qris-statis.jpeg`
(folder induk); dipasang saat alur `/order` diport (Wave C). JANGAN commit ke repo tanpa
keputusan tim (repo publik; NMID memang info publik di poster QRIS, tapi keputusannya milik tim).

## Berikutnya

**R2 — verifikasi**: dokumen PROVEN/BLOCKED + Playwright vs backend live (`cross-env
VITE_API_TARGET=http://103.93.134.22 npm run dev`); PRASYARAT dari Steven: 1 akun UMKM uji +
konfirmasi boleh MENULIS ke tenant uji (checkout + DPA), dicatat di dokumen verifikasi.
