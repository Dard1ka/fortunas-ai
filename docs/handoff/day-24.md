# Day 24 — LIVE: `https://app.fortunas.id` menyala + uji tulis sebagai tester

**Tanggal:** 2026-08-08 · **Branch:** `docs/faseA-live-verification` · Lanjutan day-22/23.
Eksekusi deploy oleh asisten via SSH atas izin eksplisit Steven; nol perubahan kode aplikasi.

## Yang berubah di dunia nyata (VPS 103.93.134.22)

1. **Backend di-redeploy dari branch lama `feat/multi-tenant-saas` (35682f9) → `main` (844a8a4)**
   → `/analyses` naik dari **4 jadi 11**. Backup data + `.env` + config nginx dibuat lebih dulu.
2. **nginx: site BARU `fortunas-app`** (`server_name app.fortunas.id`) dipasang berdampingan —
   site lama `fortunas` (`server_name _`) TIDAK disentuh, jadi **demo `http://103.93.134.22`
   tetap hidup** (terverifikasi sesudahnya).
3. **TLS Let's Encrypt** terbit lewat `certonly --webroot` (nginx tidak perlu dimatikan),
   berlaku sampai 2026-11-06, timer perpanjangan aktif.
4. **Build React diunggah** ke `/var/www/fortunas` (via tar-over-ssh; rsync tidak ada di Windows).
   Halaman diagnosa dipasang lebih dulu dan hijau total sebelum ditimpa build.
5. **Hardening:** `JWT_SECRET` dirotasi on-box, `CORS_ORIGINS` → `https://app.fortunas.id`,
   `.env` + credentials di-`chmod 600`. `FORTUNAS_DEV_AUTH` memang tidak pernah diset (aman).

## Yang diuji sebagai tester (akun uji sendiri)

Akun `tester-20260808@fortunas.id` — "TOKO UJI - JANGAN DIPAKAI", kode publik `KDR-001`.
Rantai penuh terbukti: **register → provisioning BigQuery per-tenant → Kasir multi-item menulis
transaksi → analisis membacanya kembali → RAG + Gemini menghasilkan insight grounded**.

Angka yang layak dicatat: **`/ask` 3,4 detik** (target p95 ≤ 5 detik), **briefing 11 seksi**,
`top_product` mengembalikan angka persis dari BigQuery (Kopi Susu 2 unit / Rp 30.000).
DPA: password salah → ditolak dengan pesan BI; password benar → tersimpan v1.

Bukti lengkap (9 screenshot + kredensial akun uji) di folder induk
`Fortunas/brainstorming/evidence/2026-08-08-live-test/`; salinan screenshot di `Fortunas/SS/`.
Rincian per baris ada di `docs/VERIFICATION-2026-08-08.md` Bagian B.

## Yang BELUM teruji, dan cara membukanya

1. **Alur pelanggan (OTP → QR → attach ke Kasir → `/scan`)** — butuh flag dev sementara.
   Jalankan sebagai `deploy` di VPS, lalu kabari asisten:
   ```bash
   cd /opt/fortunas-ai && echo 'FORTUNAS_DEV_AUTH=1' >> .env && sudo systemctl restart fortunas-backend
   ```
   Setelah pengujian selesai, WAJIB dimatikan lagi:
   ```bash
   cd /opt/fortunas-ai && sed -i '/^FORTUNAS_DEV_AUTH=/d' .env && sudo systemctl restart fortunas-backend
   ```
   Alternatif permanen: pasang Firebase Phone Auth (menghapus kebutuhan flag sama sekali).
2. **Mikrofon, install PWA, boot offline** — perangkat fisik; ikuti `docs/PANDUAN-CEK-MANUAL.md`.
3. **Rotasi kredensial eksternal** (GEMINI/OPENAI/META) — butuh login akun, tugas Steven.
4. **⚠ Kunci SSH Ivan bocor** (private key ter-screenshot) — rotasi wajib; detail di
   `PENDING_EXTERNAL_SETUP.md`.

## Catatan untuk yang melanjutkan

- SSH VPS pakai user **`deploy`** (bukan `root`), sudo tanpa password. Login password mati.
- Jangan menimpa site nginx `fortunas` — itu yang menjaga demo lewat IP tetap hidup.
- Saat memanggil API backend, **baca `app/schemas.py` dulu**: dua kali dalam sesi ini payload
  ditebak dan kena 422 (`raw_text` bukan `agreement_text`; `birth_date` wajib di bootstrap).
- Tenant uji memprovisikan tabel BigQuery permanen — pakai akun lain untuk demo ke juri.
