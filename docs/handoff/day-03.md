# Handoff Day 3 (DPA backend slice)

**Dev hari ini:** Go Steven Sanjaya
**Tanggal:** 2026-06-24 (dikerjakan lebih awal dari window resmi, lanjutan dari Day 2)
**Branch:** `feat/dpa-backend` (dari `main` @ `345b667`, PR #3 Day-2 sudah merged)

## ✅ Selesai hari ini — DPA jadi "pagar AI" (MVP fitur #7)

Slice backend penuh untuk Data Processing Agreement: UMKM simpan aturan boleh/larang, backend menegakkan **deterministik (Pre + Post)** di `/ask` + inject ke prompt Gemini. **Nol kredensial eksternal**, semua diuji offline. 11 commit, **74 test hijau** (48 baseline + 26 baru), ruff bersih.

- `app/dpa_repo.py` — `get_dpa`/`upsert_dpa` atas tabel `tenant_dpa_policies` (sudah ada Day 2). Default-safe: tenant tanpa DPA → payload kosong version 0. Versioned.
- `app/services/dpa_guard.py` — guardrail PURE (nol I/O): `normalize_rules`, `find_violations` (word-boundary regex, case-insensitive), `check_question`, `check_answer`, `build_refusal`.
- `app/api/routes/dpa.py` — `GET /umkm/dpa` + `PUT /umkm/dpa` (password-confirm; salah → **403** "Konfirmasi password salah."). Terdaftar di `app/main.py`.
- `app/prompt_builder.py` — param `dpa_policy` + `_dpa_constraint_block` (HARD CONSTRAINT block). `dpa_policy=None` → output identik baseline (regression aman).
- `app/agents/insight_agent.py` — thread `dpa_policy`; `call_ollama` dijadikan lazy-import.
- `app/services/pipeline.py` — `run_ask` Pre-check (refuse sebelum BQ/Gemini) + Post-check (refuse, rows tetap, llm_output=None); `run_briefing_section` dapat prompt-layer DPA (tanpa post-check). Refusal = `status="refused"` (HTTP 200, bukan exception).

## ⚙️ Catatan teknis penting

- **Pipeline importable di CI ringan.** `app/services/pipeline.py` dulu menarik `bigquery_service`(google.cloud)/`rag_agent`(chromadb)/`llm_provider`(requests) di import-time → tak bisa di-import di CI minimal. Diperbaiki: `InsightAgent`/`RAGAgent` dipindah ke `TYPE_CHECKING` (aman karena `from __future__ import annotations`), `run_query` di-lazy-import dalam `execute_analysis`. Sekarang `import app.services.pipeline` jalan tanpa chromadb.
- **CI deps ditambah (ringan saja):** `.github/workflows/ci.yml` → `fastapi httpx bcrypt PyJWT python-dotenv`. **`requirements.txt` +`PyJWT==2.10.1`** (latent: dipakai `app/core/auth.py` tapi belum terdaftar). TIDAK menambah torch/chromadb/google-cloud.
- **Pola test:** route test bikin app minimal (auth+dpa router saja) → tak import `app.main` (yang menarik router berat). Integration `run_ask` pakai fake InsightAgent + monkeypatch `execute_analysis` → nol BQ/Gemini. Semua SQLite in-memory (`conftest.py`).

## 🔴 Blocker

- TIDAK ADA. Slice merge-able default-safe walau Gemini/Postgres prod belum tersambung.

## 📦 State branch

- Branch `feat/dpa-backend` (11 commit `940cdff..16c4275`) **sudah MERGED ke `main`** via PR #4 (squash, commit `5d28ecd`, 2026-06-25). Kedua CI check hijau (Backend ruff+pytest, Mobile flutter analyze).
- Branch sudah dihapus (lokal + remote, pruned). `main` pasca-merge: 74 test hijau, ruff bersih.

## 🎯 Goal berikutnya

- **UI mobile DPA** (roadmap Hari 12): onboarding force-fill DPA + edit (password-confirm) — backend sudah siap.
- Slice **Customer JWT + QR identity backend** (credential-free bagian sign/verify; bootstrap Firebase di-stub) — kandidat berikutnya.

## 📌 Catatan tambahan

- Enforcement DPA 100% default-safe & nol seam eksternal baru. Hanya jawaban `/ask` non-refused yang tetap perlu `GEMINI_API_KEY` (sudah tercatat di `Fortunas/PENDING_EXTERNAL_SETUP.md`).
- Out-of-scope (sengaja, defer): email-OTP edit DPA (v5.1), `policy_summary` via LLM, post-check deterministik pada briefing.
- Spec & plan: `Fortunas/brainstorming/{specs,plans}/2026-06-24-dpa-backend*` (luar repo).
