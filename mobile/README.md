> ⚠️ **DEPRECATED (2026-08-07, ADR-0002):** klien produksi = React `frontend/`. Direktori ini
> cadangan demo sampai Gate D dan TIDAK menerima fitur baru. Lihat
> `docs/adr/0002-react-production-client.md`.

# Fortunas AI · Mobile (Flutter)

Client for Fortunas AI, built with **Flutter 3.32.x**, shipped as a **PWA (web only)**.
Originally replaced the React PWA from v2.1; the native Android/iOS targets that
existed during the Flutter migration were removed in Task 1b — this is a
web-only project now, and `flutter build web` is what actually ships.

## Quick start

```bash
# Install Flutter SDK (one-time):
# https://docs.flutter.dev/get-started/install

cd mobile
flutter pub get

# Run in Chrome (dev, hot reload):
flutter run -d chrome --dart-define=FORTUNAS_API=http://127.0.0.1:8000

# Production build (what actually ships):
flutter build web --release --no-web-resources-cdn
```

Backend (FastAPI + Gemini + BigQuery) needs to be running — Ollama is archived, not required (see `app/llm_provider.py`). See repo root `SETUP.md` and `DOCKER.md`.

## What this app is

Mobile-first UMKM business analyst:
- Tanya — ask business questions in Bahasa Indonesia
- Briefing — daily executive summary + KPI cards
- Voice — speak transactions, AI parses and saves to BigQuery
- Riwayat — local + cloud history
- Saya — engine status and team info

## Layout & architecture

See [MIGRATION.md](MIGRATION.md) for the full React → Flutter mapping, file inventory, and migration roadmap.

## Tech

| Layer | Package |
|---|---|
| Routing | go_router 14.x |
| State | flutter_riverpod 2.x |
| HTTP | dio 5.x |
| Voice | speech_to_text 7.x + permission_handler 11.x |
| Storage | shared_preferences |
| Fonts | google_fonts (Space Grotesk + Inter + JetBrains Mono) |
| Charts | fl_chart 0.69 |
| i18n | intl |

Stack matches the design hand-off "07 · Flutter migration" spec.

## Backend URL config

The app reads `FORTUNAS_API` at compile time via `--dart-define`. Defaults to `http://127.0.0.1:8000`.

| Run target | Use this URL |
|---|---|
| Chrome, local backend | `http://127.0.0.1:8000` (the default) |
| Chrome, backend on another machine (same network) | `http://<host-IP>:8000` |
| Production | the deployed API origin (see `deploy/DEPLOY.md`) |

## Voice permission notes

Web only: the browser prompts for microphone access on first use of
`speech_to_text` (no manifest entries — those were Android/iOS-only and no
longer apply). **HTTPS is required** — `getUserMedia` (and the voice feature
with it) is blocked entirely outside a secure context. See
`deploy/nginx-fortunas.conf` for the production HTTPS setup.

## Status

This is **v2.2 dev-in-progress** (Phase 1-3 of the design's 4-phase migration roadmap). See [MIGRATION.md](MIGRATION.md) §"Migration roadmap from design spec" for current status and follow-ups.

## License

MIT — same as the rest of the Fortunas AI project.
