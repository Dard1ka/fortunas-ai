> ⚠️ **OUTDATED (pre-v4.0).** This file predates the multi-tenant SaaS rewrite
> (auth/JWT, per-tenant BigQuery tables, Gemini LLM, VPS deploy). For current
> context use [`memory.md`](memory.md) and [`README.md`](README.md); for setup
> see README Quick Start and [`deploy/DEPLOY.md`](deploy/DEPLOY.md). Kept for history.
>
> Also outdated as of Task 1b: `mobile/android/` and `mobile/ios/` (referenced
> below as still present) have been removed from the repo. The single shipped
> client is Flutter web (PWA), built from `mobile/` via `flutter build web`.
> `frontend/` (React) is retained in the repo as an archive / design
> reference (Task 1e reverted that part of Task 1b) — not built, not tested,
> not CI-gated, and not the shipped client.

# AI_CONTEXT.md — Fortunas AI

> **Audience:** Any AI assistant (Claude, GPT, Gemini, Llama, etc.) reading this codebase for the first time. This file is the single source of truth — no other reading required to start being productive.
>
> **Last updated:** 2026-05-19 (v2.2 — Flutter migration in progress)
>
> **Active frontend:** `mobile/` (Flutter), built to web only. The `frontend/` React PWA — described below as "retained as legacy reference" — is still retained, now explicitly as an archive / design reference (Task 1e, after a brief deletion in Task 1b); see `mobile/MIGRATION.md` for the original React → Flutter rationale.

---

## 1. What this project is

**Fortunas AI** is a conversational business-intelligence app for Indonesian MSMEs (UMKM — *Usaha Mikro, Kecil, dan Menengah*). The user opens a mobile-first PWA that looks like WhatsApp, types or speaks a question in Bahasa Indonesia, and gets a structured answer pulled from their own transaction data in BigQuery.

The project is a **submission to MIS Student Grant 2026 (BINUS University)**. Four-person team, Computer Science. The grant proposal commits to specific technical choices and novelty claims — do not silently substitute them.

**Status:** v2.1 in development. Mobile redesign and voice flow just landed (this commit). Backend is mature (v1.0); frontend was rewritten this iteration.

---

## 1b. Why this is a PWA + voice, not a WhatsApp bot — the real story

This is the most important context for understanding the shape of v2.1. Get this right before generating any user-facing content about the project.

**Original ambition (proposal draft):** A real WhatsApp bot. UMKM sends a text message in a defined format (CSV or `Key: Value`); a Twilio webhook routes it to the FastAPI backend; the backend parses, validates, stages to Sheets, then inserts to BigQuery. The appeal was zero install — every UMKM owner already has WhatsApp.

**The blocker that hit:** Since 2024, **Meta has restricted WhatsApp Business Cloud API access for Indonesian phone numbers**. BSP (Business Solution Provider) verification is strict and inconsistent; individual access is very hard to obtain. Operational cost was also non-trivial: $0.005–$0.09 per inbound message × thousands of UMKM = expensive at scale. This is a documented industry issue affecting many Indonesian startups — not a team failure.

**Why the proposal already accounted for this:** Novelty #5 was written as *"Web simulator chat WhatsApp-like — **tanpa setup WA Business API**"*. The "tanpa setup" phrase is a deliberate disclaimer. The proposal **never** promised actual WhatsApp integration — it promised a *web-based simulator with WhatsApp-like UX*. The pivot was anticipated from day one.

**v1 → v2.1 evolution:**
- **v1 MVP:** Web chat-style simulator. User types transactions in CSV or `Key: Value` format into a chat box. Backend parses with regex + Pydantic, stages to Sheets, inserts to BigQuery. The WhatsApp-like UX claim was satisfied by aesthetic alone.
- **v2.1 (current):** Mobile-first PWA. Chat-style UX preserved. Voice input replaces CSV-format text input — far more accessible to UMKM owners who don't want to memorize a column order.

**Why this pivot is a strict upgrade vs the original WA bot plan:**

| Dimension | Original (WA bot) | Current (PWA + voice) |
|---|---|---|
| Platform gatekeeper | Meta approval required | None |
| Setup complexity | Twilio + webhook + Meta verification | `flutter run -d chrome` (React/`npm` era client is gone — see Task 1b) |
| Per-message cost | $0.005–$0.09 inbound | Rp 0 |
| Data path | UMKM → Meta → Twilio → backend | UMKM → backend (direct) |
| Onboarding step | Save bot's number, message it | Open URL, "Add to Home Screen" |
| Input modality | Text only (CSV format) | Voice + text fallback |

**The WA pipeline service layer is still in the codebase** (`app/services/wa_pipeline.py`, `wa_parser.py`, `wa_validator.py`) and is **reused** by the voice flow. If Meta opens up WhatsApp Business Cloud API access for Indonesia in the future, integration is roughly: add a Twilio webhook route that calls `process_wa_message` — the entire validation, dedup, Sheets staging, and BigQuery insertion logic comes for free. That's the v2.x roadmap item.

**When framing this for the MIS Grant jury or any external audience:** lead with the proposal's existing disclaimer (*"tanpa setup WA Business API"*), then describe v2.1 as a UX upgrade *on top of* the simulator promise — not a deviation from it. Five proposal novelties remain intact; voice is added on top.

---

## 2. Hard commitments from the grant proposal

These are non-negotiable without explicit user confirmation. Substituting them invalidates a published novelty claim.

| Commitment | Reason |
|---|---|
| ~~**LLM runs locally via Ollama (Qwen3:8b)**~~ — **superseded.** Active provider is **Gemini 2.5 Flash** (`app/llm_provider.py`, default `LLM_PROVIDER=gemini`); confirmed by team, not a bug. The Ollama/Qwen3 path is **archived, not deleted** — still fully wired, selectable via `LLM_PROVIDER=ollama` + `docker compose --profile archive up ollama`. | Original proposal reasoning (UU PDP compliance, zero token cost, data never leaves server) no longer holds for the active provider — see `PROPOSAL_VS_REALITA.md` in the parent folder for the paper-narrative consequence. |
| **Embedding model: `paraphrase-multilingual-MiniLM-L12-v2`** | Supports Bahasa Indonesia + Javanese informal + code-switching. Pinned to `sentence-transformers==4.1.0` (v5+ breaks this model). |
| **STT: Web Speech API (browser-native, NOT Whisper)** | Conscious MVP trade-off. Chrome/Edge route audio to Google/Microsoft cloud; Safari iOS 15+ is on-device. Whisper-based fully-local STT is on the v2.x roadmap — do not silently swap models without revisiting this. |
| **Dual-layer staging (Sheets → BigQuery)** | Audit trail readable by humans + analytics warehouse. Ordering matters: Sheets first, then BigQuery. |
| **Intent-routed RAG (originally 4 analyses, now 11)** | Not generic NL→SQL. The proposal's 4 were `repeat_customer`, `high_value_customer`, `peak_hour`, `bundle_opportunity`. Production has since added `top_product`, `revenue_trend`, `customer_segmentation`, `churn_risk`, `slow_moving_product`, `average_basket_size`, `demand_forecast` — see `app/analysis_registry.py` (11 entries, all `enabled: True`). |
| **Web-based simulator (no WhatsApp Business API)** | Sidesteps Meta regional restriction. WhatsApp UX *aesthetic*, real channel via web/PWA. |

Target metrics (don't lower without discussion):
- F1-macro intent classification ≥ 0.85
- MRR@5 retrieval ≥ 0.75
- Human rating ≥ 4.0/5
- Latency p95 end-to-end ≤ 5s
- SUS ≥ 75 (n=30 UMKM users)
- Pipeline reliability ≥ 99.5%

---

## 3. Tech stack with versions

### Backend (`requirements.txt`)
- **Python** 3.11 or 3.12 (3.13 not tested)
- **FastAPI** 0.135 — async, OpenAPI auto-docs at `/docs`
- **Pydantic** 2.x — request/response validation
- **APScheduler** 3.x — daily briefing cron + WA retry tick
- **ChromaDB** 1.5.8 — vector store at `./chroma_db/`
- **sentence-transformers** 4.1.0 (PINNED — v5+ breaks the MiniLM model)
- **transformers** 4.57.6
- **google-cloud-bigquery** 3.41 — DWH client
- **gspread** 6.1.4 — Google Sheets client
- **requests** 2.33.1 — used to call the LLM provider HTTP APIs (Gemini/OpenAI/Ollama)
- **reportlab** 4.5+ — PDF overview generator
- **Gemini 2.5 Flash** (API, `GEMINI_API_KEY`) — the LLM provider actually in use
- **Ollama** (external runtime, **archived**) — `qwen3:8b` at `OLLAMA_BASE_URL`; only started if you deliberately select `LLM_PROVIDER=ollama` (compose profile `archive`)

### Mobile (`mobile/pubspec.yaml`) — **the only shipped client (web/PWA only as of Task 1b)**
- **Flutter** 3.27+ · **Dart** 3.6+
- **flutter_riverpod** 2.6 — state management
- **go_router** 14.6 — routing
- **dio** 5.7 — HTTP client
- **speech_to_text** 7.0 + **permission_handler** 11.3 — voice STT (id_ID)
- **shared_preferences** 2.3 — local history
- **google_fonts** 6.2 — Space Grotesk + Inter + JetBrains Mono
- **fl_chart** 0.69 — charts (reserved for v2.3 KPI deep-dive)
- **intl** 0.19 — Rp / date formatting

### Frontend — **archived (Task 1e, after a brief deletion in Task 1b)**
- React 19 + Vite (`frontend/package.json`, `react-router-dom`) is retained in
  the repo as an archive / design reference (`frontend/README.md`) — not
  built, not tested, not CI-gated. The folder and the nginx Docker image that
  serves it (`docker/frontend/`) are both present again; the shipped client
  is still Flutter web only.

### Infra
- **Docker** + Docker Compose v2 (production stack) — `backend` and an
  archived `frontend` (nginx + React build) by default; `ollama` is still
  defined in `docker-compose.yml` but sits behind `profiles: ["archive"]`, so
  it does not start unless you run `docker compose --profile archive up
  ollama` on purpose. See `DOCKER.md` for the current port-exposure caveat.

### Dataset
- **UCI Online Retail** (Chen, 2015) — ±1M rows seeded into BigQuery table `fortunasai.fortunas_ai.online_retail`

---

## 4. Repository layout

```
fortunas-ai/
├── app/                          # FastAPI backend
│   ├── agents/                   # sql_agent, rag_agent, insight_agent
│   ├── api/routes/               # health, ask, briefing, ingest, report, upload, voice, whatsapp
│   ├── core/                     # config, deps (lru_cache singletons), scheduler
│   ├── knowledge/                # ingest.py + umkm_docs/ (RAG corpus)
│   ├── services/                 # pipeline, sheets_service, wa_pipeline,
│   │                             #   wa_pipeline_structured (NEW v2.1),
│   │                             #   voice_parser (NEW v2.1),
│   │                             #   wa_parser, wa_validator, report_store
│   ├── analysis_registry.py      # intent → analysis mapping (11 entries, all enabled)
│   ├── bigquery_service.py       # BQ client factory
│   ├── intent_mapper.py          # Bahasa Indonesia question → intent rule classifier
│   ├── llm_service.py            # provider-agnostic LLM call + JSON repair helpers (llm_provider.py does the gemini/openai/ollama switch)
│   ├── prompt_builder.py         # Builds the LLM prompt with RAG context + SQL rows
│   ├── queries.py                # 11 BigQuery SQL templates (parameterized)
│   ├── schemas.py                # ALL Pydantic models — single source of truth for I/O contracts
│   ├── schema_context.py         # BQ table schema description for LLM prompts
│   ├── sql_guards.py             # Blocks raw SQL interpolation
│   └── main.py                   # FastAPI app factory + lifespan + scheduler hooks
├── mobile/                       # Flutter app — THE ONLY SHIPPED CLIENT, web/PWA only
│   ├── pubspec.yaml              # stack per design hand-off spec
│   ├── lib/
│   │   ├── main.dart             # runApp + system UI overlay
│   │   ├── app.dart              # go_router shell with FortunasBottomNav
│   │   ├── theme/tokens.dart     # FortunasColors + popShadow + GoogleFonts helpers
│   │   ├── api/                  # client.dart (dio + Riverpod), errors.dart, models.dart
│   │   ├── ui/                   # brand_mark, pill, example_chip, screen_header,
│   │   │                         #   mode_tabs, bottom_nav, icon_set
│   │   ├── screens/              # home, briefing, result, history, profile
│   │   └── voice/                # voice_flow (state machine), speech_controller,
│   │                             #   voice_idle/listening/parsed/success,
│   │                             #   big_mic_button, waveform, typed_transcript
│   ├── MIGRATION.md              # React → Flutter mapping reference (dated; android/ios since removed)
│   └── README.md                 # quick start
│   # NOTE: mobile/android/ and mobile/ios/ (native platform targets) were
│   # removed in Task 1b — only mobile/web/ is built and shipped.
├── frontend/                     # React 19 + Vite — ARCHIVED (Task 1e, after a
│                                 #   brief deletion in Task 1b): not built, not
│                                 #   tested, not CI-gated, not the shipped client.
│                                 #   See frontend/README.md.
├── docker/                       # backend/ (Dockerfile, entrypoint.sh), ollama/, frontend/ (nginx + React build, archived)
├── docs/                         # Fortunas-AI-Overview.pdf + generate_pdf.py + LinkedIn drafts
├── docker-compose.yml            # production stack
├── docker-compose.dev.yml        # hot-reload dev stack
├── Makefile                      # make up / dev / pull-model / ingest / zip / etc.
├── package.ps1                   # Windows packaging script (zip without CLAUDE.md)
├── requirements.txt
├── README.md
├── SETUP.md                      # manual setup, env template, troubleshooting
├── DOCKER.md                     # Docker guide
├── AI_CONTEXT.md                 # ← this file
└── CLAUDE.md                     # Claude Code-specific guide (gitignored; not in submission zip)
```

---

## 4b. Speech-to-Text — honest architectural disclosure

This deserves its own section because the surface-level pitch ("data never leaves the server") has a real exception at the STT step. Be transparent about it in any user-facing material you generate.

> **Task 1b/1e note:** this section documents the React-era implementation
> (`frontend/src/voice/useSpeechRecognition.js`). That file is retained in the
> repo — `frontend/` is archived, not deleted (Task 1e reverted Task 1b's
> deletion) — but the code path is not built, not run, and not shipped. The
> trade-off reasoning is kept for history. Current voice input lives in the
> Flutter app (`mobile/lib/voice/`) via the `speech_to_text` package (see §3).

### What we actually use

```
User speaks → mic → browser SpeechRecognition API
                         │
                         ├─ Chrome desktop/Android: audio → Google Cloud STT → text
                         ├─ Edge:                    audio → Microsoft Speech    → text
                         ├─ Safari iOS 15+:          on-device                    → text  ✓
                         ├─ Safari macOS Sonoma+:    on-device                    → text  ✓
                         ├─ Safari macOS older:      audio → Apple cloud STT      → text
                         └─ Firefox:                 NOT SUPPORTED — fall back to text input
                         ▼
                    transcript string → POST /voice/parse → regex / Qwen3:8b (LOCAL) → struct
```

Frontend code: `frontend/src/voice/useSpeechRecognition.js`. It is a thin wrapper around `window.SpeechRecognition || window.webkitSpeechRecognition`. We do NOT control where the audio bytes go after they hit the API — that's the browser vendor's choice.

### Why we picked this (not Whisper)

The user explicitly chose this trade-off during the v2.1 brainstorm. Reasoning recorded:

- **Zero backend deps** (no `faster-whisper`, no 470 MB/1.5 GB model download, no Python audio plumbing).
- **Zero disk overhead** on the server.
- **Latency in tens of milliseconds**, vs Whisper's 2–3 second batch inference even on GPU.
- **Bahasa Indonesia quality is already strong** on Chrome's STT — handles "delapan ribu lima ratus" type spoken numbers correctly, which is exactly the use case.

### The trade-off we accepted

The proposal's "data tidak keluar server" promise is **partially weakened** at this single step for the dominant user (UMKM on Android Chrome). LLM remains local; embeddings remain local; SQL and Sheets and BigQuery stay where they were. But raw audio is processed by Google's cloud servers before becoming text — and that text is what flows into the rest of the local pipeline.

For grant submission honesty: **explain this trade-off**, don't gloss over it.

### Roadmap mitigation (v2.x)

When we revisit STT for v2.x:

1. Add `app/api/routes/voice.py:POST /voice/transcribe` endpoint accepting audio multipart.
2. Add `faster-whisper` to `requirements.txt`. Recommended model: `small` (~470 MB, good Indonesian) or `medium` (~1.5 GB, better Indonesian).
3. Frontend `useSpeechRecognition.js` switches to `MediaRecorder` API → POST audio blob → receive text.
4. Keep Web Speech API as a fast-path fallback when (a) the backend Whisper service isn't available, or (b) the user opts into "fast mode" knowingly.

Until that ships, anyone documenting the system should describe STT as "browser-native via Web Speech API; v2.x adds Whisper for full-local STT."

---

## 5. Request flows (end-to-end)

> **Task 1b/1e note:** the frontend-side steps below (screen names, routes,
> the Vite proxy) describe the React client, which is no longer the shipped
> one and are stale as a result — the code itself is still in the repo,
> archived (`frontend/`, Task 1e reverted Task 1b's deletion), just not
> built/run/shipped. The backend-side steps (`app/api/routes/*` →
> `app/services/pipeline.py` → intent mapping → BigQuery → RAG → LLM) remain
> accurate — only the client calling these endpoints changed (Flutter web,
> `mobile/lib/api/client.dart`).

### Flow A: "Ask a business question" — `POST /ask`

```
Frontend HomeScreen
  └─ user types or clicks example chip
  └─ navigate('/result?q=...')
ResultScreen
  └─ api.ask(question) → POST /api/ask
       Vite proxy strips /api → :8000/ask
Backend app/api/routes/ask.py
  └─ run_ask() in app/services/pipeline.py
       │
       ├─ intent_mapper.map_question_to_analysis(question)
       │     → returns one of the 11 keys in app/analysis_registry.py
       │                       (repeat_customer, high_value_customer, peak_hour,
       │                        bundle_opportunity, top_product, revenue_trend,
       │                        customer_segmentation, churn_risk, slow_moving_product,
       │                        average_basket_size, demand_forecast) | "unknown"
       │
       ├─ rag_agent.query(question, n_results=4)
       │     → ChromaDB semantic search over umkm_docs/
       │     → returns top-K knowledge snippets
       │
       ├─ sql_agent.run(analysis_type)
       │     → queries.py SQL template (parameterized via sql_guards)
       │     → bigquery_service.execute() → rows list
       │
       ├─ prompt_builder.build_ask_prompt(question, rows, rag_snippets)
       │     → assembles few-shot Bahasa Indonesia prompt with rows + context
       │
       ├─ insight_agent.generate(prompt)
       │     → llm_service.llm_generate() → app/llm_provider.py routes to the
       │       active provider (Gemini 2.5 Flash by default; Ollama/Qwen3:8b
       │       archived, selectable via LLM_PROVIDER=ollama) → JSON response
       │     → llm_service._repair_output() coerces shape:
       │          { summary, top_findings[≤3], recommendation[≤3] }
       │
       └─ returns AskResponse {
            question, mapped_analysis, status, message,
            agent_trace[], rows[], llm_output: LLMOutput
          }
```

### Flow B: "Voice transaction entry" — `POST /voice/parse` then `/voice/transaction`

```
Frontend VoiceFlow (state machine: idle → listening → parsing → parsed → success)
  └─ user taps BigMicButton
  └─ useSpeechRecognition() starts Web Speech API (id-ID, continuous, interim)
  └─ live transcript streams into TypedTranscript
  └─ user taps stop
  └─ api.voiceParse(transcript) → POST /api/voice/parse
       │
Backend app/api/routes/voice.py → voice_parser.parse_transcript()
  │
  ├─ TIER 1: regex_parse() — fast path for structured speech
  │     Regex extracts invoice/qty/price/customer/country.
  │     _word_to_int_id() converts "delapan ribu lima ratus" → 8500.
  │     If all critical fields present → return confidence=0.92, source='regex'
  │
  └─ TIER 2: llm_parse() — fallback for messy free-form transcripts
        Calls the active LLM provider (app/llm_provider.py — Gemini 2.5 Flash
        by default; Ollama/Qwen3:8b archived) with a JSON-schema prompt.
        Returns confidence based on field completeness, source='llm'.
        On provider failure → return None → empty fallback.
       │
       returns VoiceParseResponse {
         invoice, product, qty, unit_price, total,
         customer, country, confidence, source
       }
  ▼
Frontend VoiceParsed
  └─ shows confirm card with editable fields
  └─ user clicks "Konfirmasi & Simpan"
  └─ api.voiceTransaction(payload) → POST /api/voice/transaction
       │
Backend app/api/routes/voice.py → wa_pipeline_structured.process_structured_transaction()
  │
  ├─ to_wa_payload() — maps voice schema → wa_validator schema:
  │     invoice (digits-only) → Invoice
  │     product               → Description + derived StockCode
  │     qty                   → Quantity
  │     unit_price            → Price
  │     customer              → Customer ID
  │     country               → Country
  │     InvoiceDate           → now() UTC ISO
  │
  ├─ wa_validator.validate_payload() — type coercion + business rules
  │     (qty bounds, price bounds, date bounds, etc.)
  │
  ├─ wa_validator.check_duplicate_in_bq(Invoice, StockCode)
  │     → if duplicate, reject
  │
  ├─ excel_upload._insert_in_batches([payload]) — straight to BigQuery, NO
  │     Sheets staging (docstring: "langsung ke BigQuery (tanpa Sheets)").
  │     The Sheets dual-layer staging from the original single-tenant design
  │     (`app/services/sheets_service.py`) is still used by the legacy
  │     `/wa/simulate` path (`app/services/wa_pipeline.py`) but NOT by this
  │     tenant-scoped voice flow.
  │
  └─ returns VoiceTransactionResponse { ok, status, reply, invoice }
       (row_number stays null on this path — it's a legacy field kept for
        schema compatibility with the Sheets-backed /wa/simulate flow)
  ▼
Frontend VoiceSuccess (confirmation animation + ROI nudge)
  └─ localStorage push for HistoryScreen display
  └─ auto-close after 2.2s
```

### Flow C: "Daily briefing" — `GET /briefing`

```
APScheduler (BRIEFING_CRON_HOUR:MINUTE, default 06:00 Asia/Jakarta)
  └─ _run_daily_briefing_job() in app/main.py
       │
       └─ pipeline.run_full_briefing()
            │
            └─ for each enabled analysis in ANALYSIS_REGISTRY (11 today):
                  run_briefing_section()
                  ├─ sql_agent.run(analysis_type)
                  ├─ rag_agent.query(label, n_results=3)
                  ├─ prompt_builder + insight_agent.generate()
                  └─ returns BriefingSection {
                       analysis_type, label, status, summary,
                       top_findings, recommendation, row_count, ...
                     }
            │
            └─ build_deterministic_executive_summary(successful)
                  composes 2-3 sentence high-level summary from the successful sections
       │
       └─ report_store.save_report() → app/data/daily_reports.json
```

Manual GET trigger: `/briefing` (returns immediately) or `/briefing/stream` (SSE, streams per-section).
Frontend `BriefingScreen` reads `GET /report/daily` to display saved latest + history.

---

## 6. Endpoint catalog

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| GET  | `/health` | Liveness + RAG check | — | `{status, rag_enabled}` |
| GET  | `/llm/health` | Active LLM provider health (Gemini by default) | — | `{status, provider, model, ...}` |
| POST | `/ask` | NL question → insight | `AskRequest` | `AskResponse` |
| POST | `/route` | Intent classify only (no SQL/LLM) | `AskRequest` | `{mapped_analysis, supported}` |
| GET  | `/briefing` | Run all 11 analyses + exec summary | — | `BriefingResponse` |
| GET  | `/briefing/stream` | Same, but SSE per-section | — | `text/event-stream` |
| GET  | `/report/daily` | Saved latest briefing + history | — | `DailyReportResponse` |
| POST | `/report/daily/run` | Run + save | — | `DailyReportResponse` |
| DELETE | `/report/daily` | Delete entry by `generated_at` or all | query | `DailyReportResponse` |
| POST | `/voice/parse` | Transcript → structured tx | `VoiceParseRequest` | `VoiceParseResponse` |
| POST | `/voice/transaction` | Confirmed payload → save | `VoiceTransactionRequest` | `VoiceTransactionResponse` |
| POST | `/ingest` | Re-ingest RAG corpus | `?reset=true` | `IngestResponse` |
| POST | `/upload` | CSV/Excel bulk transactions | multipart | `UploadResponse` |
| POST | `/wa/simulate` | Legacy WA text simulator | form | `{ok, reply}` |

All Pydantic models live in `app/schemas.py`. Don't define route-local models — extend `schemas.py`.

---

## 7. Conventions

- **Language:** User-facing strings, error messages, and chat replies are in **Bahasa Indonesia**. Identifiers, code comments, and technical jargon stay **English**. Mirror this when generating UI copy.
- **Function naming:** snake_case Python, camelCase JS.
- **Pydantic models:** snake_case fields. Frontend's `client.js` normalizes camelCase ↔ snake_case where needed.
- **Imports in route handlers:** keep thin. Route handlers wire HTTP ↔ service layer; **business logic lives in `app/services/*`**.
- **LLM JSON contract:** every LLM call expects strict JSON. `llm_service._repair_output` normalizes; if you add a new prompt, also extend the repair step.
- **CSS:** **no CSS-in-JS library**. Inline `style={{...}}` objects + CSS variables from `theme/tokens.css`. Zero runtime overhead. Don't introduce styled-components / emotion / tailwind without explicit discussion.
- **Animations:** Defined as keyframes in `theme/animations.css` with `fortunas-` prefix to avoid collisions. Reuse before creating new.
- **No tests right now.** Verification is by running the dev stack and exercising endpoints. If you add tests, use `pytest` and put them in `tests/`.

---

## 8. Common pitfalls (read before debugging)

1. **`sentence-transformers` version mismatch.** Pin is `4.1.0`. v5+ silently breaks `paraphrase-multilingual-MiniLM-L12-v2`. Symptom: `rag_enabled: false` in `/health` or `ValueError: Unrecognized processing class`. Fix: `pip install "sentence-transformers>=4.0,<5.0"`.

2. **Chroma collection missing.** Uvicorn started from the wrong directory makes `./chroma_db` resolve to an empty location. Always run uvicorn from repo root, or set `CHROMA_DB_PATH` to an absolute path in `.env`.

3. **`/ingest` is RAG re-ingestion, not transaction ingestion.** The endpoint name is misleading. Transactions go through `/voice/transaction` (new) or `/wa/simulate` (legacy text). `POST /ingest?reset=true` rebuilds the ChromaDB collection from `app/knowledge/umkm_docs/`.

4. **Invoice must be numeric in BigQuery.** Voice transcripts may say "INV-2024" — `wa_pipeline_structured.to_wa_payload` strips non-digits before validation. If the user only says letters, validation rejects with a clear Bahasa Indonesia error.

5. **Web Speech API browser support — and the privacy gap.** Chrome/Edge desktop+Android: full support, but audio is **sent to Google/Microsoft cloud STT** before returning as text. Safari iOS 15+: on-device (truly local). Safari macOS Sonoma+: on-device; older versions: cloud. Firefox: no support at all — UI falls back to a text input. Do not hard-fail on missing API.
   This means the "data never leaves the server" claim is **partially broken** at the STT stage in Chrome/Edge. LLM and embedding remain 100% local — that part of the proposal claim is intact. See section 4b below for the full honest disclosure and the Whisper roadmap.

6. **APScheduler in dev with `--reload`.** uvicorn's reload spawns a fresh process each code change; the scheduler restarts too. Briefing job will run only after the next cron tick post-restart. Verify by checking timestamps in `app/data/daily_reports.json`.

7. **CORS.** `app/core/config.py` (`CORS_ORIGINS` env var) defaults to `localhost:3000`, `127.0.0.1:3000`, `:5173` — these match the *archived* React dev server's ports (`frontend/`, Task 1e restored it after Task 1b's deletion; Vite dev server listens on `:3000` in `docker-compose.dev.yml`, `:5173` via a bare local `npm run dev`), not the shipped Flutter client. The `nginx`-serves-frontend same-origin scenario (`docker-compose.yml`'s `frontend` service) exists again too, but that's the archived/design-reference path — not the supported deploy (`deploy/nginx-fortunas.conf`, where the PWA and API share an origin instead). Whatever origin actually serves the Flutter web build (`flutter run -d chrome`'s dev port, or the deployed PWA's domain) needs to be in `CORS_ORIGINS` if it isn't already.

8. **`get_*_agent()` are `lru_cache`d in `app/core/deps.py`.** If you change `.env` (especially BigQuery or LLM provider settings — `LLM_PROVIDER`, `GEMINI_API_KEY`, `OLLAMA_*`), restart uvicorn — the cache doesn't observe env changes.

9. **WA pipeline is still wired** in `app/main.py` even though the new mobile UI doesn't expose it. This is intentional: `wa_pipeline.retry_failed_rows` is the APScheduler hook that re-tries `failed`/`pending` Sheets rows. Removing the route would break that job. Leave it.

10. **`CLAUDE.md` is gitignored.** It exists locally (generated by `/init`) to help Claude Code. It is **not** part of the submission zip. `Makefile`'s `zip` target and `package.ps1` both exclude it. `AI_CONTEXT.md` (this file) is the version checked in.

---

## 9. Extension recipes

### Adding a new analysis intent (e.g. `cancellation_rate`)

1. Add SQL template in `app/queries.py` (parameterized — use `bigquery.ScalarQueryParameter`, never f-string).
2. Register in `app/analysis_registry.py`:
   ```python
   "cancellation_rate": {
       "label": "Analisis Rate Pembatalan",
       "description": "...",
       "enabled": True,
   }
   ```
3. Extend the rule set in `app/intent_mapper.py` so questions like *"berapa pesanan yang batal?"* map to the new key.
4. If the prompt structure differs from the 11 existing analyses, extend `app/prompt_builder.py`.
5. Optionally add a Markdown doc to `app/knowledge/umkm_docs/` and run `POST /ingest?reset=true` to refresh RAG.
6. Add entries to the `_iconFor`/`_colorFor` maps in `mobile/lib/screens/briefing_screen.dart` so the KPI card renders. (Historical note: this used to be `frontend/src/screens/BriefingScreen.jsx`; the React client is no longer the shipped one — it's kept in the repo as an archive (`frontend/`, Task 1b removed it, Task 1e restored it) but isn't built/run/shipped — see day-18 handoff.)

### Adding a new API route

1. Create `app/api/routes/<name>.py` with `router = APIRouter(tags=["<name>"])`.
2. Define request/response Pydantic models in `app/schemas.py` (not in the route file).
3. Register in `app/main.py:create_app()` via `app.include_router(<name>.router)`.
4. Put business logic in `app/services/<name>_service.py` if it's >30 LOC.
5. Add client method to `mobile/lib/api/client.dart`. (Historical note: this used to also touch `frontend/src/api/client.js`; the React client is no longer the shipped one — it's kept in the repo as an archive (`frontend/`, Task 1b removed it, Task 1e restored it) but isn't built/run/shipped — see day-18 handoff.)

### Adding a new screen

1. Create `mobile/lib/screens/<name>_screen.dart`. Reuse `ScreenHeader`, `Pill`, `Icon` etc. from `mobile/lib/ui/`.
2. Add a route entry in `mobile/lib/app.dart` (go_router).
3. Update `mobile/lib/ui/bottom_nav.dart` if it deserves a tab.
(Historical note: this recipe used to target `frontend/src/screens/*.jsx`, `App.jsx`, `BottomNav.jsx`; the React client is no longer the shipped one — it's kept in the repo as an archive (`frontend/`, Task 1b removed it, Task 1e restored it) but isn't built/run/shipped — see day-18 handoff.)

### Generating the overview PDF

```
python docs/generate_pdf.py
```

Output: `docs/Fortunas-AI-Overview.pdf`. Pure ReportLab — no external services. Edit `build_story()` in `docs/generate_pdf.py` to update sections.

---

## 10. Build / run / deploy

### Local dev (manual)
```bash
# Backend
python -m venv .venv
.venv\Scripts\activate     # Windows; source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
python -m app.knowledge.ingest          # one-time, builds chroma_db/
uvicorn app.main:app --reload --port 8000

# Client (Flutter web / PWA) — the only shipped client
# Install Flutter SDK first: https://docs.flutter.dev/get-started/install
cd mobile
flutter pub get
flutter run -d chrome --dart-define=FORTUNAS_API=http://127.0.0.1:8000
# Production build: flutter build web --release --no-web-resources-cdn

# Ollama (OPTIONAL — only if you deliberately set LLM_PROVIDER=ollama;
# the default provider is Gemini and needs no local model server at all)
ollama pull qwen3:8b                    # one-time, ~4.8 GB download
ollama serve
```

### Viewing the app

The single shipped client is **Flutter web (PWA)** (in `mobile/`). As of Task 1b,
`mobile/android/` and `mobile/ios/` (native platform targets) have been removed
from the repo — only the web target is built and shipped. `frontend/` (the
React client) was also removed by Task 1b, then restored by Task 1e as an
archive / design reference — it is back in the repo but still not built, not
tested, and not shipped:

```bash
cd mobile
flutter run -d chrome --dart-define=FORTUNAS_API=http://127.0.0.1:8000
```

Note: `speech_to_text` has limited support in web — voice flow falls back to
text input on browsers/conditions where it isn't available.

See `mobile/README.md` and `mobile/MIGRATION.md` for further details. (Historical
note: `mobile/MIGRATION.md` predates the native-target removal and still refers
to android/ios scaffolding — that's a dated record, left as-is intentionally.)

### Docker (recommended)
```bash
make up                  # build + start the backend (Gemini by default — no Ollama needed)
# Backend: http://localhost:8000/docs (PWA runs outside Docker — see above)
make dev                 # hot-reload variant via docker-compose.dev.yml

# Only if you deliberately want the archived local-LLM path (LLM_PROVIDER=ollama):
# docker compose --profile archive up ollama
# make pull-model          # one-time: docker compose --profile archive exec ollama ollama pull qwen3:8b
```

### Environment variables (`.env` at repo root)

Required: `GOOGLE_APPLICATION_CREDENTIALS` (absolute path to BQ service-account JSON), `BIGQUERY_PROJECT_ID`, `BIGQUERY_DATASET`, `BIGQUERY_TABLE`, and `GEMINI_API_KEY` (the active LLM provider — `LLM_PROVIDER` defaults to `gemini`). Optional: `OLLAMA_BASE_URL` (in Docker: `http://ollama:11434`) and `OLLAMA_MODEL` only matter if you set `LLM_PROVIDER=ollama` to use the archived local path; also `BRIEFING_*` scheduler, `WA_RETRY_ENABLED`. Full template in `SETUP.md` §3.4.

### Submission packaging (only when explicitly requested)
```bash
make zip                 # produces fortunas-ai.zip; excludes CLAUDE.md, .git, node_modules, credentials, etc.
# or on Windows:
pwsh ./package.ps1
```

---

## 11. Quick endpoint smoke tests

```bash
# Health
curl http://localhost:8000/health

# Intent classification only (no LLM, no SQL)
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"question":"Siapa pelanggan paling setia bulan ini?"}'

# Voice parsing (offline-friendly — uses regex fast-path)
curl -X POST http://localhost:8000/voice/parse \
  -H "Content-Type: application/json" \
  -d '{"transcript":"Invoice 489438, sabun cuci, qty 10, harga delapan ribu lima ratus"}'

# Full ask (requires the active LLM provider reachable — Gemini API by default,
# i.e. GEMINI_API_KEY set; only requires Ollama running if LLM_PROVIDER=ollama)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Pelanggan mana yang paling sering beli bulan ini?"}'
```

---

## 12. Glossary

- **UMKM** — Usaha Mikro, Kecil, dan Menengah. Indonesian MSME (Micro, Small, Medium Enterprise).
- **RAG** — Retrieval-Augmented Generation. Inject retrieved docs into LLM prompt for grounding.
- **Intent-routed RAG** — Specific to this project: question is first classified to one of 11 pre-built analyses (not free-form NL-to-SQL).
- **Dual-layer staging** — Sheets first (audit trail readable by humans), then BigQuery (analytics), with auto-retry on BQ failure. This is the original single-tenant design, still live for the legacy `/wa/simulate` path (`app/services/wa_pipeline.py`). The current tenant-scoped voice flow (`wa_pipeline_structured.py`) writes straight to BigQuery — no Sheets layer.
- **UU PDP No. 27/2022** — Indonesian Personal Data Protection Law. Local LLM execution is part of the compliance posture.
- **WA pipeline** — `app/services/wa_pipeline.py`. Originally for WhatsApp Business API; now mostly a service layer reused by the new voice flow.
- **Neo-brutalism** — Design language used in the v2.1 UI: hard 1.5-2px borders, pop shadows `4px 4px 0 ink`, no soft shadows.

---

## 13. What this file is NOT

- Not a marketing brief — see `README.md` and `docs/Fortunas-AI-Overview.pdf` for those.
- Not a setup walkthrough — see `SETUP.md`.
- Not a Docker guide — see `DOCKER.md`.
- Not a Claude Code-specific guide — see `CLAUDE.md` (gitignored).

This file is **for any AI assistant** picking up the codebase cold. If something here is wrong, it's a bug — fix this file alongside the code change.
