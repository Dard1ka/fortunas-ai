<div align="center">

<img src="frontend/public/logo-mark-256.png" alt="Fortunas AI" width="100"/>

# Fortunas AI

**Conversational Business Intelligence for Indonesian MSMEs — Multi-Tenant SaaS**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Flutter](https://img.shields.io/badge/Flutter-mobile-02569B?logo=flutter&logoColor=white)](https://flutter.dev)
[![BigQuery](https://img.shields.io/badge/BigQuery-Google_Cloud-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/bigquery)
[![Gemini](https://img.shields.io/badge/LLM-Gemini_2.5_Flash-8E75B2?logo=googlegemini&logoColor=white)](https://ai.google.dev)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-1.5-FF6B35)](https://trychroma.com)
[![Auth](https://img.shields.io/badge/Auth-JWT_multi--tenant-000000)](#-multi-tenant--auth)
[![Version](https://img.shields.io/badge/version-4.0.0-gold)](https://github.com/Dard1ka/fortunas-ai)

**Ask your sales data anything — in plain Bahasa Indonesia.**

[Multi-Tenant](#-multi-tenant--auth) · [Architecture](#-architecture) · [Quick Start](#-quick-start-local-dev) · [Deploy](#-deployment-vps) · [API](#-api-reference)

</div>

---

## 🔍 What is Fortunas AI?

Fortunas AI bridges the gap between raw transaction data and actionable business insight for Indonesian MSMEs (UMKM). Instead of dashboards or SQL, a business owner just **asks a question in natural Bahasa Indonesia** (typed or by voice) and gets a structured, data-backed answer in seconds.

> **"Siapa pelanggan paling setia bulan ini?"**
> → Fortunas AI maps the intent, queries that tenant's BigQuery tables, enriches with RAG, and Gemini writes a grounded report (summary + findings + recommendations) — e.g. *"Sari (18103), Budi (18105)..."*.

It is a **multi-tenant SaaS**: each business has its own isolated data, accessed via login. The backend is **deployed (FastAPI on a VPS)**; the final client is a **mobile app (Flutter)**, with a React web app for demos.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Multi-tenant + Auth** | Email/password (bcrypt) + JWT. Each business sees only its own data. |
| **Conversational Query** | Ask in natural Bahasa Indonesia → grounded insight (`/ask`) |
| **4 Auto-Analyses** | `repeat_customer` · `high_value_customer` · `peak_hour` · `bundle_opportunity` |
| **Daily Briefing** | On-demand per-tenant business summary (4 analyses + executive summary) |
| **🎤 Voice Input** | Speak transactions in Bahasa Indonesia → parsed → saved to that tenant's BigQuery |
| **Customer naming** | Auto-assign numeric Customer ID per name; shown as `Nama (id)` |
| **RAG Knowledge Base** | UMKM tips retrieved from ChromaDB to enrich recommendations |
| **Pluggable LLM** | `LLM_PROVIDER` = `gemini` (default) · `openai` · `ollama` (local, zero-cost) |
| **Mobile (Flutter)** | Final client — single codebase iOS + Android (auth WIP) |

---

## 🔐 Multi-Tenant & Auth

- `POST /auth/register` → creates a user (bcrypt) + tenant + JWT, and **provisions two BigQuery tables**: `{prefix}_transactions` and `{prefix}_customers`.
- `POST /auth/login` → returns a JWT. Every data endpoint requires `Authorization: Bearer <token>`.
- **Isolation is enforced at the data layer**, not the LLM: each request resolves its tenant (`get_current_tenant`) and only touches that tenant's tables. Gemini is stateless — it only ever sees one tenant's data per request, so one API key safely serves all tenants.
- Account metadata (users, tenants) lives in **SQLite** (`app/data/fortunas.db`); business data lives in **BigQuery** (shared project, per-tenant tables).

---

## 🏗 Architecture

```
   Mobile (Flutter) / React (demo)
            │  HTTP + Authorization: Bearer <JWT>
            ▼
        nginx :80  ──►  uvicorn :8000  (FastAPI)
            │
            ├─ Auth (JWT) ─► get_current_tenant ─► tenant's tables only
            ├─ Intent Mapper ─► BigQuery (named SQL on {prefix}_transactions)
            ├─ RAG (ChromaDB + MiniLM) ─► UMKM tips
            └─ LLM provider ─► Gemini 2.5 Flash ─► grounded insight (JSON)
            │
   ┌────────┴─────────┐
   │ BigQuery (cloud) │  per-tenant: {prefix}_transactions / {prefix}_customers
   │ SQLite           │  accounts & tenants (fortunas.db)
   └──────────────────┘
```

**Query flow:** NL question → intent → tenant's BigQuery SQL → enrich customer names → RAG → prompt (+ business profile) → Gemini → `{summary, top_findings, recommendation, rag_sources}`.

**Voice flow:** browser STT → `/voice/parse` (regex → LLM fallback) → review → `/voice/transaction` → validate → insert to tenant's BigQuery (invoice auto-increment, customer auto-assign).

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Mobile (final client) | Flutter + Dart (Riverpod, go_router, dio, speech_to_text) |
| Web (demo) | React 19 + Vite 8 |
| Backend | FastAPI (async), Python 3.11/3.12 |
| Auth | bcrypt + PyJWT (JWT), SQLite metadata |
| LLM | Gemini 2.5 Flash (default) · switchable to OpenAI / Ollama-Qwen via `app/llm_provider.py` |
| Data Warehouse | Google BigQuery — per-tenant tables |
| Vector DB / RAG | ChromaDB 1.5 + `paraphrase-multilingual-MiniLM-L12-v2` |
| Deploy | VPS (Ubuntu) · systemd · nginx · ufw |
| Demo Dataset | UCI Online Retail (Chen, 2015) |

---

## ⚡ Quick Start (Local Dev)

> Credentials & full step-by-step (incl. VPS access) are in `HANDOVER.txt` (gitignored, internal). Project context: [`memory.md`](memory.md).

**Prerequisites:** Python 3.11/3.12, Node 20+, a GCP service-account JSON (BigQuery), a Gemini API key.

```bash
git clone https://github.com/Dard1ka/fortunas-ai.git
cd fortunas-ai

# Backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
# (Linux/Mac: source .venv/bin/activate && pip install -r requirements.txt)

# Credentials + .env
mkdir credentials   # put fortunas-service-account.json here
cp deploy/.env.production.example .env   # then edit: GEMINI_API_KEY, JWT_SECRET, BIGQUERY_*

# (optional) build RAG index
.venv/Scripts/python -m app.knowledge.ingest

# Run backend
.venv/Scripts/python -m uvicorn app.main:app --port 8000

# Run web demo (separate terminal)
cd frontend && npm install && npm run dev      # http://localhost:3000
```

Then open `http://localhost:3000` → **Register** a business or **Login**. To point the web demo at a deployed backend instead of localhost:
```bash
# in frontend/
VITE_API_TARGET=http://<vps-ip> npm run dev      # PowerShell: $env:VITE_API_TARGET="http://<vps-ip>"; npm run dev
```

Minimal `.env`:
```
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
JWT_SECRET=...            # openssl rand -hex 32
GOOGLE_APPLICATION_CREDENTIALS=./credentials/fortunas-service-account.json
BIGQUERY_PROJECT_ID=fortunasai
BIGQUERY_DATASET=fortunas_ai
VOICE_DRY_RUN=false
BRIEFING_SCHEDULER_ENABLED=false
```

---

## 🚀 Deployment (VPS)

The backend is deployed on a VPS (Ubuntu + systemd + nginx). Full guide: **[`deploy/DEPLOY.md`](deploy/DEPLOY.md)** (artifacts in `deploy/`: systemd unit, nginx conf, `.env.production.example`).

Update a running deployment:
```bash
cd /opt/fortunas-ai && git pull && sudo systemctl restart fortunas-backend
```
HTTPS (when a domain is available): certbot — see DEPLOY.md §9.

> Docker files (`docker/`, `docker-compose*.yml`) remain in the repo but predate multi-tenant/auth — the supported path is now the VPS guide above.

---

## 📡 API Reference

Interactive docs: **`/docs`**. All data endpoints require `Authorization: Bearer <JWT>`.

| Method | Endpoint | Auth | Description |
|---|---|:--:|---|
| `POST` | `/auth/register` | — | Create business + user, provision BQ tables, return JWT |
| `POST` | `/auth/login` | — | Login → JWT |
| `GET` | `/auth/me` | ✅ | Current account/tenant info |
| `POST` | `/ask` | ✅ | NL question → grounded insight |
| `GET` | `/briefing` | ✅ | Run 4 analyses + executive summary |
| `POST` | `/report/daily/run` | ✅ | Run + save daily briefing (per-tenant) |
| `GET` | `/report/daily` | ✅ | Latest saved briefing + history |
| `POST` | `/voice/parse` | ✅ | Voice transcript → structured preview |
| `POST` | `/voice/transaction` | ✅ | Confirm → save to tenant's BigQuery |
| `POST` | `/upload/excel` | ✅ | Bulk CSV/Excel → tenant's BigQuery |
| `GET` | `/health` · `/rag/health` · `/llm/health` | — | Health checks |

```bash
# login then ask
TOKEN=$(curl -s -X POST .../auth/login -H 'Content-Type: application/json' \
  -d '{"email":"demo@fortunas.test","password":"demo12345"}' | jq -r .access_token)
curl -X POST .../ask -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"question":"siapa pelanggan paling bernilai"}'
```

---

## 📁 Project Structure

```
fortunas-ai/
├── app/
│   ├── api/routes/          # auth, ask, briefing, voice, upload, report, health
│   ├── core/                # config, deps, scheduler, auth (JWT/bcrypt), tenancy
│   ├── db.py                # SQLite: users & tenants
│   ├── agents/              # sql_agent, rag_agent, insight_agent
│   ├── services/            # pipeline, wa_pipeline_structured, tenant_provisioning, excel_upload
│   ├── llm_provider.py      # gemini / openai / ollama switch
│   ├── llm_service.py, prompt_builder.py
│   ├── queries.py           # per-tenant SQL builders
│   ├── intent_mapper.py, analysis_registry.py, bigquery_service.py, schemas.py
│   ├── knowledge/           # ingest.py + umkm_docs/ (RAG corpus)
│   └── main.py
├── frontend/                # React web demo (login, ask, briefing, voice, history, profile)
├── mobile/                  # Flutter app (final client; auth WIP)
├── deploy/                  # DEPLOY.md, systemd unit, nginx conf, .env.production.example
├── scripts/                 # BQ maintenance utilities
├── memory.md                # project context (credential-free)
└── requirements.txt
```

---

## 🔒 Data Privacy & Isolation

- **Tenant isolation** at the data layer: each request only accesses its own tenant's BigQuery tables.
- **LLM trade-off:** with `LLM_PROVIDER=gemini` (default), prompts are sent to Google (cloud) — fast, high quality. For strict "data never leaves" requirements, set `LLM_PROVIDER=ollama` to run a local Qwen model (zero token cost, fully on-prem).
- `.env`, `credentials/`, `*.db`, `chroma_db/`, `HANDOVER.txt` are git-ignored — never commit secrets.

---

## 🗺 Roadmap

- [x] v1–v2 — RAG pipeline, BigQuery, Docker, React PWA + voice
- [x] v3.0.0 — Flutter mobile app
- [x] **v4.0.0 — Multi-tenant SaaS** (JWT auth, per-tenant tables, Gemini provider) + **VPS deploy**
- [ ] Mobile app auth (login → JWT) — connect Flutter to the deployed API
- [ ] HTTPS (domain + certbot) before mobile release
- [ ] WhatsApp Business Cloud API (infra ready; blocked by Meta region restriction)
- [ ] `demand_forecast` / `inventory_alert` analysis modules

---

## 📋 Changelog (recent)

### v4.0.0 — Multi-Tenant SaaS + Deploy
- Auth: register/login (bcrypt + JWT), `get_current_tenant` dependency; SQLite account store (`app/db.py`)
- Per-tenant BigQuery tables (`{prefix}_transactions/_customers`) + provisioning on register
- All flows tenant-scoped (`/ask`, `/voice`, `/briefing`, `/upload`, `/report`); Google Sheets removed from the data path
- LLM provider layer (`gemini`/`openai`/`ollama`); Gemini default; insight uses LLM output (grounded) + RAG; customer shown as `Nama (id)`
- React: login/register screen + token handling; `deploy/` kit (systemd, nginx, guide); **deployed to VPS**

### v3.0.0 — Flutter mobile app + voice multi-item
### v2.x — Docker, React PWA, voice flow, RAG, BigQuery (see git history)

---

## 👥 Team

| Name | NIM |
|---|---|
| Gregorius Darrel Andika Setya | 2702299882 |
| Filo Alvian Ongky | 2702375613 |
| Go Steven Sanjaya | 2702397225 |
| Michael Ivan Santoso | 2702300120 |

**Computer Science — Binus University · MIS Student Grant 2026**

## 📄 License
[MIT](LICENSE) © 2026 Fortunas AI Team

## 📚 References
- Lewis, P. et al. (2020). *Retrieval-Augmented Generation*. [arXiv:2005.11401](https://arxiv.org/abs/2005.11401)
- Reimers, N. & Gurevych, I. (2019). *Sentence-BERT*. [arXiv:1908.10084](https://arxiv.org/abs/1908.10084)
- Chen, D. (2015). *UCI Online Retail Dataset*. [DOI:10.24432/C5BW33](http://archive.ics.uci.edu/dataset/352/online+retail)
