# Fortunas AI — Project Memory / Context

> Konteks proyek untuk developer & AI assistant yang melanjutkan. **Bebas credential**
> (aman di repo publik). Credential & langkah setup detail ada di `HANDOVER.txt` (gitignored, internal).
> Update terakhir: 2026-06-20.

## Apa Ini
Backend analitik UMKM Indonesia: pemilik usaha bertanya pakai Bahasa Indonesia (teks/suara),
dijawab AI dari data transaksi mereka sendiri. **Multi-tenant SaaS** + sudah **deploy ke VPS**.
Produk akhir = **web app + PWA (React 19 + Vite, di-build dari `frontend/` via `npm run build`)**.

> **Status klien (2026-08-08, ADR-0002 — Gate D dieksekusi):** React (`frontend/`) =
> satu-satunya klien — dibangun, dites, di-gate CI (`Frontend (lint + test + build)`),
> live di `app.fortunas.id`. Flutter `mobile/` sudah DIHAPUS setelah paritas penuh
> (Wave C, PR #35). Lihat `docs/adr/0002-react-production-client.md`.

## Stack
- FastAPI (Python 3.11/3.12), uvicorn
- BigQuery — data per-tenant (tabel ber-prefix dalam 1 dataset)
- LLM: **Gemini 2.5 Flash** via lapisan provider (`LLM_PROVIDER` = gemini | openai | ollama)
- RAG: ChromaDB + embedding MiniLM (tips UMKM umum, ~56 dok) — global, dipakai semua tenant
- Auth: email+password (bcrypt) + JWT; metadata akun/tenant di SQLite (`app/data/fortunas.db`)

## Arsitektur (alur data)
```
Client (React web/PWA — frontend/) --Bearer JWT--> nginx :80 --> uvicorn :8000 (FastAPI)
  get_current_tenant (JWT) → tahu tenant → akses HANYA tabel {prefix}_transactions/_customers
  → Gemini menyusun insight (grounded ke data) + RAG → JSON {summary, top_findings, recommendation, rag_sources}
```
- **Isolasi antar bisnis = di lapisan DATA backend**, bukan di LLM. Gemini stateless: cuma tahu
  isi prompt per-request. 1 API key aman untuk banyak tenant.
- **Register** → buat user+tenant+JWT, lalu provision 2 tabel BQ (`{prefix}_transactions`, `{prefix}_customers`).
- Customer ID auto-assign + reuse per tenant; ditampilkan format **`Nama (id)`**.

## Konvensi / Perilaku Penting
- Insight (`/ask`, `/briefing`) **pakai output LLM** (Gemini), grounded ke `rows[0..]` lewat aturan prompt;
  template deterministik dari data = fallback bila LLM kosong (`_repair_output` di `app/llm_service.py`).
- Invoice voice **auto-increment** (user tak perlu sebut). Sheets **sudah dihapus** dari jalur multi-tenant (langsung BQ).
- Scheduler briefing OFF (`BRIEFING_SCHEDULER_ENABLED=false`); briefing per-tenant via `POST /report/daily/run`.
- 11 intent analitik (hardcoded, lihat `app/analysis_registry.py`): repeat_customer, high_value_customer,
  peak_hour, bundle_opportunity, top_product, revenue_trend, customer_segmentation, churn_risk,
  slow_moving_product, average_basket_size, demand_forecast.
  Nambah analisis → ubah `intent_mapper.py` + `queries.py` + `analysis_registry.py`.

## Endpoint Inti (lihat `/docs`)
`POST /auth/register`, `POST /auth/login`, `GET /auth/me` · `POST /ask` · `GET /briefing`,
`POST /report/daily/run`, `GET /report/daily` · `POST /voice/parse`, `POST /voice/transaction` ·
`POST /upload/excel` · `GET /health`, `/rag/health`, `/llm/health`

## Peta File
- `app/db.py` — SQLite users/tenants
- `app/core/auth.py` — bcrypt + JWT
- `app/core/tenancy.py` — `TenantContext`, `get_current_tenant`
- `app/api/routes/auth.py` — register/login/me
- `app/services/tenant_provisioning.py` — buat tabel BQ per tenant
- `app/queries.py` — builder SQL named-analysis (terima tabel tenant)
- `app/services/pipeline.py` — orkestrasi /ask & /briefing
- `app/services/wa_pipeline_structured.py` — voice → BQ, customer resolve
- `app/llm_provider.py` — switch LLM gemini/openai/ollama
- `app/llm_service.py`, `app/prompt_builder.py` — insight + prompt
- `app/agents/rag_agent.py`, `app/knowledge/ingest.py` — RAG
- `frontend/src/` — React 19 + Vite (klien produksi, PWA)
- `deploy/` — DEPLOY.md, systemd unit, nginx conf, .env contoh
- `scripts/` — util maintenance BQ

## Cara Jalan (ringkas — detail di HANDOVER.txt / deploy/DEPLOY.md)
- **Lokal**: venv + `pip install -r requirements.txt`; isi `.env`; jalankan
  `uvicorn app.main:app --port 8000`; `cd frontend && npm ci && npm run dev`.
  Client → backend lain: set `VITE_API_TARGET=http://<host>:8000` (proxy dev server-side).
- **VPS (sudah live)**: kode di `/opt/fortunas-ai`; update = `git pull && sudo systemctl restart fortunas-backend`.

## Gotchas
- SQLite akun **terpisah** per backend (lokal vs VPS). JWT lokal tak valid di VPS (JWT_SECRET beda) → auto-logout.
- BigQuery = cloud BERSAMA (tabel tenant sama dari lokal/VPS). Streaming insert tak bisa di-UPDATE/DELETE ~90 menit.
- `.env`, `credentials/`, `*.db`, `chroma_db/`, `HANDOVER.txt` = gitignored. Jangan commit secret.

## TODO Berikutnya
- [ ] Paritas React skop-hibah: Checkout + DPA (Wave A), customer OTP/QR/scan (Wave B) — lihat ADR-0002.
- [ ] HTTPS (domain + certbot) sebelum rilis PWA React — blocker utama.
- [ ] Rotate API key Gemini; jadikan repo private.
- [ ] (opsional) rapikan format "Rp x,0"; bersihkan endpoint WA/Sheets legacy.
