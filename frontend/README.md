# Fortunas AI — Web Client (Produksi)

Klien produksi Fortunas AI: **React 19 + Vite** — stack yang di-commit proposal hibah.
Satu-satunya klien sejak Gate D (ADR-0002): [`docs/adr/0002-react-production-client.md`](../docs/adr/0002-react-production-client.md).

## Menjalankan

```bash
npm ci          # sekali, atau setelah lockfile berubah
npm run dev     # dev server :3000, proxy /api → VITE_API_TARGET (default 127.0.0.1:8000)
npm run lint    # eslint 9
npm run build   # produksi → dist/ (perintah rilis; identik dengan CI)
```

Node ≥ 20.19 (Vite 8). Backend lokal penuh tidak bisa jalan tanpa deps berat (chromadb) —
untuk verifikasi live pakai `cross-env VITE_API_TARGET=<backend> npm run dev` (proxy
server-side; tidak tergantung CORS).

## Peta singkat

- `src/screens/` — Home, Result, Briefing, History, Profile, Login (+ layar baru per Spec 2)
- `src/voice/` — dictation Web Speech API (id-ID) + alur transaksi suara
- `src/api/client.js` — fetch wrapper: BASE `/api`, Bearer JWT, 401 → logout event
- `src/theme/tokens.css` — design tokens neo-brutalist
- `src/_legacy/` — UI v1, di luar build graph; referensi wiring backend, jangan dipakai fitur baru

## CI & deploy

- CI: job `Frontend (lint + test + build)` di `.github/workflows/ci.yml` — build CI wajib
  byte-identik dengan perintah rilis.
- Deploy: `dist/` di-rsync ke docroot VPS same-origin `app.fortunas.id` (lihat `deploy/DEPLOY.md`).
