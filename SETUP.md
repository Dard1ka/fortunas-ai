# Fortunas AI — Panduan Setup

Panduan lengkap untuk menyiapkan Fortunas di mesin baru. Ikuti urut dari atas ke bawah.

## Quick Start (5 Menit)

Untuk yang sudah punya Python 3.11/3.12, Node 20+, dan Ollama jalan:

```bash
# Terminal 1 — Backend
cd Fortunas
python -m venv .venv
.venv\Scripts\activate              # Windows PowerShell; Git Bash pakai: source .venv/Scripts/activate
pip install --upgrade pip
pip install -r requirements.txt
# Buat file .env — lihat template di section 3.4
python -m app.knowledge.ingest      # sekali saja, generate chroma_db/
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend (shell baru, paralel)
cd Fortunas/frontend
npm install
npm run dev

# Terminal 3 — Ollama (kalau belum nyala)
ollama serve
```

Buka `http://localhost:3000`. Kalau backend respons di `http://127.0.0.1:8000/health`, setup sukses.

Urutan penting: Ollama → ingest (sekali) → uvicorn → npm run dev.

## 1. Prasyarat

| Kebutuhan | Versi | Cek |
|-----------|-------|-----|
| Python | 3.11 atau 3.12 | `python --version` |
| Node.js | 20 atau 22 | `node --version` |
| npm | 10+ | `npm --version` |
| Ollama | terbaru | `ollama --version` |
| Akun Google Cloud | BigQuery aktif | service account JSON tersedia |

Download link:
- Python: https://www.python.org/downloads/
- Node.js: https://nodejs.org/
- Ollama: https://ollama.com/download

Setelah Ollama terinstal, pull model yang dipakai aplikasi:

```bash
ollama pull qwen3:8b
ollama serve
```

## 2. Struktur Folder

```
Fortunas/
├── app/                  # Backend FastAPI + agents
│   ├── agents/           # sql_agent, insight_agent, rag_agent
│   ├── api/routes/       # ask, briefing, report, ingest, health
│   ├── core/             # config, deps, scheduler
│   ├── services/         # pipeline, report_store
│   ├── knowledge/        # umkm_docs untuk RAG
│   └── main.py           # entrypoint FastAPI
├── frontend/             # React + Vite
│   ├── src/
│   └── package.json
├── requirements.txt      # Python deps
├── .env                  # Config lokal (JANGAN di-commit / di-zip)
└── SETUP.md              # File ini
```

## 3. Setup Backend

### 3.1 Buat Virtual Environment

**Penting:** selalu buat venv baru di mesin masing-masing. Jangan ikut-sertakan folder `.venv/` saat mengirim kode ke tim — isinya absolute path ke interpreter mesin pembuat, tidak portable.

Dari folder `Fortunas/`:

```bash
python -m venv .venv
```

### 3.2 Aktifkan Virtual Environment

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Git Bash / WSL):**
```bash
source .venv/Scripts/activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

Setelah aktif, prompt akan berubah jadi `(.venv) ...`.

### 3.3 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Proses ini memerlukan koneksi internet stabil. Install `sentence-transformers` otomatis menarik PyTorch (~700 MB–2 GB), sediakan ruang disk minimal 4 GB.

### 3.4 Konfigurasi File `.env`

Buat file `.env` di root `Fortunas/` dengan isi berikut. Ganti nilai sesuai mesin Anda:

```dotenv
# ── Google BigQuery ────────────────────────────
# Path absolut ke service account JSON Anda sendiri
GOOGLE_APPLICATION_CREDENTIALS=C:/path/ke/service-account.json
BIGQUERY_PROJECT_ID=fortunasai
BIGQUERY_DATASET=fortunas_ai
BIGQUERY_TABLE=online_retail

# ── Ollama (Local LLM) ─────────────────────────
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:8b

# ── RAG (Chroma + sentence-transformers) ───────
CHROMA_DB_PATH=./chroma_db
RAG_COLLECTION_NAME=umkm_knowledge
RAG_EMBED_MODEL=paraphrase-multilingual-MiniLM-L12-v2
RAG_DEFAULT_N_RESULTS=4

# ── Daily Briefing Scheduler ───────────────────
BRIEFING_CRON_HOUR=6
BRIEFING_CRON_MINUTE=0
BRIEFING_TIMEZONE=Asia/Jakarta
BRIEFING_SCHEDULER_ENABLED=true

# ── Report Storage ─────────────────────────────
DAILY_REPORT_PATH=./app/data/daily_reports.json
DAILY_REPORT_HISTORY_DAYS=7

# ── Knowledge Base ─────────────────────────────
KNOWLEDGE_DOCS_DIR=./app/knowledge/umkm_docs
```

Catatan:
- `GOOGLE_APPLICATION_CREDENTIALS` harus path absolut ke file JSON service account BigQuery milik Anda. Minta akses proyek GCP ke pemilik.
- Di Windows, gunakan `/` atau `\\` sebagai separator path.
- `.env` **tidak boleh** di-commit ke git atau di-zip ke tim.

### 3.5 Ingest Knowledge Base (satu kali)

Dokumen UMKM di `app/knowledge/umkm_docs/` harus di-ingest ke Chroma sekali saat setup:

```bash
python -m app.knowledge.ingest
```

Ini membuat folder `chroma_db/` di root. Jalankan ulang kalau menambah/mengubah dokumen di `umkm_docs/`.

### 3.6 Jalankan Backend

```bash
uvicorn app.main:app --reload --port 8000
```

Akses dokumentasi interaktif di `http://127.0.0.1:8000/docs`.

Verifikasi cepat:
```bash
curl http://127.0.0.1:8000/health
```

## 4. Setup Frontend

Dari folder `frontend/`:

```bash
cd frontend
npm install
npm run dev
```

Buka `http://localhost:3000`. Vite otomatis proxy request `/api/*` ke backend di port 8000 — pastikan backend sudah jalan.

Build produksi:
```bash
npm run build
```

Hasil di `frontend/dist/`.

## 5. Verifikasi End-to-End

Urut saat pertama kali setup:

1. Ollama nyala: `ollama list` menampilkan `qwen3:8b`.
2. Backend nyala: `GET http://127.0.0.1:8000/health` balas `200`.
3. Frontend nyala: `http://localhost:3000` tampil halaman Fortunas.
4. Mode **Tanya**: ajukan "Siapa customer yang paling sering beli?" — dapat respons lengkap dengan temuan + rekomendasi.
5. Mode **Briefing Bisnis**: klik "Mulai Briefing" — 4 section selesai satu per satu + executive summary.
6. Mode **Harian**: klik "Jalankan hari ini" — briefing tersimpan, muncul di riwayat setelah refresh.

## 6. Troubleshooting

### "No Python at 'C:\\Users\\XXX\\...\\Python311\\python.exe'"
Venv dibuat di mesin lain dan path interpreter-nya hardcoded di `pyvenv.cfg`. Fix: hapus folder `.venv/`, buat ulang dari langkah 3.1.

### "ModuleNotFoundError: No module named 'chromadb'" (atau modul lain)
Dependency baru ditambahkan tapi `requirements.txt` belum diperbarui. Jalankan:
```bash
pip install -r requirements.txt
```
Kalau tetap error, install manual dan minta yang menambahkan import untuk `pip freeze > requirements.txt` dan commit ulang.

### RAG error `ValueError: Unrecognized processing class` atau `rag_enabled: false`
Library `sentence-transformers` v5.x tidak kompatibel dengan format model `paraphrase-multilingual-MiniLM-L12-v2`. Pastikan `requirements.txt` mem-pin versi 4.x:
```
sentence-transformers==4.1.0
transformers==4.57.6
```
Kalau sudah ter-install versi lain, downgrade:
```bash
pip install "sentence-transformers>=4.0,<5.0"
```
Lalu jalankan `python -m app.knowledge.ingest` dari root `Fortunas/` dan restart uvicorn.

### `rag_enabled: false` dengan error `Collection [umkm_knowledge] does not exist`
Uvicorn dijalankan dari folder yang salah, sehingga `./chroma_db` resolve ke lokasi kosong. Pastikan `uvicorn` dijalankan dari dalam folder `Fortunas/` (bukan parent). Atau set `CHROMA_DB_PATH` di `.env` ke absolute path.

### "GOOGLE_APPLICATION_CREDENTIALS belum di-set di file .env"
Buka `.env`, pastikan baris `GOOGLE_APPLICATION_CREDENTIALS=` berisi path absolut yang benar ke file JSON service account Anda.

### "Connection refused" saat panggil Ollama
Ollama belum nyala. Jalankan `ollama serve` di terminal terpisah.

### Port 3000 / 8000 sudah dipakai
Cari proses yang pakai:
```bash
# Windows
netstat -ano | findstr :8000

# macOS / Linux
lsof -i :8000
```
Matikan proses atau ubah port (`--port 8001` untuk backend, `--port 3001` untuk frontend via `vite.config.js`).

### Frontend build gagal di `npm run build`
Hapus `node_modules/` dan `package-lock.json`, lalu `npm install` ulang.

### Briefing scheduler nyala tapi tidak eksekusi
Cek `.env`:
- `BRIEFING_SCHEDULER_ENABLED=true`
- `BRIEFING_TIMEZONE` sesuai zona waktu mesin (default `Asia/Jakarta`)

Log scheduler muncul di terminal uvicorn saat jam `BRIEFING_CRON_HOUR:BRIEFING_CRON_MINUTE`.

## 7. Checklist Handoff Antar Anggota Tim

Sebelum zip atau commit ke repo bersama, pastikan:

- [ ] **Tidak ada** folder `.venv/` dalam zip / commit
- [ ] **Tidak ada** folder `node_modules/` dalam zip / commit
- [ ] **Tidak ada** folder `chroma_db/` dalam zip / commit (dibuat saat ingest lokal)
- [ ] **Tidak ada** file `.env` dalam zip / commit (template saja di SETUP.md)
- [ ] **Tidak ada** file service account JSON dalam zip / commit
- [ ] `requirements.txt` sudah di-update kalau ada tambahan `import` library baru — jalankan `pip freeze > requirements.txt` sebelum zip
- [ ] `package.json` + `package-lock.json` ter-commit (keduanya, untuk reproducible install)
- [ ] Dokumen baru di `app/knowledge/umkm_docs/` ter-commit (dipakai untuk ingest)

## 8. Pembagian Peran

| Agent | Peran | File Utama | Pemilik |
|-------|-------|-----------|---------|
| Agent 1 | Backend API, intent mapping, pipeline orchestration | `app/api/routes/`, `app/services/pipeline.py`, `app/intent_mapper.py`, `app/core/` | Steven |
| Agent 2 | SQL Agent — mapping pertanyaan ke query BigQuery, guard SQL injection | `app/agents/sql_agent.py`, `app/queries.py`, `app/sql_guards.py`, `app/bigquery_service.py` | Teammate |
| Agent 3 | RAG Agent — retrieval dokumen UMKM via Chroma + embedding model | `app/agents/rag_agent.py`, `app/knowledge/ingest.py`, `app/knowledge/umkm_docs/*.md` | Teammate |
| Agent 4 | Insight Agent — generate summary/findings/recommendation via Ollama LLM | `app/agents/insight_agent.py`, `app/llm_service.py`, `app/prompt_builder.py` | Teammate |
| Agent 5 | Frontend (React + Vite) | `frontend/src/App.jsx`, `frontend/src/App.css`, `frontend/src/index.css` | Steven |

Setiap perubahan di file agent pemilik masing-masing. Untuk kontrak data antar agent, koordinasi via `app/schemas.py`.

## 9. Stack Frontend

- **Display**: `Cormorant Garamond` — judul, exec summary, ringkasan besar
- **Body**: `Outfit` — seluruh UI teks
- Palette dark + gold accent, glass-surface rounded cards

File: [src/index.css](frontend/src/index.css) untuk variabel global & tema, [src/App.css](frontend/src/App.css) untuk komponen. Font di-load dari Google Fonts via [index.html](frontend/index.html).
