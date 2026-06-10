# Fortunas AI · Mobile (Flutter)

Mobile app for Fortunas AI, built with **Flutter 3.27+**. Replaces the React PWA from v2.1.

## Quick start

```bash
# Install Flutter SDK (one-time):
# https://docs.flutter.dev/get-started/install

cd mobile
flutter create . --platforms=android,ios,web   # scaffold native folders (first time only)
flutter pub get

# Run on the fastest target — Chrome (no emulator needed):
flutter run -d chrome --dart-define=FORTUNAS_API=http://127.0.0.1:8000

# Or run on physical Android device:
flutter run --dart-define=FORTUNAS_API=http://192.168.40.6:8000
```

Backend (FastAPI + Ollama + BigQuery) needs to be running. See repo root `SETUP.md` and `DOCKER.md`.

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
| Android emulator | `http://10.0.2.2:8000` (host's localhost from emulator) |
| iOS simulator | `http://localhost:8000` |
| Physical phone (same WiFi) | `http://<your-PC-IP>:8000` |
| Production | `https://api.fortunas.example.com` |

## Voice permission notes

Android: `AndroidManifest.xml` needs `RECORD_AUDIO` (added automatically by `permission_handler` setup).
iOS: `Info.plist` needs `NSMicrophoneUsageDescription` and `NSSpeechRecognitionUsageDescription`. Add after `flutter create .` generates the iOS folder.

## Status

This is **v2.2 dev-in-progress** (Phase 1-3 of the design's 4-phase migration roadmap). See [MIGRATION.md](MIGRATION.md) §"Migration roadmap from design spec" for current status and follow-ups.

## License

MIT — same as the rest of the Fortunas AI project.
