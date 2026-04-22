<div align="center">

<img src="frontend/public/logo-mark-256.png" alt="Fortunas AI" width="100"/>

# Fortunas AI

**Conversational Business Intelligence for Indonesian MSMEs**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![BigQuery](https://img.shields.io/badge/BigQuery-Google_Cloud-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/bigquery)
[![Ollama](https://img.shields.io/badge/Ollama-Qwen3%3A8b-black?logo=ollama&logoColor=white)](https://ollama.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-1.5-FF6B35)](https://trychroma.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Ask your sales data anything — in plain Bahasa Indonesia.**

[Demo Features](#-demo) · [Quick Start](#-quick-start) · [Architecture](#-architecture) · [API Docs](#-api-reference)

</div>

---

## 🔍 What is Fortunas AI?

Fortunas AI bridges the gap between raw transaction data and actionable business insight for Indonesian MSMEs (Usaha Mikro, Kecil, dan Menengah). Instead of navigating complex BI dashboards or writing SQL queries, business owners simply **type a question in natural language** — and get a detailed, data-backed answer in seconds.

> **"Pelanggan mana yang paling sering beli bulan ini?"**
> → Fortunas AI queries BigQuery, retrieves context from ChromaDB, generates a structured insight report with findings and recommendations via a local LLM — all in under 5 seconds.

### 💬 WhatsApp-Style Simulator
The frontend includes a **WhatsApp-like chat simulator** that replicates the familiar messaging UX Indonesian UMKM owners already use daily. This allows frictionless adoption without requiring any WhatsApp Business API integration during the MVP phase. Full WhatsApp Business Cloud API integration is scoped as a planned enhancement.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Conversational Query** | Ask business questions in natural Bahasa Indonesia |
| **4 Auto-Analyses** | `repeat_customer` · `high_value_customer` · `peak_hour` · `bundle_opportunity` |
| **Daily Briefing** | Automated morning business summary (APScheduler cron) |
| **WA Chat Simulator** | WhatsApp-style chat interface built in React |
| **Transaction Ingestion** | Input via chat → validated → Google Sheets staging → BigQuery |
| **RAG Knowledge Base** | UMKM business context retrieved from ChromaDB per query |
| **Local LLM** | Qwen3:8b via Ollama — zero token cost, full data privacy |
| **Dual-Layer Staging** | Google Sheets audit trail + BigQuery analytics warehouse |
| **Auto-Retry Pipeline** | APScheduler retries `failed`/`pending` rows automatically |
| **Interactive Dashboard** | KPI cards: daily revenue, top customer, top product, peak hour |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User (Browser)                        │
│         React 19 + Vite  —  WA Chat Simulator           │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / REST
┌────────────────────────▼────────────────────────────────┐
│               FastAPI Backend (Python 3.11)              │
│                                                          │
│  /wa/simulate   /ask   /briefing   /ingest   /report     │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Intent      │  │ RAG Agent    │  │ Insight Agent  │  │
│  │ Mapper      │  │ (ChromaDB +  │  │ (Ollama LLM)   │  │
│  │             │  │  Embeddings) │  │                │  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬────────┘  │
│         │                │                  │            │
│  ┌──────▼────────────────▼──────────────────▼────────┐  │
│  │              SQL Agent (BigQuery)                  │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────┬───────────────────┬─────────────────────-─┘
               │                   │
   ┌───────────▼───┐     ┌─────────▼─────────┐
   │ Google Sheets │     │   Google BigQuery   │
   │ (Audit Trail  │────▶│  (Analytics DWH)    │
   │  + Staging)   │     │  online_retail tbl  │
   └───────────────┘     └─────────────────────┘
          ▲
          │ Auto-Retry (APScheduler)
          │ failed/pending rows
```

**Data Flow — Transaction Input:**
```
Chat Input → Pydantic Validation → Google Sheets (staging)
    → BigQuery INSERT → bq_status updated in Sheet
    → Embedding → ChromaDB (vector index for RAG)
```

**Data Flow — Query:**
```
Natural Language Question → Intent Classification
    → ChromaDB top-K retrieval → BigQuery SQL execution
    → Prompt assembly → Qwen3:8b (Ollama) → Structured answer
```

---

## 🛠 Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | React + Vite | 19 / 8 |
| Backend | FastAPI (async) | 0.135 |
| Validation | Pydantic | 2.x |
| Staging | Google Sheets (`gspread`) | 6.x |
| Data Warehouse | Google BigQuery | — |
| Scheduler | APScheduler | 3.x |
| Vector DB | ChromaDB | 1.5 |
| Embedding | `paraphrase-multilingual-MiniLM-L12-v2` | sentence-transformers 4.x |
| LLM | Qwen3:8b via Ollama | — |
| Demo Dataset | UCI Online Retail (Chen, 2015) | 1M+ rows |

---

## ⚡ Quick Start

### Prerequisites

| Requirement | Version | Check |
|---|---|---|
| Python | 3.11 or 3.12 | `python --version` |
| Node.js | 20+ | `node --version` |
| Ollama | latest | `ollama --version` |
| Google Cloud account | BigQuery enabled | service account JSON |

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/fortunas-ai.git
cd fortunas-ai

# Backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env — fill in your Google Cloud credentials and paths
```

See [`.env.example`](.env.example) for all required variables.

### 3. Pull LLM Model

```bash
ollama pull qwen3:8b
ollama serve          # keep this running in a separate terminal
```

### 4. Ingest Knowledge Base (once)

```bash
python -m app.knowledge.ingest
```

This builds `chroma_db/` with UMKM domain knowledge embeddings.

### 5. Start Servers

```bash
# Terminal 1 — Backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Open **http://localhost:3000** 🎉

For detailed setup, see [SETUP.md](SETUP.md).

---

## 🎬 Demo

### WA Chat Simulator — Transaction Input
```
You:  Invoice INV-2024, sabun cuci, qty 10, harga 8500, negara Indonesia
Bot:  ✅ Transaksi INV-2024 berhasil dicatat.
      Tersimpan di Google Sheets (audit) + BigQuery (analytics).
```

### WA Chat Simulator — Business Query
```
You:  Pelanggan mana yang paling sering beli?
Bot:  📊 Analisis Repeat Customer

      Temuan:
      1. Customer C12345 melakukan 47 transaksi (tertinggi)
      2. Rata-rata frekuensi top-10 customer: 28 transaksi/bulan
      3. 85% repeat customer berasal dari region United Kingdom

      Rekomendasi:
      • Buat program loyalitas untuk C12345 dan 9 customer teratas
      • Fokus retensi di region UK yang dominan
      • Tawarkan early access produk baru ke repeat customers
```

### Available Queries
```
"Siapa customer dengan belanja tertinggi?"     → high_value_customer
"Kapan waktu paling ramai transaksi?"          → peak_hour
"Produk apa yang sering dibeli bersama?"       → bundle_opportunity
"Siapa customer yang paling sering beli?"      → repeat_customer
```

Try the **Briefing Bisnis** tab for a fully automated, no-prompt daily business summary.

---

## 📡 API Reference

Interactive docs: **http://localhost:8000/docs**

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/wa/simulate` | WA simulator — input transaction or question |
| `POST` | `/ask` | Direct analytics query |
| `POST` | `/briefing` | Generate full daily briefing |
| `GET` | `/report/latest` | Get latest saved report |
| `POST` | `/ingest` | Ingest transaction records |
| `POST` | `/upload` | Bulk upload CSV |

### Example: WA Simulator

```bash
curl -X POST http://localhost:8000/wa/simulate \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "body=Siapa+customer+paling+sering+beli&sender=user_demo"
```

---

## 📁 Project Structure

```
fortunas-ai/
├── app/
│   ├── agents/              # sql_agent, rag_agent, insight_agent
│   ├── api/routes/          # ask, briefing, health, ingest, report, whatsapp
│   ├── core/                # config, deps, scheduler
│   ├── knowledge/           # ingest.py + umkm_docs/ (RAG corpus)
│   ├── services/            # pipeline, sheets_service, wa_pipeline
│   ├── analysis_registry.py # intent → analysis mapping
│   ├── bigquery_service.py
│   ├── intent_mapper.py     # NL intent classification
│   ├── llm_service.py       # Ollama wrapper
│   ├── prompt_builder.py    # RAG prompt assembly
│   ├── queries.py           # BigQuery SQL templates
│   ├── schemas.py           # Pydantic models
│   └── main.py              # FastAPI app factory
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── App.css          # Component styles
│   │   └── index.css        # Global theme (dark + gold)
│   ├── public/
│   │   ├── logo.svg         # Fortunas AI wordmark
│   │   └── favicon.svg
│   └── package.json
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── SETUP.md                 # Detailed setup guide
├── DEMO_SCRIPT.md           # Demo scenarios
└── README.md                # This file
```

---

## 🔒 Data Privacy

- **LLM runs locally** via Ollama — transaction data never leaves your server
- **`.env` and `credentials/`** are git-ignored — never commit credentials
- Google Sheets staging provides a human-readable audit trail
- Compliant with Indonesian UU PDP No. 27/2022 architecture principles

---

## 🗺 Roadmap

- [ ] **WhatsApp Business Cloud API** — real channel integration (blocked by Meta region restriction in MVP; infrastructure ready)
- [ ] Fine-tune embedding model on Indonesian retail corpus
- [ ] Add `demand_forecast` and `inventory_alert` intent modules
- [ ] Alternative credit scoring module based on transaction history
- [ ] Multi-tenant support for SaaS deployment

---

## 👥 Team

| Name | Role | NIM |
|---|---|---|
| Gregorius Darrel Andika Setya | Backend API · Frontend · Pipeline | 2702299882 |
| Filo Alvian Ongky | — | 2702375613 |
| Go Steven Sanjaya | — | 2702397225 |
| Michael Ivan Santoso | — | 2702300120 |

**Computer Science — Binus University · MIS Student Grant 2026**

---

## 📄 License

[MIT](LICENSE) © 2026 Fortunas AI Team

---

## 📚 References

- Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS. [arXiv:2005.11401](https://arxiv.org/abs/2005.11401)
- Reimers, N. & Gurevych, I. (2019). *Sentence-BERT*. [arXiv:1908.10084](https://arxiv.org/abs/1908.10084)
- Chen, D. (2015). *UCI Online Retail Dataset*. [DOI:10.24432/C5BW33](http://archive.ics.uci.edu/dataset/352/online+retail)
