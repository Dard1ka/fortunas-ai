# Day 22 — R2: verifikasi (lingkup read-only) — PROVEN/BLOCKED terdokumentasi

**Tanggal:** 2026-08-08 · **Branch:** `docs/react-r2-verification` · Lanjutan day-21 (R1d).
Dokumen-only: nol perubahan kode aplikasi.

## Yang dikerjakan

1. **`docs/VERIFICATION-2026-08-08.md`** — laporan R2 dengan pemisahan keras PROVEN (perintah +
   output verbatim) vs BLOCKED (alasan + pembuka), sesuai spec 2 §8.
2. **PROVEN (10 baris):** lint 0 · test 48/48 (16 file) · build sukses (sw.js + workbox ber-hash +
   registerSW.js) · payload entry **95,58 KB gzip** (metode gzip-9 python; budget 300 KB) · nol
   `fonts.googleapis` di dist · CI @ ccfa641 tiga job success (run 31207144452) · live
   `/health` `/llm/health` `/rag/health` 200 ok · matriks Playwright 390/800/1024/1440 (kartu auth
   420px, compact utuh, console 0 error, network 0 gagal, nol pihak ketiga) · phone-only
   `/customer/*` terbukti di 1440 (kolom 430px + backdrop) · guard `/customer/otp` redirect benar.
3. **BLOCKED (5 baris, dengan pembuka):** walkthrough authenticated + uji tulis Kasir/DPA (butuh
   akun uji + izin tulis Steven — self-register DILARANG, provisi BQ permanen) · `/analyses` live
   masih **4** = deploy basi (pembuka: redeploy R3-4) · mic/install/offline (butuh TLS R3 → panduan
   R4) · header cache produksi + SW live (butuh deploy R3).
4. Evidence (luar repo, folder induk): `Fortunas/brainstorming/evidence/2026-08-08-react-parity/`
   — 6 PNG + `network-requests.md` + `console-network-log.md` + `GATE.md`; salinan PNG di `Fortunas/SS/`.
5. Draf jalur demo React disiapkan di folder induk (DEMO_SCRIPT.md TIDAK diedit — milik Gate D).

## Angka

48 test (16 file) · lint 0 · entry 95,58 KB gzip + lazy qrcode 8,85 KB · precache SW 22 entri (861 KiB).

## Prasyarat yang ditagih (aksi Steven)

1. **1 akun UMKM uji + konfirmasi eksplisit boleh MENULIS** (checkout + DPA) ke tenant uji →
   membuka B1/B4; persetujuan akan dicatat di VERIFICATION.
2. **Redeploy backend VPS ke main** (4→11) → membuka B2.
3. TLS `app.fortunas.id` (DNS + certbot) → membuka B3/B5; file deploy React disiapkan di PR R3 terpisah.
4. Edarkan ADR-0002 ke tim (1/4 tanda tangan).

## Berikutnya

PR R3 (`feat/react-r3-deploy-docs`): revisi `deploy/nginx-fortunas.conf` untuk Vite, rewrite
`deploy/DEPLOY.md`, string `deploy/domain-check`, `scripts/start.ps1` → serve `frontend/dist`.
Setelah akun uji ada: walkthrough tulis + update VERIFICATION (B1/B4 → PROVEN) → R4 panduan manual.
