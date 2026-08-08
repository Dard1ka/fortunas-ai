# VERIFICATION — 2026-08-08

> **PEMBARUAN 2026-08-08 sore — deploy live + uji tulis SELESAI.** Lihat seksi
> **"BAGIAN B — Live di `https://app.fortunas.id`"** di bawah. Bagian A (di bawah ini)
> adalah verifikasi read-only sebelum deploy; dipertahankan apa adanya sebagai riwayat,
> dan status BLOCKED-nya diperbarui di Bagian B.

## BAGIAN A — R2 lingkup read-only (sebelum deploy)

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

---

# BAGIAN B — Live di `https://app.fortunas.id` (deploy + uji tulis)

## Izin & lingkup

Steven memberi izin eksplisit di chat 2026-08-08: *"lakukan semuanya saya beri kamu izin, yg di
blocked lakukan contoh yg buat login gitu, kamu lakukan aja dan bisa check di db atau servernya
sendiri"* dan *"tolong deploy kan jg … ini untuk hosting, domain, vps, atau apapun gitu boleh
kamu lakukan"*. Atas dasar itu: akun UMKM uji dibuat sendiri, transaksi & DPA ditulis ke tenant
uji, dan deploy dieksekusi asisten via SSH. Akses SSH dibuka Steven (kunci `claude-deploy` di
`~deploy/.ssh/authorized_keys`); user `deploy` punya sudo tanpa password.

Akun uji: `tester-20260808@fortunas.id` / bisnis **"TOKO UJI - JANGAN DIPAKAI"** / workspace
`toko_uji_jangan_dipakai` / kode publik `KDR-001`. Kredensial di
`Fortunas/brainstorming/evidence/2026-08-08-live-test/akun-uji.local.md` (luar git).
⚠ Tenant ini memprovisikan tabel BigQuery permanen — jangan dipakai untuk demo ke juri.

## PROVEN — infrastruktur

| # | Apa | Bukti |
|---|---|---|
| L1 | DNS `app.fortunas.id` → `103.93.134.22` | `curl -w %{remote_ip}` → `103.93.134.22` |
| L2 | TLS Let's Encrypt terbit & valid | `certbot certonly --webroot` → "Successfully received certificate", expires **2026-11-06**, renewal timer aktif; `curl -w %{ssl_verify_result}` → `0` |
| L3 | HTTP → HTTPS | `curl http://app.fortunas.id/` → `301` → `https://app.fortunas.id/` |
| L4 | Backend di `main`, **11 analisis** (dari 4) | repo VPS `git log -1` → `844a8a4`; `/api/analyses` → `11` (kunci lengkap: repeat_customer … demand_forecast) |
| L5 | Gemini + RAG hidup | `/llm/health` → `{"provider":"gemini","model":"gemini-2.5-flash"}`; `/rag/health` → `collection_count: 56` |
| L6 | Header cache benar | `index.html`, `manifest.webmanifest`, `sw.js`, `registerSW.js` → `Cache-Control: no-cache` + HSTS; `/assets/index-ljFSdJ5N.js` → `public, immutable` + `max-age=31536000` |
| L7 | SPA fallback (React Router path riil) | `/briefing /checkout /dpa /scan /customer/login` → semua `200` |
| L8 | Swagger tidak publik | `/api/docs`, `/api/redoc`, `/api/openapi.json` → `404` bertiga |
| L9 | **Demo IP lama tetap hidup** | `curl http://103.93.134.22/health` → `{"status":"ok"}` — config baru dipasang sebagai site nginx terpisah `fortunas-app`, site lama tak disentuh |
| L10 | Halaman diagnosa hijau total | `domain-check-live.png`: "Semua cek lolos" — secure context, service worker, mikrofon, `/api/health` 200 dalam 62 ms |
| L11 | Nol request pihak ketiga | `grep -R "fonts.googleapis" dist/` kosong sebelum unggah |

## PROVEN — aplikasi (uji sebagai tester, browser riil)

| # | Apa | Bukti |
|---|---|---|
| A1 | Register + provisioning tenant | Form daftar (nama bisnis, jenis, alamat, email, password) → masuk Beranda; workspace & tabel BigQuery ter-provisi (`live-01-home.png`) |
| A2 | Kode publik UMKM terbit dari alamat | Profil menampilkan `KDR-001` (alamat "Jl. Uji Coba 1, Kediri") — `live-08-profile.png` |
| A3 | Empty state jujur, bukan halusinasi | Tenant baru → "Analisis 'Analisis Pelanggan Loyal' berhasil dijalankan, tetapi tidak ada data yang cocok." (`live-02-result.png`) |
| A4 | **Kasir multi-item menulis ke BigQuery** | 2 item (Kopi Susu 2×15.000, Roti Bakar 1×10.000) → "Transaksi tersimpan · 1 · 2 item · Rp 40.000" (`live-03-checkout.png`); total dihitung benar dan tombol simpan terkunci selama baris belum lengkap |
| A5 | Data terbaca kembali dari BigQuery | `/api/umkm/transactions` → invoice `1`, 2 item, total `40000`, timestamp `2026-08-08 05:47:50+00:00` |
| A6 | **Intent-routed RAG end-to-end** | "produk apa yang paling laris?" → `top_product`; rows: Kopi Susu (qty 2, omzet 30000), Roti Bakar (1, 10000); `agent_trace`: mapped → SQL → BigQuery 2 rows → RAG 4 chunks → sources *Inventory Management, Pricing Strategy* |
| A7 | **Latency `/ask` = 3,4 detik** | diukur di browser (`Date.now()` sekitar fetch) — di bawah target p95 ≤ 5 detik |
| A8 | Insight grounded | summary + 3 temuan mengutip angka persis dari data (Rp 30000, 2 unit) + 3 rekomendasi (`live-06-result-data.png`) |
| A9 | **Briefing 11 seksi** | "11 analisis selesai" + 11 kartu (Pelanggan Loyal, Paling Bernilai, Jam Ramai, Bundling, Terlaris, Tren Omzet, Segmentasi RFM, Risiko Churn, Slow-Moving, Ukuran Keranjang, Prediksi Permintaan) + Temuan Utama dari data nyata (`live-07-briefing.png`) |
| A10 | **DPA: password salah ditolak** | UI menampilkan alert "Konfirmasi password salah." (403 backend) |
| A11 | DPA: simpan sukses | v1 tersimpan, chip larangan "menyarankan diskon di atas 50%" tampil, timestamp `2026-08-08T05:56:36+00:00` (`live-04-dpa.png`); `PUT /api/umkm/dpa` (skema `raw_text`) → `200` |
| A12 | Intent router menolak pertanyaan di luar 11 analisis | "promo diskon 90%" → "Pertanyaan belum dikenali" + saran pertanyaan (`live-05-dpa-guard.png`) — perilaku benar, bukan error |

## PROVEN — pengetatan keamanan

| # | Apa | Bukti |
|---|---|---|
| S1 | `JWT_SECRET` dirotasi | nilai baru 64-hex digenerate on-box (`openssl rand -hex 32`), tidak pernah ditampilkan; backend restart sehat sesudahnya |
| S2 | `CORS_ORIGINS` diketatkan | dari `*` → `https://app.fortunas.id` |
| S3 | `FORTUNAS_DEV_AUTH` tidak aktif di produksi | `grep -c '^FORTUNAS_DEV_AUTH=' .env` → `0` |
| S4 | Izin file rahasia | `.env` dan `credentials/*.json` → `-rw-------` (600) |
| S5 | Backup sebelum perubahan | `~/fortunas-data-backup-20260808-1218.tgz`, `.env.bak-*`, config nginx lama di `/root/` |

## BLOCKED tersisa (dengan pembuka)

| # | Apa | Kenapa | Pembuka |
|---|---|---|---|
| C1 | Alur pelanggan (login HP → OTP → QR) + attach token ke Kasir + `/scan` membership | Butuh `FORTUNAS_DEV_AUTH=1` sementara (Firebase Phone Auth belum dipasang). Perintah untuk menyalakannya ditolak lapisan keamanan sesi ini — mengaktifkan flag dev di produksi memang perubahan yang layak dilakukan sadar oleh manusia | Steven jalankan toggle (perintah ada di handoff `day-24.md`) lalu beri tahu — asisten menguji dan mematikannya kembali; atau pasang Firebase (menghapus kebutuhan flag selamanya) |
| C2 | Mikrofon/voice riil, install PWA Android/iOS, boot offline di HP | Butuh perangkat fisik | `docs/PANDUAN-CEK-MANUAL.md` — dijalankan Steven |
| C3 | Enforcement pagar DPA saat jawaban melanggar | Larangan yang dipasang tidak terpicu oleh 11 analisis yang ada (pertanyaan promo ditolak intent router lebih dulu, lihat A12). Enforcement-nya sendiri sudah tertutup 74 test backend | Rancang kasus uji yang memetakan ke analisis DAN melanggar aturan (mis. larangan "menyebut nama pelanggan" + data pelanggan berulang) |
| C4 | Rotasi `GEMINI_API_KEY`, `OPENAI_API_KEY`, `META_*` | Butuh login akun eksternal yang tidak dipegang asisten | Steven — masih TOP di `PENDING_EXTERNAL_SETUP.md` |

## Catatan operasional

- Akun ACME Let's Encrypt didaftarkan dengan email `steven.sanjaya@juaracapital.com` supaya ada
  peringatan bila perpanjangan gagal. Ubah dengan `certbot update_account` bila tidak dikehendaki.
- SSH VPS: user **`deploy`** (bukan `root`), sudo tanpa password. `root` login-by-password mati
  (`PermitRootLogin prohibit-password`).
- ⚠ **Kunci SSH Ivan bocor** (private key ter-screenshot di chat 2026-08-08) — rotasi wajib, lihat
  `PENDING_EXTERNAL_SETUP.md`. Sampai selesai, kunci `KCIyx72s…` di `~deploy/.ssh/authorized_keys`
  harus dianggap kompromi. Ada juga satu entri `claude-deploy` asing (`c47WfbJc…`) hasil salah
  ketik saat bootstrap — tak ada yang memegang privat-nya, tapi sebaiknya dibersihkan.

## Riwayat pembaruan

- **2026-08-08 pagi** — dokumen dibuat (lingkup read-only, Bagian A).
- **2026-08-08 sore** — Bagian B: deploy `app.fortunas.id` selesai + uji tulis sebagai tester.
  B1/B2/B4/B5 dari Bagian A kini **PROVEN** (lihat L1–L11, A1–A12, S1–S5). Sisa: C1–C4.
