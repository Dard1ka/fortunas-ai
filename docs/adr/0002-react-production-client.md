# ADR 0002 — Klien produksi = React 19 + Vite; Flutter web dihentikan bertahap

- **Status:** 🟡 PROPOSED — menunggu ratifikasi 4 anggota (lihat §Ratifikasi)
- **Tanggal:** 2026-08-07
- **Pengusul:** Go Steven Sanjaya
- **Menggantikan:** [ADR-0001](0001-pwa-only-flutter-web.md) (PWA-only via Flutter web).
  Catatan tata kelola: ADR-0001 berstatus PROPOSED dan tidak pernah diratifikasi maupun
  di-push — ADR ini adalah keputusan arah klien pertama yang benar-benar melewati
  ratifikasi tim.

## Keputusan

1. **Klien produksi tunggal = React 19 + Vite** di `frontend/` — sesuai stack yang di-commit
   proposal hibah. Kanal rilis: `npm ci && npm run build` → `frontend/dist/`, disajikan
   same-origin di `app.fortunas.id` (topologi ADR-0001/D2 dipertahankan).
2. **`mobile/` (Flutter) DEPRECATED** sejak ADR ini beredar: tidak menerima fitur baru; tetap
   di tree sebagai cadangan demo sampai Gate D.
3. **Gate D — penghapusan `mobile/`** hanya dieksekusi setelah SEMUANYA terpenuhi:
   (a) ADR ini diratifikasi 4 anggota;
   (b) **paritas fungsional PENUH** React berstatus PROVEN di dokumen verifikasi:
       Wave A + Wave B + Wave C + voice multi-item (lihat §Disposisi layar) — arahan produk:
       *tidak ada fitur yang rusak/hilang pada momen mana pun* (K2 = C-port);
   (c) Steven menyetujui perubahan required status checks (admin), dieksekusi SATU perubahan
       terkoordinasi dengan penghapusan job CI mobile.
4. Produk = **web app + PWA**. Native (APK/iOS) tidak dirilis — melanjutkan keputusan yang
   sudah dieksekusi (shell android/ios sudah dihapus).

## Rasional

- Proposal hibah meng-commit **React 19 + Vite** — ini kembali ke rencana, bukan penyimpangan.
- Tabel biaya ADR-0001 sendiri menjadi bukti: payload Flutter web **3,28 MB gzip terukur** vs
  React ~0,09 MB terukur (build 2026-08-07: 88,36 KB gzip); **nol accessibility semantics**
  (CanvasKit merender semuanya ke satu canvas); **nol SEO**. ADR-0001 mengakui penolakan React
  saat itu "karena waktu, bukan kalah teknis".
- Yang berubah pada kalkulus waktu (audit repo 2026-08-07): kontrak API 6 layar React masih
  100% valid (drift hanya level fitur); gap P0 hibah cuma 2 layar (Checkout, DPA) + 6 layar
  kecil MVP-3; paritas skop-hibah ±5–8 hari-dev, bukan penulisan ulang buta 24 layar sekaligus.

## Disposisi 18 layar Flutter yang belum ada di React

| Wave | Layar | Status |
|---|---|---|
| A (P0 hibah) | Checkout/Kasir multi-item + attach QR customer; DPA view/edit | Dibangun segera (Spec 2 R1b/R1c) |
| B (P1, MVP-3) | Customer phone→OTP→profile; Customer QR; UMKM Scan validate; Customer menu/home minimal | Dibangun sebelum submission (Spec 2 R1d) |
| C (P2) | Katalog produk; Order inbox; Public order + QRIS; Customer points; Customer promo; Customer home penuh; Customer history | **C-port**: diport pasca-submission, SEBELUM Gate D — fitur tidak pernah offline |
| n/a | Splash (auth gate React resolve instan); Register terpisah (sudah ada sebagai toggle LoginScreen) | Tidak diperlukan |

Plus: **voice multi-item** — parser Dart lokal (353 baris, tanpa test) diport ke JS + diberi
test, wajib sebelum Gate D. Interim: voice single-item via `/voice/parse` → `/checkout/confirm`.

## Konsekuensi

- **HTTPS tetap blocker keras** — service worker, install prompt, dan mikrofon (Web Speech API)
  butuh secure context. Ini bukan artefak Flutter dan tidak hilang bersama Flutter.
- **CI:** job `Frontend (lint + test + build)` ditambahkan sekarang (check ekstra, non-required).
  Job `Mobile (flutter analyze)` TIDAK di-rename/dihapus sampai Gate D — branch protection
  mencocokkan nama job secara harfiah (insiden PR #26).
- Dokumen repo memakai framing transisi jujur (React = produksi; mobile = deprecated) —
  bukan klaim yang mendahului kenyataan.
- Handoff `docs/handoff/*.md` dan `docs/history/mobile-migration-2026.md` adalah rekaman
  sejarah — menceritakan keadaan pada tanggalnya, tidak diedit ulang.

## Yang secara sadar TIDAK diputuskan di sini

- Tanggal pasti Gate D (bergantung bukti paritas + ratifikasi).
- Perubahan setelan branch protection — milik Steven, ditunda olehnya.

## Ratifikasi

Centang = setuju (via approving review PR ini atau pernyataan tertulis yang di-link di sini).

- [ ] Gregorius Darrel Andika Setya (ketua)
- [ ] Filo Alvian Ongky
- [ ] Michael Ivan Santoso
- [x] Go Steven Sanjaya (pengusul, 2026-08-07)
