# Day 18 — R1a: Hardening klien produksi React

**Tanggal:** 2026-08-08 · **Branch:** `feat/react-r1a-hardening` · **Konteks:** ADR-0002
(React = klien produksi), Spec 2 R1a. Semua perubahan di `frontend/` saja — backend & `mobile/`
tidak disentuh.

## Yang berubah

1. **Vitest + React Testing Library** masuk — `npm test` kini aktif (job CI `Frontend
   (lint + test + build)` otomatis menjalankannya via `--if-present`). 26 test hijau.
2. **Font self-host** via `@fontsource` subset **latin** (Inter/Space Grotesk/JetBrains Mono)
   — `@import` Google Fonts + preconnect DIHAPUS. Nol request pihak ketiga (PDP + offline);
   dijaga test statis `src/test/no-third-party.test.js`.
3. **Service worker (Workbox, autoUpdate)** via `vite-plugin-pwa` — React kini PWA sejati
   (installable + offline-capable), precache 20 entri ±797 KiB. Manifest tetap file manual
   `public/manifest.webmanifest` (plugin `manifest: false`) — satu sumber kebenaran ter-test.
4. **Branding:** theme_color meta = manifest = `#6D5EF7` (paritas test-pinned); deskripsi
   era-Gemini (copy Qwen3 hilang); `<noscript>` BI.
5. **Shell adaptif 3-tier:** `src/ui/shell.js` (SATU sumber konstanta: 600/1024, konten
   720/840, phone-frame 430, form 420) + `useShellTier` + `NavRail` (76px ikon / 200px label)
   + `AppShell`. HP TIDAK berubah (bottom-nav tetap); ≥600 dapat rail. **Rute
   `/customer/*` + `/order` = kolom HP 430px di layar lebar** — daftar ter-pin test
   (`PHONE_ONLY_ROUTE_PREFIXES`); `/orders` (inbox UMKM, nanti) TIDAK termasuk.
6. **UI kit:** `Button` (disabled DISTINGUISHABLE — bukan violet redup), `Input` (boxed,
   fokus dua-sinyal, label ter-asosiasi = a11y), `Card`, `FormPane` (420px, untuk form Wave B).
7. **Layar:** Login pakai kit + **field alamat opsional** (register → kode publik UMKM);
   Home chips dari `GET /analyses` (11 intent, fallback offline); Briefing render **semua 11
   seksi** (peta ikon/warna lengkap); History + seksi **transaksi BigQuery**
   (`GET /umkm/transactions`, bentuk persis `UmkmTransactionsResponse`); Profile versi dari
   `package.json` (4.1.0 — konfirmasi Steven) + tampil kode publik + backfill alamat
   (`PUT /umkm/address`).

## Yang SENGAJA tidak berubah

- Layar tidak di-redesign (keputusan D1: phone-first, desktop cukup rapi) — hanya hardening.
- `mobile/` tak tersentuh; jalur demo Flutter tetap sah sampai Gate D.
- Toast/Dialog belum dibuat (YAGNI — masuk R1b saat Checkout membutuhkannya).
- LoginScreen memakai layout centering-nya sendiri (sudah benar di semua tier); `FormPane`
  dipakai untuk form BARU (Wave B), bukan dipaksakan ke login.

## Angka

- Payload initial: **JS 90,65 KB + CSS 1,66 KB gzip ≈ 92,3 KB** (budget ≤300 KB; Flutter web
  dulu 3,28 MB). Metode: output `vite build` (gzip size per aset entry).
- Test: 26 (10 file); lint 0 error; build hijau.

## Konvensi untuk dev berikutnya

- Breakpoint/lebar JANGAN di-hardcode — impor dari `src/ui/shell.js`.
- Layar/rute baru persona customer/publik → tambahkan prefiksnya ke
  `PHONE_ONLY_ROUTE_PREFIXES` (test akan memaksa sadar).
- Komponen form WAJIB `Input`/`Button` dari kit (a11y + disabled-state gratis).
- Jangan tambah font/asset dari host eksternal — test `no-third-party` merah.
- Bentuk respons backend untuk mock test: BACA `app/schemas.py` dulu, jangan menebak.

## Blocker tersisa (di luar PR ini)

- ⛔ Rotasi 6 kredensial (aksi Steven, PENDING_EXTERNAL_SETUP.md).
- TLS `app.fortunas.id` (DNS + certbot, aksi Steven) — prasyarat mic/install/offline di HP.
- Ratifikasi ADR-0002 masih 1/4 tanda tangan.
- Verifikasi offline-boot browser riil + matriks screenshot penuh = R2.

## Berikutnya

**R1b — Checkout/Kasir** (multi-item + attach `customer_qr_token` LANGSUNG di
`/checkout/confirm`, TANPA pre-validate — token single-use 90 detik; UI wajib menampilkan
hasil attach) · lalu **R1c — DPA** · **R1d — Wave B customer**. Spec:
`Fortunas/brainstorming/specs/2026-08-07-spec2-react-paritas-verifikasi-deploy-design.md`.
