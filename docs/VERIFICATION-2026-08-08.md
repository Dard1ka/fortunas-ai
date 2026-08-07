# VERIFICATION — 2026-08-08 (R2, lingkup read-only)

- **SHA:** `ccfa641` (main; PR #27–#31 merged) · **Frontend:** `frontend@4.1.0` (skema versi belum final dikonfirmasi)
- **Lingkup:** porsi **read-only** dari R2 (spec 2 §8). Akun UMKM uji + izin tulis dari Steven **belum tersedia** →
  walkthrough authenticated & uji tulis (Checkout/DPA) dicatat BLOCKED, **bukan** dikerjakan diam-diam.
  Self-register ke backend live DILARANG (register memprovisikan tabel BigQuery per-tenant permanen).
- **Persetujuan menulis ke tenant uji: BELUM ADA.** Saat Steven memberikan akun uji + konfirmasi eksplisit
  boleh menulis (checkout + perubahan DPA), persetujuan itu dicatat di seksi ini, lalu item BLOCKED #1/#4
  dijalankan dan dipindah ke PROVEN.
- **Evidence (luar repo):** `Fortunas/brainstorming/evidence/2026-08-08-react-parity/` (PNG matriks, log
  console/network, `GATE.md`). Salinan screenshot juga di `Fortunas/SS/`.
- Aturan dokumen: baris PROVEN wajib perintah persis + output verbatim; BLOCKED wajib alasan + pembuka.

---

## PROVEN

### P1 — Lint bersih

Perintah: `cd frontend && npm run lint`

```
> frontend@4.1.0 lint
> eslint .

EXIT=0
```

### P2 — Test suite hijau (48/48)

Perintah: `cd frontend && npm test` (dijalankan pada tree yang sama, `ccfa641`)

```
> frontend@4.1.0 test
> vitest run

 Test Files  16 passed (16)
      Tests  48 passed (48)
   Start at  01:34:45
   Duration  10.29s (transform 2.98s, setup 8.25s, import 5.26s, tests 9.99s, environment 62.90s)
```

### P3 — Build produksi sukses

Perintah: `cd frontend && npm run build`

```
vite v8.0.8 building client environment for production...
✓ 105 modules transformed.
dist/registerSW.js                                            0.13 kB
dist/index.html                                               1.55 kB │ gzip:  0.73 kB
[... 20 aset font woff/woff2 ber-hash di dist/assets/ ...]
dist/assets/index-mQMOAKVG.css                                5.41 kB │ gzip:  1.66 kB
dist/assets/chunk-B3K2TuZy.js                                 0.55 kB │ gzip:  0.35 kB
dist/assets/browser-l7PurnjH.js                              23.46 kB │ gzip:  8.85 kB   ← chunk lazy qrcode
dist/assets/index-ljFSdJ5N.js                               332.77 kB │ gzip: 97.04 kB
✓ built in 408ms

PWA v1.3.0
mode      generateSW
precache  22 entries (861.04 KiB)
files generated
  dist/sw.js
  dist/workbox-9c191d2f.js
EXIT=0
```

### P4 — Payload entry ≤ budget 300 KB gzip

Metode terdokumentasi (spec §7): gzip level 9 (python) atas aset JS+CSS yang direferensikan `dist/index.html`
(chunk lazy qrcode TIDAK dihitung — dimuat on-demand di `/customer/qr`).

```
index-ljFSdJ5N.js: 93.62 KB gzip
chunk-B3K2TuZy.js: 0.35 KB gzip
index-mQMOAKVG.css: 1.61 KB gzip
TOTAL entry JS+CSS: 95.58 KB gzip (budget 300 KB)
```

### P5 — Nol request pihak ketiga di build

Perintah: `grep -R "fonts.googleapis" dist/`

```
grep_exit=1   (nol match)
```

Isi root `dist/`: `assets/ favicon.svg icons.svg index.html logo-mark-256.png logo-mark.svg logo.svg
manifest.webmanifest registerSW.js sw.js workbox-9c191d2f.js` — font self-host semuanya di `dist/assets/`.

### P6 — Gate backend: CI `Backend (ruff + pytest)` hijau di `ccfa641`

Perintah: `gh run list --branch main ... | select(.headSha|startswith("ccfa641"))` lalu `gh run view 31207144452 --json jobs`

```
{"conclusion":"success","databaseId":31207144452,
 "url":"https://github.com/Dard1ka/fortunas-ai/actions/runs/31207144452"}

{"conclusion":"success","name":"Backend (ruff + pytest)"}
{"conclusion":"success","name":"Frontend (lint + test + build)"}
{"conclusion":"success","name":"Mobile (flutter analyze)"}
```

### P7 — Backend live hidup (probe read-only)

Perintah: `curl -s -m 15 http://103.93.134.22/{health,llm/health,rag/health}` — semua HTTP 200:

```
== /health
{"status":"ok","rag_enabled":true}
== /llm/health
{"status":"ok","provider":"gemini","model":"gemini-2.5-flash"}
== /rag/health
{"status":"ok","rag_enabled":true,"collection_count":56,"error":""}
```

### P8 — Probe `/analyses` live menjawab 4 (bukti deploy basi — lihat BLOCKED #2)

Perintah: `curl -s http://103.93.134.22/analyses | python -c "...len(...)..."`

```
count = 4
keys = ['repeat_customer', 'high_value_customer', 'peak_hour', 'bundle_opportunity']
```

### P9 — Matriks browser riil 390/800/1024/1440 (Playwright, dev server → proxy ke VPS live)

Server: `npx cross-env VITE_API_TARGET=http://103.93.134.22 npm run dev` (proxy `/api` server-side; jalur ini
tidak bergantung CORS). Screenshot di folder evidence:

| File | Verdict visual |
|---|---|
| `login-390.png` | Compact: form full-width, tombol "Masuk" violet solid + border ink + hard shadow |
| `login-800.png` | ≥medium: kartu putih 420px terpusat dua sumbu, border ink, hard shadow |
| `login-1024.png` | Idem 800 — band 1024 (dulu bermasalah di Flutter) bersih, tanpa overflow |
| `login-1440.png` | Idem — kartu tetap 420px, terpusat |
| `customer-1440.png` | **Phone-only PROVEN:** kolom 430px + backdrop `#E9E4D8` di viewport 1440 |
| `customer-login-390.png` | Compact customer: layar "Masuk pelanggan" utuh |

Console seluruh sesi: **0 error, 0 warning** (hanya info React DevTools dev-mode + 1 saran verbose
`autocomplete` di input password — observasi minor). Network: **semua 200 OK, semuanya same-origin,
nol pihak ketiga, nol panggilan `/api/*` dari layar pra-auth**. Detail: `console-network-log.md` +
`network-requests.md` di folder evidence.

### P10 — Guard alur customer

`/customer/otp` diakses langsung tanpa state nomor HP → redirect ke `/customer/login` (perilaku benar,
sesuai desain alur OTP).

---

## BLOCKED

| # | Apa | Kenapa | Pembuka |
|---|---|---|---|
| B1 | Walkthrough authenticated vs live: Login → Tanya → Result → Briefing → Riwayat → Profil → Kasir → DPA → Scan (+ rute customer ber-token) | Belum ada akun UMKM uji; self-register DILARANG (provisi tabel BigQuery permanen di dataset produksi); login/bootstrap coba-coba = menulis DB live | Steven kirim 1 akun UMKM uji + konfirmasi eksplisit boleh MENULIS (checkout + DPA) ke tenant uji — persetujuan dicatat di dokumen ini, lalu walkthrough + screenshot Checkout/DPA sukses dijalankan |
| B2 | `/analyses == 11` di live | Deploy VPS basi — masih 4 analisis (bukti P8); kode `main` sudah 11 | Langkah R3-4: redeploy backend ke `main` (runbook `Fortunas/REDEPLOY_VPS_RUNBOOK.md`; BACKUP DB, JANGAN alembic, verifikasi on-box) |
| B3 | Mikrofon/voice, install PWA (Android/iOS), offline-boot di HP | Semua dikunci browser di balik secure context — `app.fortunas.id` belum ada TLS | R3 (DNS + certbot) → dijalankan Steven via `docs/PANDUAN-CEK-MANUAL.md` (R4) |
| B4 | Checkout multi-item + attach token QR & DPA edit terhadap backend live | Gabungan B1 (butuh akun + izin tulis) | Sama dengan B1; token QR harus SEGAR (single-use, TTL 90 dtk) saat dijalankan |
| B5 | Header cache produksi (`index.html`/`manifest.webmanifest`/`sw.js` no-cache; `/assets/*` immutable) + SW live | Belum ada deploy React di VPS; nginx masih config era Flutter | R3-2/R3-6/R3-7 (revisi nginx + upload build) — draf conf sudah disiapkan di PR R3 |

---

## Riwayat pembaruan

- **2026-08-08** — dokumen dibuat (lingkup read-only). Pembaruan berikutnya: saat akun uji tersedia (B1/B4),
  pasca-redeploy backend (B2), pasca-R3 (B3/B5).
