> ⚠️ **Bukan jalur deploy yang didukung.** Stack Docker ini terus disentuh
> setelah rewrite multi-tenant + auth (Task 1b sempat menghapus service
> `frontend`, Task 1e memulihkannya sebagai arsip; Task 1c mengarsipkan
> `ollama`) — jadi bukan "mendahului multi-tenant", tapi tetap tidak
> merepresentasikan bentuk stack multi-tenant saat ini secara cukup dekat
> untuk jadi jalur deploy resmi. Gunakan **[deploy/DEPLOY.md](deploy/DEPLOY.md)**
> (VPS: systemd + nginx) dan **[README.md](README.md)**. Disimpan sebagai arsip.
>
> **Status klien (2026-08-07, ADR-0002):** service `frontend` (React, image nginx-nya
> sendiri) mem-build **klien produksi** — React `frontend/` (React 19 + Vite). Flutter
> `mobile/` = deprecated, cadangan demo sampai Gate D, dijalankan di luar Docker.
> Lihat `docs/adr/0002-react-production-client.md`.

# Fortunas AI — Docker Setup Guide

Panduan lengkap menjalankan Fortunas AI menggunakan Docker.
Tidak perlu install Python atau Ollama secara manual — semua berjalan di dalam container.

---

## Arsitektur Docker

```
┌─────────────────────────────────────────────────────┐
│         React web (PWA), dev di luar Docker          │
│         cd frontend && npm run dev                   │
└──────────────────────┬──────────────────────────────┘
                       │ http://localhost:8000
         ┌─────────────▼─────────────┐
         │   fortunas_backend        │
         │   FastAPI + RAG pipeline  │
         │   port 8000 (exposed)     │
         └──────┬──────────┬─────────┘
                │          │
   ┌────────────▼───┐  ┌───▼──────────────────┐
   │ fortunas_ollama│  │  Google Cloud (ext.)  │
   │ Qwen3:8b       │  │  BigQuery + Gemini API│
   │ port 11434     │  └──────────────────────-┘
   │ (ARSIP —       │
   │  profile       │
   │  "archive",    │
   │  tidak start   │
   │  default)      │
   └────────────────┘

Volumes:
  ollama_data  → model weights (~4.8 GB), hanya terisi kalau profile archive dipakai
  chroma_data  → vector embeddings
  reports_data → daily briefing JSON
```

> Diagram di atas menampilkan jalur pengembangan (Vite dev server di luar
> Docker). `docker-compose.yml` juga punya service `fortunas_frontend`
> (nginx + React build produksi, port `3000:80`, `depends_on: backend`) —
> membangun klien produksi yang sama (ADR-0002). Catatan known-issue: nginx
> compose ini belum mem-proxy `/media/` (gambar produk 404 lewat service ini;
> perbaikannya dijadwalkan di Spec 2).

> **Ollama sekarang ARSIP, bukan bagian default stack.** `docker compose up`
> (tanpa flag tambahan) **tidak** menyalakan `fortunas_ollama` — servicenya
> ada di `docker-compose.yml` tapi di balik `profiles: ["archive"]`. LLM aktif
> = Gemini 2.5 Flash (API, lihat `app/llm_provider.py`), jadi backend jalan
> normal tanpa Ollama. Untuk sengaja menjalankan jalur lokal arsip:
> `docker compose --profile archive up ollama` + `LLM_PROVIDER=ollama` di `.env`.

> **Catatan port & CORS:** `docker-compose.yml` (production) mem-publish
> `8000:8000` langsung di service `backend` — ini tetap benar meski service
> `frontend` ada lagi (Task 1e), karena `frontend` mengakses backend lewat
> nginx proxy internal-nya sendiri (`docker/frontend/nginx.conf`, `/api/*` →
> `backend:8000`), bukan lewat port yang dipublish ke host. `CORS_ORIGINS` di
> file itu berisi placeholder (`http://localhost`, `http://127.0.0.1`) untuk
> pemanggil yang menghubungi `:8000` langsung dari origin lain — sesuaikan
> dengan origin asli tempat client benar-benar disajikan (mis. Vite dev
> server `http://localhost:3000`). Di jalur deploy yang didukung
> (`deploy/nginx-fortunas.conf`), PWA dan API disajikan same-origin sehingga
> CORS tidak relevan sama sekali.

---

## Prasyarat

| Kebutuhan | Versi | Cek |
|---|---|---|
| Docker Desktop | 25+ | `docker --version` |
| Docker Compose | v2 (sudah bundled) | `docker compose version` |
| RAM bebas | min 8 GB | Task Manager |
| Disk bebas | min 10 GB | (model + images) |
| File `.env` | sudah diisi | lihat step 1 |
| Service account JSON | ada di `credentials/` | lihat step 2 |

Download Docker Desktop: https://www.docker.com/products/docker-desktop/

---

## Step-by-Step Setup

### Step 1 — Siapkan file `.env`

```bash
cp .env.example .env
```

Buka `.env` dan pastikan nilai berikut sudah diisi:

```dotenv
# WAJIB diisi:
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json
BIGQUERY_PROJECT_ID=nama-project-gcp-kamu
GOOGLE_SHEETS_ID=id-spreadsheet-kamu

# Sudah ada default yang benar untuk Docker — tidak perlu diubah:
OLLAMA_BASE_URL=http://ollama:11434    ← pakai nama service, bukan localhost
CHROMA_DB_PATH=/data/chroma_db
```

> ⚠️ **Penting:** Di Docker, Ollama berjalan sebagai service bernama `ollama`.
> Jadi `OLLAMA_BASE_URL` harus `http://ollama:11434`, **bukan** `http://localhost:11434`.

---

### Step 2 — Taruh Service Account JSON

Pastikan file JSON credentials Google Cloud ada di:

```
credentials/
└── service-account.json    ← nama file bebas, sesuaikan di .env
```

```bash
# Contoh:
mkdir -p credentials
cp /path/ke/file-sa-kamu.json credentials/service-account.json
```

File ini di-mount sebagai read-only ke dalam container backend di `/app/credentials/`.

---

### Step 3 — Build & Start (pertama kali)

```bash
docker compose up --build
```

Atau pakai Makefile:
```bash
make up
```

Proses pertama kali akan:
1. Download base image backend (python:3.11-slim) — `ollama/ollama` HANYA ter-download kalau kamu pakai `docker compose --profile archive up ollama` sengaja, bukan dengan `docker compose up --build` biasa
2. Install semua Python dependencies — ~5 menit
3. Start service `backend` (satu-satunya service default; `ollama` di-skip karena `profiles: ["archive"]`)

Log yang normal saat startup (default, `LLM_PROVIDER=gemini`, tanpa profile archive —
`docker/backend/entrypoint.sh` mengecek `LLM_PROVIDER` **sebelum** mencoba
menghubungi Ollama sama sekali, jadi tidak ada delay tunggu di jalur ini):
```
fortunas_backend | [1/3] LLM_PROVIDER=gemini — skipping Ollama wait (not selected).
fortunas_backend | [2/3] First boot — running knowledge base ingest...
fortunas_backend | ✓ Knowledge base ingest complete.
fortunas_backend | [3/3] Starting FastAPI (uvicorn)...
fortunas_backend | INFO: Application startup complete.
```
> **Sebelum diperbaiki (Task 1d, 2026-08-07), ini bukan perilakunya.**
> `entrypoint.sh` dulu selalu mencoba ping Ollama dulu tanpa syarat — jadi tiap
> `docker compose up` biasa (Ollama archived, service-nya tidak jalan) diam-diam
> nunggu ~2,5 menit (30x percobaan, jeda 5 detik) sebelum akhirnya lanjut. Itu
> justru mengulang masalah yang mau dihindari arsip: backend tetap berlaku
> seolah Ollama aktif walau sudah dipindah ke profile arsip. Sudah digate di
> `entrypoint.sh` supaya wait-loop-nya skip untuk `LLM_PROVIDER=openai` atau
> `gemini` dan jalan untuk nilai lain mana pun (Task 1e menyempurnakan gate-nya
> supaya persis meniru routing `app/llm_provider.py`, bukan cuma cek string
> `"ollama"` — lihat Troubleshooting di bawah untuk kenapa itu penting).
>
> Kalau kamu sengaja menjalankan `docker compose --profile archive up ollama` +
> `LLM_PROVIDER=ollama`, log-nya jadi (persis seperti sebelumnya, tidak diubah
> untuk jalur ini):
> ```
> fortunas_backend | [1/3] LLM_PROVIDER=ollama — waiting for Ollama at http://ollama:11434...
> fortunas_backend |    ... attempt 1/30, retrying in 5s   (berulang sampai 30x kalau ollama belum siap)
> fortunas_backend | ✓ Ollama is ready.
> ```
> Catatan kecil: baris `✓ Ollama is ready.` ini tercetak tanpa syarat setelah
> loop selesai — termasuk kalau loop-nya habis 30x percobaan tanpa pernah
> berhasil (kasus itu juga akan menampilkan baris peringatan `⚠ Ollama not
> ready after 30 attempts. Starting anyway...` tepat sebelumnya). Ini quirk
> lama di skrip yang tidak disentuh task ini — kalau kamu melihat kedua baris
> itu bersamaan, itu berarti Ollama memang belum siap walau pesannya bilang
> "ready".

---

### Step 4 — (OPSIONAL, hanya untuk jalur arsip) Pull Model Qwen3:8b

LLM aktif produksi = **Gemini 2.5 Flash**, jadi step ini **tidak wajib** untuk
menjalankan aplikasi. Kerjakan hanya kalau kamu sengaja mau memakai jalur lokal
arsip (`LLM_PROVIDER=ollama`):

```bash
docker compose --profile archive up -d ollama   # nyalakan service ollama dulu
make pull-model
```

Atau manual:
```bash
docker compose --profile archive exec ollama ollama pull qwen3:8b
```

> Model berukuran **~4.8 GB**. Proses download mungkin membutuhkan 10–30 menit
> tergantung kecepatan internet. Setelah selesai, model tersimpan di volume
> `ollama_data` sehingga tidak perlu didownload ulang.

Verifikasi:
```bash
make model-list
# atau
docker compose --profile archive exec ollama ollama list
```

---

### Step 5 — Buka Aplikasi

| URL | Keterangan |
|---|---|
| http://localhost:8000/docs | Swagger UI backend (hanya di dev mode) |
| http://localhost:11434 | Ollama API — hanya ada kalau `--profile archive` dipakai |

Untuk pengembangan client, jalankan Vite dev server terpisah dari stack Docker
ini (`cd frontend && npm run dev`) — atau pakai service `frontend` compose (:3000).

---

## Perintah Sehari-hari

```bash
# Start tanpa rebuild (setelah pertama kali)
docker compose up -d

# Stop semua
docker compose down

# Lihat status containers
make ps

# Stream log semua service
make logs

# Stream log backend saja
make logs-backend

# Masuk ke shell backend (debugging)
make shell-backend

# Re-run ingest knowledge base (jika dokumen di umkm_docs/ berubah)
make ingest

# Restart satu service saja
docker compose restart backend
```

---

## Development Mode (Hot Reload)

Untuk developer yang aktif mengubah kode:

```bash
make dev
```

Perbedaan dengan mode production:
- **Backend**: source code di-mount langsung → perubahan `.py` langsung efektif tanpa rebuild
- Port `8000` sama-sama dibuka ke host di kedua mode (lihat catatan port & CORS di atas) — bisa akses Swagger di http://localhost:8000/docs, dan client dev (`npm run dev`) bisa connect ke `http://localhost:8000`

```bash
# Stop dev mode
make dev-down
```

---

## Struktur File Docker

```
Fortunas/
├── docker/
│   ├── backend/
│   │   ├── Dockerfile        ← image backend FastAPI
│   │   └── entrypoint.sh     ← startup script (wait Ollama → ingest → uvicorn)
│   └── ollama/
│       └── pull-model.sh     ← helper script pull qwen3:8b
│
├── docker-compose.yml        ← production stack
├── docker-compose.dev.yml    ← development stack (hot reload)
├── .dockerignore             ← file yang tidak masuk ke build context
└── Makefile                  ← shortcut commands
```

---

## Troubleshooting

### "Ollama not ready after 30 attempts. Starting anyway..."
Sejak `entrypoint.sh` di-gate (Task 1d, gate-nya disempurnakan lagi di Task 1e
supaya persis meniru routing `app/llm_provider.py`), pesan ini **hanya bisa
muncul** di jalur tunggu Ollama — yaitu kalau `LLM_PROVIDER` (setelah
di-trim + lowercase) bukan persis `openai` atau `gemini`. Dengan
`LLM_PROVIDER=gemini` (default, dan yang dipin di `.env.example` maupun
`deploy/.env.production.example`), skrip **skip** wait ini sama sekali —
pesan ini **tidak akan pernah muncul** di jalur default (lihat contoh log
Step 3 di atas, tanpa delay).

Kalau kamu benar-benar melihat pesan ini:
- **Sengaja pakai jalur arsip** (`LLM_PROVIDER=ollama`) tapi lupa nyalakan
  service-nya? Nyalakan dengan profile-nya:
  ```bash
  docker compose --profile archive up -d ollama
  docker compose --profile archive ps
  docker compose --profile archive logs ollama

  # Restart jika perlu
  docker compose --profile archive restart ollama
  docker compose restart backend
  ```
- **Tidak sengaja?** Cek nilai `LLM_PROVIDER` di `.env` — kemungkinan kosong
  atau typo (bukan persis `openai`/`gemini`). Nilai seperti itu bukan cuma
  bikin `entrypoint.sh` menunggu Ollama: `app/llm_provider.py` sendiri juga
  diam-diam merutekan ke `_ollama_generate()` lewat `else` bare untuk nilai
  apa pun selain `openai`/`gemini` — jadi ini perilaku aplikasi yang nyata,
  bukan cuma cerita startup script. Perbaiki nilainya jadi `gemini`.

### "Cannot connect to BigQuery"
```bash
# Cek credentials sudah ada
ls credentials/service-account.json

# Cek .env sudah benar
grep GOOGLE_APPLICATION_CREDENTIALS .env
# Harus: GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json

# Cek di dalam container
make shell-backend
ls /app/credentials/
```

### "Port 8000 already in use" (mode dev)
```bash
# Ganti port di docker-compose.dev.yml:
ports:
  - "8001:8000"    # ubah 8000 ke port lain
```

### Ingin reset semua data (chroma, reports)
```bash
docker compose down -v    # hapus semua volumes
docker compose up --build # rebuild dari nol
# Kalau kamu pakai jalur arsip (LLM_PROVIDER=ollama), model perlu di-pull ulang:
# make pull-model
```

### Backend lambat saat pertama kali
Normal. Saat pertama boot, backend menjalankan ingest knowledge base + load model embeddings. Setelah itu restart berikutnya jauh lebih cepat karena ada marker file `.ingest_done`.

---

## Checklist Sebelum Commit Docker Files

```bash
# Validasi compose TANPA mencetak nilai .env ke terminal/transkrip.
# ⚠️ JANGAN jalankan `docker compose config` polos — perintah itu
# meng-interpolasi .env dan MENCETAK semua secret (insiden nyata 2026-08-07:
# 6 kredensial bocor ke transkrip sesi dan harus dirotasi).
docker compose config --quiet && echo "compose OK"

# File yang WAJIB ada sebelum docker compose up:
ls .env                                  # isi nilai nyata (jangan commit)
ls credentials/service-account.json     # (jangan commit)
ls .env.example                         # template (boleh commit)
ls .dockerignore                        # (wajib commit)
ls docker-compose.yml                   # (wajib commit)
```
