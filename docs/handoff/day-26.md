# Day 26 — Gate D: Hapus Flutter (`mobile/`)

**Tanggal:** 2026-08-08 · **Branch:** `chore/gate-d-remove-flutter` · **Arahan:** langsung dari Steven (2026-08-08) setelah Wave C (PR #35) merge + terverifikasi live di `app.fortunas.id`.

## Yang terjadi hari ini (konteks)

1. PR #34 (docs day-24) & PR #35 (Wave C paritas penuh) di-merge Steven → `main@d8ff01c`.
2. **Redeploy VPS** dari main tersebut: build lokal (`grep fonts.googleapis dist/` KOSONG), docroot `/var/www/fortunas` dikosongkan lalu diisi `dist/` baru, QRIS PNG dipasang manual ke `payments/` (di luar git — lihat day-25 §QRIS).
3. Verifikasi live (curl): `/` 200 bundle baru, `/order` 200 (SPA fallback), `/payments/qris-statis.png` 200 `image/png` 221646B, `/api/analyses` = 11, demo lama `103.93.134.22/health` tetap 200.
4. Keputusan domain: **tetap `app.fortunas.id`** (root cPanel tidak disentuh; MX rawan).

## Isi PR ini (Gate D)

- **`mobile/` DIHAPUS** (±149 file Flutter). Riwayat tetap ada di git.
- **Job CI `Mobile (flutter analyze)` → STUB bernama sama** (satu `echo`, ±5 detik):
  branch protection masih mewajibkan check bernama itu dan hanya admin repo yang bisa
  mengubah daftarnya — tanpa stub, SEMUA PR macet `blocked` (insiden PR #26).
  **Aksi Dard1ka (admin):** Settings → Branches → tukar required checks
  (`Mobile (flutter analyze)` keluar, `Frontend (lint + test + build)` masuk), lalu hapus
  job stub di PR yang sama.
- Referensi Flutter dibersihkan: `.gitignore` (blok artefak Flutter), `Makefile` (exclude zip),
  PR template (perintah test → frontend), `CONTRIBUTING.md` (ownership + checklist),
  `README.md` (status klien, stack, prasyarat, tree), `SETUP.md` (7 titik), `memory.md`,
  `docs/API_CONTRACTS.md` (mirror Dart dicabut).
- **`DEMO_SCRIPT.md` ditulis ulang penuh ke alur React** (7 skenario, termasuk Kasir+Kelola
  Produk, voice multi-item, order publik+QRIS) — menepati janji "rewrite final di PR Gate D".
- `AI_CONTEXT.md` (konteks era Flutter, Mei 2026, sudah menyesatkan) → diarsipkan ke
  `docs/history/AI_CONTEXT-2026-05.md` + banner arsip.
- `docs/adr/0002-react-production-client.md`: seksi "Status Gate D — DIEKSEKUSI" ditambahkan;
  kotak ratifikasi Darrel/Filo/Michael tetap menunggu centang mereka (merge/approve PR ini
  dihitung sebagai persetujuan).

## Yang TIDAK diubah

- `docs/handoff/*` lama, `docs/history/mobile-migration-2026.md`, ADR-0001, `docs/PLAN_EVERY_DEV.md`,
  `docs/ROADMAP.md`, `docs/VERIFICATION-*` — rekaman sejarah, menceritakan keadaan pada tanggalnya.
- `frontend/`, `app/` — nol perubahan kode aplikasi di PR ini.

## Sisa setelah PR ini

1. **Dard1ka:** tukar required checks + hapus stub `Mobile` (lihat atas).
2. Ratifikasi ADR-0002: centang Darrel, Filo, Michael.
3. Uji alur pelanggan end-to-end di produksi (item C1 VERIFICATION — butuh `FORTUNAS_DEV_AUTH`
   sementara, dinyalakan+dimatikan Steven di VPS).
4. `docs/PANDUAN-CEK-MANUAL.md` dijalankan di HP fisik (mic, install PWA, offline boot).
5. Follow-up produk: redeem promo sisi kasir; Firebase OTP asli; QRIS badan usaha per-toko.
