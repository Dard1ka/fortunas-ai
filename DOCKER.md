> ⚠️ **USANG (pra-v4.0).** Stack Docker ini mendahului multi-tenant + auth, dan
> bukan jalur deploy yang didukung sekarang. Gunakan **[deploy/DEPLOY.md](deploy/DEPLOY.md)**
> (VPS: systemd + nginx) dan **[README.md](README.md)**. Disimpan sebagai arsip.
>
> Catatan tambahan: service `frontend` (React, dulu di-build dari image nginx-nya sendiri) yang dirujuk
> di dokumen ini sudah dihapus dari repo dan dari `docker-compose*.yml`. Klien
> yang di-ship sekarang adalah **Flutter web (PWA)** di `mobile/`, dijalankan
> di luar Docker (`flutter run -d chrome` / `flutter build web`).

# Fortunas AI — Docker Setup Guide

Panduan lengkap menjalankan Fortunas AI menggunakan Docker.
Tidak perlu install Python atau Ollama secara manual — semua berjalan di dalam container.

---

## Arsitektur Docker

```
┌─────────────────────────────────────────────────────┐
│              Flutter web (PWA), luar Docker          │
│              flutter run -d chrome                   │
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
   │ Qwen3:8b       │  │  BigQuery + Sheets    │
   │ port 11434     │  └──────────────────────-┘
   └────────────────┘

Volumes:
  ollama_data  → model weights (~4.8 GB)
  chroma_data  → vector embeddings
  reports_data → daily briefing JSON
```

> **Catatan port & CORS:** dengan service `frontend`/nginx dihapus,
> `docker-compose.yml` (production) sekarang mem-publish `8000:8000` langsung
> di service `backend` — stack ini murni API-only. `CORS_ORIGINS` di file itu
> berisi placeholder (`http://localhost`, `http://127.0.0.1`); sesuaikan
> dengan origin asli tempat PWA benar-benar disajikan (mis. port dev
> `flutter run -d chrome`). Di jalur deploy yang didukung
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
1. Download base images (python:3.11-slim, ollama/ollama) — ~1–2 GB
2. Install semua Python dependencies — ~5 menit
3. Start semua services

Log yang normal saat startup:
```
fortunas_ollama  | Ollama is running
fortunas_backend | [1/3] Waiting for Ollama...
fortunas_backend | ✓ Ollama is ready.
fortunas_backend | [2/3] First boot — running knowledge base ingest...
fortunas_backend | ✓ Knowledge base ingest complete.
fortunas_backend | [3/3] Starting FastAPI (uvicorn)...
fortunas_backend | INFO: Application startup complete.
```

---

### Step 4 — Pull Model Qwen3:8b (WAJIB, dilakukan sekali)

Buka terminal baru (biarkan docker compose tetap jalan):

```bash
make pull-model
```

Atau manual:
```bash
docker compose exec ollama ollama pull qwen3:8b
```

> Model berukuran **~4.8 GB**. Proses download mungkin membutuhkan 10–30 menit
> tergantung kecepatan internet. Setelah selesai, model tersimpan di volume
> `ollama_data` sehingga tidak perlu didownload ulang.

Verifikasi:
```bash
make model-list
# atau
docker compose exec ollama ollama list
```

---

### Step 5 — Buka Aplikasi

| URL | Keterangan |
|---|---|
| http://localhost:8000/docs | Swagger UI backend (hanya di dev mode) |
| http://localhost:11434 | Ollama API (hanya untuk debugging) |

Aplikasi Fortunas AI sendiri adalah PWA Flutter, dijalankan terpisah dari stack
Docker ini (`cd mobile && flutter run -d chrome`).

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
- Port `8000` sama-sama dibuka ke host di kedua mode (lihat catatan port & CORS di atas) — bisa akses Swagger di http://localhost:8000/docs, dan PWA (`flutter run -d chrome`) bisa connect ke `http://localhost:8000`

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

### "Ollama not ready after 30 attempts"
Backend startup timeout menunggu Ollama. Solusi:
```bash
# Pastikan Ollama container jalan
docker compose ps
docker compose logs ollama

# Restart jika perlu
docker compose restart ollama
docker compose restart backend
```

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
make pull-model           # pull model lagi (masih ada di volume ollama)
```

### Backend lambat saat pertama kali
Normal. Saat pertama boot, backend menjalankan ingest knowledge base + load model embeddings. Setelah itu restart berikutnya jauh lebih cepat karena ada marker file `.ingest_done`.

---

## Checklist Sebelum Commit Docker Files

```bash
# Pastikan tidak ada secrets dalam docker context
docker compose config     # tidak boleh ada nilai nyata dari .env ditampilkan

# File yang WAJIB ada sebelum docker compose up:
ls .env                                  # isi nilai nyata (jangan commit)
ls credentials/service-account.json     # (jangan commit)
ls .env.example                         # template (boleh commit)
ls .dockerignore                        # (wajib commit)
ls docker-compose.yml                   # (wajib commit)
```
