> ⚠️ **OUTDATED (pre-v4.0).** This file predates the multi-tenant SaaS rewrite
> (auth/JWT, per-tenant BigQuery tables, Gemini LLM, VPS deploy). For current
> context use [`memory.md`](memory.md) and [`README.md`](README.md); for setup
> see README Quick Start and [`deploy/DEPLOY.md`](deploy/DEPLOY.md). Kept for history.

# AI_CONTEXT.md — Fortunas AI

> **Audience:** Any AI assistant (Claude, GPT, Gemini, Llama, etc.) reading this codebase for the first time. This file is the single source of truth — no other reading required to start being productive.
>
> **Last updated:** 2026-05-19 (v2.2 — Flutter migration in progress)
>
> **Active frontend:** `mobile/` (Flutter). The `frontend/` React PWA is **retained as legacy reference** until the Flutter app is device-verified — see `mobile/MIGRATION.md` for the rationale.

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
| Setup complexity | Twilio + webhook + Meta verification | `npm run dev` |
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
| **LLM runs locally via Ollama (Qwen3:8b)** | Compliance with UU PDP No. 27/2022. Zero API token cost. LLM-stage data never leaves the server. |
| **Embedding model: `paraphrase-multilingual-MiniLM-L12-v2`** | Supports Bahasa Indonesia + Javanese informal + code-switching. Pinned to `sentence-transformers==4.1.0` (v5+ breaks this model). |
| **STT: Web Speech API (browser-native, NOT Whisper)** | Conscious MVP trade-off. Chrome/Edge route audio to Google/Microsoft cloud; Safari iOS 15+ is on-device. Whisper-based fully-local STT is on the v2.x roadmap — do not silently swap models without revisiting this. |
| **Dual-layer staging (Sheets → BigQuery)** | Audit trail readable by humans + analytics warehouse. Ordering matters: Sheets first, then BigQuery. |
| **Intent-routed RAG (4 analyses)** | Not generic NL→SQL. Each question routes to one of: `repeat_customer`, `high_value_customer`, `peak_hour`, `bundle_opportunity`. |
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
- **requests** 2.33.1 — used to call Ollama HTTP
- **reportlab** 4.5+ — PDF overview generator
- **Ollama** (external runtime) running `qwen3:8b` at `OLLAMA_BASE_URL`

### Mobile (`mobile/pubspec.yaml`) — **active frontend for v2.2+**
- **Flutter** 3.27+ · **Dart** 3.6+
- **flutter_riverpod** 2.6 — state management
- **go_router** 14.6 — routing
- **dio** 5.7 — HTTP client
- **speech_to_text** 7.0 + **permission_handler** 11.3 — voice STT (id_ID)
- **shared_preferences** 2.3 — local history
- **google_fonts** 6.2 — Space Grotesk + Inter + JetBrains Mono
- **fl_chart** 0.69 — charts (reserved for v2.3 KPI deep-dive)
- **intl** 0.19 — Rp / date formatting

### Frontend (`frontend/package.json`) — **legacy v2.1, kept as fallback**
- **React** 19.2.4 + **Vite** 8.0.4
- **react-router-dom** 7.x
- Lives in `frontend/`. Not actively developed; do not add features here. The Flutter app at `mobile/` is the active mobile target.

### Infra
- **Docker** + Docker Compose v2 (production stack)
- **nginx:alpine** — production frontend serving + `/api/*` reverse proxy to backend:8000

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
│   ├── analysis_registry.py      # intent → analysis mapping (4 entries)
│   ├── bigquery_service.py       # BQ client factory
│   ├── intent_mapper.py          # Bahasa Indonesia question → intent rule classifier
│   ├── llm_service.py            # Ollama wrapper + JSON repair helpers
│   ├── prompt_builder.py         # Builds the LLM prompt with RAG context + SQL rows
│   ├── queries.py                # 4 BigQuery SQL templates (parameterized)
│   ├── schemas.py                # ALL Pydantic models — single source of truth for I/O contracts
│   ├── schema_context.py         # BQ table schema description for LLM prompts
│   ├── sql_guards.py             # Blocks raw SQL interpolation
│   └── main.py                   # FastAPI app factory + lifespan + scheduler hooks
├── mobile/                       # Flutter app — ACTIVE FRONTEND (v2.2+)
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
│   ├── MIGRATION.md              # React → Flutter mapping reference
│   └── README.md                 # quick start
├── frontend/                     # React PWA — LEGACY v2.1, kept as fallback reference
│   ├── src/                      # screens/, ui/, voice/, api/, theme/
│   └── package.json              # do not add features here; mobile/ is the active target
├── docker/                       # Dockerfile, entrypoint.sh, nginx.conf
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
       │     → returns one of: repeat_customer | high_value_customer
       │                       | peak_hour | bundle_opportunity | "unknown"
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
       │     → llm_service.call_ollama() → Qwen3:8b JSON response
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
        Calls Ollama with JSON-schema prompt for Qwen3:8b.
        Returns confidence based on field completeness, source='llm'.
        On Ollama failure → return None → empty fallback.
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
  ├─ sheets_service.append_transaction() — Sheets staging (audit trail FIRST)
  │     → returns row_number
  │
  ├─ excel_upload._insert_in_batches([payload]) — BigQuery insert
  │
  ├─ sheets_service.update_bq_status(row, 'success'|'failed', error)
  │     → close the loop on the audit trail
  │
  └─ returns VoiceTransactionResponse {
       ok, status, reply, invoice, row_number
     }
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
            └─ for each of the 4 analyses in ANALYSIS_REGISTRY:
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
                  composes 2-3 sentence high-level summary from the 4 sections
       │
       └─ report_store.save_report() → app/data/daily_reports.json
```

Manual GET trigger: `/briefing` (returns immediately) or `/briefing/stream` (SSE, streams per-section).
Frontend `BriefingScreen` reads `GET /report/daily` to display saved latest + history.

---

## 6. Endpoint catalog

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| GET  | `/health` | Liveness + Ollama check | — | `{status, ollama: {...}}` |
| POST | `/ask` | NL question → insight | `AskRequest` | `AskResponse` |
| POST | `/route` | Intent classify only (no SQL/LLM) | `AskRequest` | `{mapped_analysis, supported}` |
| GET  | `/briefing` | Run 4 analyses + exec summary | — | `BriefingResponse` |
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

7. **CORS in Docker vs local.** `app/core/config.py` allows `localhost:3000`, `127.0.0.1:3000`, `:5173`. In Docker production, nginx serves frontend so requests are same-origin — no CORS issue. In dev, Vite proxy strips `/api` so backend sees `/ask` not `/api/ask`.

8. **`get_*_agent()` are `lru_cache`d in `app/core/deps.py`.** If you change `.env` (especially BigQuery or Ollama settings), restart uvicorn — the cache doesn't observe env changes.

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
4. If the prompt structure differs from the four existing analyses, extend `app/prompt_builder.py`.
5. Optionally add a Markdown doc to `app/knowledge/umkm_docs/` and run `POST /ingest?reset=true` to refresh RAG.
6. Add `ICON_FOR_ANALYSIS` and `COLOR_FOR_ANALYSIS` entries in `frontend/src/screens/BriefingScreen.jsx` so the KPI card renders.

### Adding a new API route

1. Create `app/api/routes/<name>.py` with `router = APIRouter(tags=["<name>"])`.
2. Define request/response Pydantic models in `app/schemas.py` (not in the route file).
3. Register in `app/main.py:create_app()` via `app.include_router(<name>.router)`.
4. Put business logic in `app/services/<name>_service.py` if it's >30 LOC.
5. Add client method to `frontend/src/api/client.js`.

### Adding a new screen

1. Create `frontend/src/screens/<Name>Screen.jsx`. Reuse `ScreenHeader`, `Pill`, `Icon` etc.
2. Add a route entry in `frontend/src/App.jsx` (`<Route path="..." element={...} />`).
3. Update `frontend/src/ui/BottomNav.jsx` `ITEMS` array if it deserves a tab.

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

# Mobile (Flutter) — ACTIVE FRONTEND
# Install Flutter SDK first: https://docs.flutter.dev/get-started/install
cd mobile
flutter create . --platforms=android,ios,web   # one-time, scaffolds android/ ios/ web/
flutter pub get
flutter run -d chrome --dart-define=FORTUNAS_API=http://127.0.0.1:8000

# Legacy React PWA (only if you need to compare or fallback)
cd frontend
npm install
npm run dev                             # http://localhost:3000

# Ollama (separate terminal)
ollama pull qwen3:8b                    # one-time, ~4.8 GB download
ollama serve
```

### Viewing the mobile app

Active frontend is **Flutter** (in `mobile/`). The React PWA in `frontend/` is legacy.

Three ways to preview the Flutter app:

1. **Chrome / web build** (fastest, no emulator needed):
   ```bash
   cd mobile
   flutter run -d chrome --dart-define=FORTUNAS_API=http://127.0.0.1:8000
   ```
   Flutter compiles to WASM + canvas. Note: `speech_to_text` does not work in web — voice flow falls back to text input. For mic testing use a real device or emulator.

2. **Android emulator** (preferred for voice testing):
   ```bash
   flutter run -d emulator-5554 --dart-define=FORTUNAS_API=http://10.0.2.2:8000
   ```
   `10.0.2.2` is the emulator's alias for the host's localhost.

3. **Physical phone over USB**:
   ```bash
   flutter run --dart-define=FORTUNAS_API=http://192.168.40.6:8000
   ```
   Phone must be on same WiFi as the backend. USB debugging enabled. No HTTPS needed (Flutter app talks directly to backend; no browser cert restriction).

See `mobile/README.md` and `mobile/MIGRATION.md` for full details.

### Docker (recommended)
```bash
make up                  # build + start all services
make pull-model          # one-time: docker compose exec ollama ollama pull qwen3:8b
# Frontend: http://localhost:3000   Backend: http://localhost:8000/docs
make dev                 # hot-reload variant via docker-compose.dev.yml
```

### Environment variables (`.env` at repo root)

Required: `GOOGLE_APPLICATION_CREDENTIALS` (absolute path to BQ service-account JSON), `BIGQUERY_PROJECT_ID`, `BIGQUERY_DATASET`, `BIGQUERY_TABLE`. Optional but useful: `OLLAMA_BASE_URL` (in Docker: `http://ollama:11434`), `OLLAMA_MODEL`, `BRIEFING_*` scheduler, `WA_RETRY_ENABLED`. Full template in `SETUP.md` §3.4.

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

# Full ask (requires Ollama running)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Pelanggan mana yang paling sering beli bulan ini?"}'
```

---

## 12. Glossary

- **UMKM** — Usaha Mikro, Kecil, dan Menengah. Indonesian MSME (Micro, Small, Medium Enterprise).
- **RAG** — Retrieval-Augmented Generation. Inject retrieved docs into LLM prompt for grounding.
- **Intent-routed RAG** — Specific to this project: question is first classified to one of 4 pre-built analyses (not free-form NL-to-SQL).
- **Dual-layer staging** — Sheets first (audit trail readable by humans), then BigQuery (analytics). Auto-retry on BQ failure.
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
