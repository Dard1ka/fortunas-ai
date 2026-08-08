# Day 23 — R3 prep: file deploy ditulis ulang untuk klien React/Vite

**Tanggal:** 2026-08-08 · **Branch:** `feat/react-r3-deploy-docs` · Lanjutan day-22 (R2 read-only).
Dokumen/konfigurasi-only: nol perubahan kode aplikasi; eksekusi SSH/DNS tetap milik Steven (D7).

## Yang berubah

1. **`deploy/nginx-fortunas.conf`** — direvisi dari era Flutter ke Vite:
   - DIHAPUS: blok `flutter_service_worker.js` / `flutter_bootstrap.js` / `main.dart.js` /
     `manifest.json` / regex `.wasm` (tidak ada lagi file-file itu di build React).
   - Rantai boot baru **no-cache** (exact match): `index.html`, `manifest.webmanifest`
     (nama berubah dari manifest.json!), `sw.js`, `registerSW.js`.
   - **`^~ /assets/`** → `expires 1y` + `public, immutable` (aset Vite ber-hash; `^~` WAJIB
     supaya tidak kalah dari regex ekstensi — jebakan yang sama dengan `/media/`).
     Regex `workbox-*.js` (ber-hash, root dist) juga immutable, ditaruh SEBELUM regex umum.
   - File `public/` tak ber-hash (favicon/ikon/logo) → `expires 1h`.
   - DIPERTAHANKAN: HSTS diulang di setiap blok ber-`add_header` (jebakan inheritance),
     404 Swagger, `/api/` strip-proxy 120s + buffering off (SSE), `^~ /media/` tanpa strip,
     `try_files` SPA fallback (kini benar-benar terpakai — React Router path riil, bukan hash),
     `client_max_body_size 25m`, **4** placeholder `FORTUNAS_DOMAIN` (terverifikasi `grep -c` = 4).
   - gzip_types: buang wasm/ttf/otf (woff2 sudah terkompresi), tambah `application/manifest+json`.
2. **`deploy/DEPLOY.md`** — bagian PWA ditulis ulang: build = `cd frontend && npm ci && npm run
   build` (byte-identik CI); cek pasca-build pengganti useLocalCanvasKit = `grep -R
   "fonts.googleapis" dist/` HARUS kosong + 4 file rantai boot ada; rsync `frontend/dist/`
   (dry-run tetap WAJIB); § verifikasi pasca-deploy baru (no-cache vs immutable, SPA fallback
   deep-link, `/api/analyses` == 11, jebakan SW basi saat verifikasi); contoh domain →
   `app.fortunas.id`. **Urutan bootstrap diperbaiki** (temuan review): urutan lama melingkar
   ("kerjakan § 1 sebelum Step 7" padahal perintah § 1 menyasar file yang baru dibuat Step 7);
   kini Step 7 = pasang config TANPA reload → § 1 = DNS + `certbot certonly --standalone`
   (penerbitan pertama) → aktivasi `nginx -t && reload`. Step 1–6 backend tak berubah.
3. **`deploy/domain-check/`** — string build/upload → React (`frontend/dist/`), rujukan token
   warna → `frontend/src/theme/tokens.css`; logika halaman TIDAK diubah.
4. **`scripts/start.ps1` + `stop.ps1`** — frontend kini `vite preview` menyajikan
   `frontend/dist` di :5200 (python http.server dibuang: tanpa SPA fallback, refresh di rute
   dalam 404). Auto `npm ci`+build kalau dist belum ada; pola kill fallback frontend →
   `node.exe` + `vite` (dulu `python.exe` + `http.server`). Keduanya lolos parser PS 5.1.
5. **Runbook redeploy (folder induk, luar git)** — ditambah seksi "🚀 Urutan penuh R3"
   (R3-1 DNS → R3-2 nginx sebagai **site TERPISAH** `fortunas-app` → R3-3 certbot standalone +
   aktivasi → R3-4 redeploy backend [seksi lama, verbatim] → R3-5 domain-check DULUAN →
   R3-6 build+rsync → R3-7 verifikasi → R3-8 hardening [JWT_SECRET, CORS ketat,
   FORTUNAS_DEV_AUTH off, rotasi 6 kredensial] → R3-9 cek manual). **Temuan review penting
   yang sudah dibenamkan:** site lama JANGAN ditimpa & `default` JANGAN dihapus — `server_name`
   bukan filter; kalau site lama hilang, blok `:80` baru jadi catch-all dan me-redirect
   `http://103.93.134.22/*` ke HTTPS bersertifikat salah domain (demo IP mati). Dengan site
   terpisah, vhost `app.fortunas.id` menang via exact match dan bare-IP tetap ke site lama;
   satu-satunya downtime demo = ±1 menit saat certbot standalone.

## Yang sengaja TIDAK diubah

- `DEMO_SCRIPT.md` (rewrite milik PR-D Gate D; draf jalur demo React ada di folder induk).
- Backend & CI (nol perubahan; job names tak tersentuh).
- Server demo lama `http://103.93.134.22` — config baru hanya menyentuh `app.fortunas.id`.

## Catatan verifikasi

- `grep -c FORTUNAS_DOMAIN deploy/nginx-fortunas.conf` = **4** ✓ · parser PS 5.1 kedua script
  0 error ✓ · `nginx -t` lokal TIDAK bisa dijalankan (docker daemon mati di mesin dev) →
  cek sintaks final = `nginx -t` on-box saat R3-2 (sudah tertulis di runbook; kegagalan
  "cannot load certificate" sebelum certbot = jebakan terdokumentasi, bukan error sintaks).
- Draf direview adversarial multi-agen (lensa: jebakan nginx, kontrak spec §9, konsistensi
  lintas-file) sebelum PR — temuan CONFIRMED diterapkan.

## Berikutnya

Eksekusi R3 oleh Steven (urutan lengkap di runbook folder induk). Setelah R3-7: asisten
verifikasi dari luar + update `docs/VERIFICATION-2026-08-08.md` (B2/B5 → PROVEN) → R4
`docs/PANDUAN-CEK-MANUAL.md`.
