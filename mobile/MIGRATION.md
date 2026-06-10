# React PWA → Flutter Migration (v2.1 → v2.2)

This document captures **what was moved, what was kept, and how to run** the new Flutter mobile app for Fortunas AI. It is the dev reference — for the user-facing story see `docs/Fortunas-AI-Overview.pdf`.

## TL;DR

- **Old:** `frontend/` (React 19 + Vite PWA), still present as fallback reference.
- **New:** `mobile/` (Flutter 3.27+ project), this is the active mobile app.
- **Backend:** **unchanged** — FastAPI, Ollama, BigQuery, all of `app/services/` and `app/api/routes/`.
- **Voice:** Web Speech API replaced with `speech_to_text` Flutter plugin (id_ID locale).
- **Stack picks match the design hand-off spec** (mockup artboards "07 · Flutter migration" + "08 · React → Flutter mapping").

## What's in `mobile/`

```
mobile/
├── pubspec.yaml                          # deps per design spec
└── lib/
    ├── main.dart                         # runApp + system UI overlay
    ├── app.dart                          # go_router shell with bottom nav
    ├── theme/
    │   └── tokens.dart                   # FortunasColors + popShadow + GoogleFonts helpers
    ├── api/
    │   ├── client.dart                   # FortunasApi (dio) + apiProvider (Riverpod)
    │   ├── errors.dart                   # humanizeError → Bahasa Indonesia
    │   └── models.dart                   # DTOs mirroring app/schemas.py
    ├── ui/
    │   ├── brand_mark.dart               # rotated F tile
    │   ├── pill.dart                     # status chip with 1.5px ink border
    │   ├── example_chip.dart             # tappable suggestion
    │   ├── screen_header.dart            # brand + wordmark + AI online
    │   ├── mode_tabs.dart                # Tanya/Briefing/Harian pill toggle
    │   ├── bottom_nav.dart               # 5-slot + raised violet mic FAB
    │   └── icon_set.dart                 # React Icon → Material Icons mapping
    ├── screens/
    │   ├── home_screen.dart              # Tanya — hero + input + examples + Tambah Transaksi
    │   ├── briefing_screen.dart          # /report/daily → exec summary + KPI grid + findings
    │   ├── result_screen.dart            # /ask → summary + findings + recommendations
    │   ├── history_screen.dart           # local voice tx + briefing history
    │   └── profile_screen.dart           # /health status + storage + team + compliance
    └── voice/
        ├── voice_flow.dart               # state machine (idle/listening/parsing/parsed/success)
        ├── speech_controller.dart        # ChangeNotifier wrapper around speech_to_text
        ├── voice_idle.dart               # CTA + big mic + sample phrasing
        ├── voice_listening.dart          # transcript card + waveform + stop button
        ├── voice_parsed.dart             # editable confirm card
        ├── voice_success.dart            # check animation + ROI nudge
        ├── big_mic_button.dart           # 104→120px button with pulse rings
        ├── waveform.dart                 # 28-bar animated voice indicator
        └── typed_transcript.dart         # live transcript with blinking caret
```

## Component mapping (React → Flutter)

Per the design hand-off "08 · React → Flutter mapping" artboard. Used as the porting reference.

| React JSX | Flutter widget | Notes |
|---|---|---|
| `<div>` | `Container` / `Column` / `Row` | `Container` for styled box, `Column`/`Row` for layout |
| `<button>` | `InkWell` + `Container` | Lets us preserve custom neo-brutalist shape & ripple |
| `onClick` | `onTap` | Same idea. `onLongPress` for press-and-hold mic. |
| `useState` | `StateProvider` (Riverpod) | Used for shared state. Local component state stays in `StatefulWidget` |
| `useEffect` | `initState` + `dispose` | Pair listeners. `Timer.periodic` for repeating work; `Future.delayed` for setTimeout. |
| `border` + `boxShadow` | `BoxDecoration` | `border: Border.all(color: ink, width: 1.5)` + `boxShadow: [BoxShadow(offset: Offset(4,4), color: ink)]` |
| `borderRadius: 18` | `BorderRadius.circular(18)` | Identity map |
| `position: absolute` | `Stack` + `Positioned` | Wrap parent in `Stack`, child gets `Positioned(top:, left:, ...)` |
| `overflow: auto` | `SingleChildScrollView` / `ListView` | `ListView.builder` for long lists (lazy) |
| `fetch('/api/ask')` | `dio.post('/ask')` | `apiProvider` singleton via Riverpod |
| `setTimeout` | `Future.delayed(Duration(...), () { ... })` | Cancel with stored future |
| `<input>` | `TextField` | `controller: TextEditingController()` |
| CSS `@keyframes` | `AnimationController` + `Tween` | Waveform: controller loop + `Tween<double>(0.18, 1.0)` → scaleY |
| Web Speech API | `speech_to_text` (^7.0) | `SpeechToText().listen(localeId: 'id_ID')` |
| `localStorage` | `shared_preferences` | Voice history persistence |
| `<Link>` / `navigate()` | `context.go('/briefing')` | go_router |

## Pivots from React PWA

### Voice — Web Speech API → `speech_to_text`

| | React PWA | Flutter |
|---|---|---|
| Plugin | `webkitSpeechRecognition` browser API | `speech_to_text: ^7.0` |
| Locale | `lang='id-ID'` | `localeId: 'id_ID'` |
| Continuous | `recognition.continuous = true` | `listenMode: ListenMode.dictation` |
| Interim results | `interimResults: true` | `partialResults: true` |
| Permission | Browser prompts on `.start()` | Explicit `Permission.microphone.request()` first |

Privacy gap **is the same** as the React PWA:
- Android: routes audio to Google Cloud STT (cloud-bound).
- iOS 15+: on-device.
- Documented in `AI_CONTEXT.md` §4b.

### Routing — React Router → go_router

```
React Router                       go_router
─────────────                      ─────────
<Route path="/"        ...>        GoRoute(path: '/',         builder: ...)
<Route path="/briefing"...>        GoRoute(path: '/briefing', builder: ...)
<Route path="/result"  ...>        GoRoute(path: '/result',   builder: ctx -> uri.queryParameters)
<Routes><BottomNav/>               ShellRoute(builder: child → Scaffold w/ FortunasBottomNav)

useNavigate() → navigate('/x')     context.go('/x')
useLocation()                      GoRouterState.of(context).uri.path
useSearchParams() → ?q=...         state.uri.queryParameters['q']
overlay state showVoice            push('/voice') as fullscreenDialog
```

### State management — useState/lifted state → Riverpod

The React app used local `useState` for UI state and lifted shared state to `App.jsx`. In Flutter:

- **Local UI state** (toggles, form fields) → `StatefulWidget` `setState`. No Riverpod needed.
- **API client + shared services** → `Provider<FortunasApi>` via Riverpod (`apiProvider` in `api/client.dart`).
- **Voice STT** → `SpeechController` (`ChangeNotifier`), wired into `VoiceFlow` via `addListener`.

We deliberately don't over-engineer with Bloc/Cubit/MVVM — the app is small enough that Riverpod + `setState` covers it cleanly.

### Theme tokens

`frontend/src/theme/tokens.css` → `mobile/lib/theme/tokens.dart`. The mapping is 1:1:

| CSS var | Dart constant |
|---|---|
| `--bg` | `FortunasColors.bg` |
| `--ink` | `FortunasColors.ink` |
| `--violet` | `FortunasColors.violet` |
| `--lime` | `FortunasColors.lime` |
| `--peach`, `--sky` | `FortunasColors.peach`, `.sky` |
| `--surface-soft` | `FortunasColors.surfaceSoft` |
| `box-shadow: 4px 4px 0 var(--ink)` | `popShadow()` helper |

Fonts (`SpaceGrotesk`, `Inter`, `JetBrainsMono`) loaded via `google_fonts` package — no asset bundling needed.

## What still runs on the React side (and why we keep it)

`frontend/` is **not deleted**. Reasons:
1. **Submission timeline safety net.** If Flutter device testing reveals an issue close to MIS Grant deadline, we can fall back to the React PWA which is already verified working.
2. **Cross-reference.** Some screens have subtle behaviors (the `humanizeError` strings, latency tracker semantics) that the Dart port can be diffed against.
3. **The backend doesn't care.** Both clients hit the same REST endpoints.

When Flutter is fully verified on device, `frontend/` can be moved to `_legacy_react/` or removed.

## Running it locally

### 1. Install Flutter SDK (one-time)

```
# Windows: https://docs.flutter.dev/get-started/install/windows
# After install, in a new shell:
flutter doctor
```

`flutter doctor` should show green checks for at minimum:
- Flutter (3.27+)
- Dart (3.6+)
- A device target (Chrome for web preview, Android emulator/device, or iOS sim on Mac)

### 2. Get dependencies

```
cd mobile
flutter pub get
```

This downloads:
- `flutter_riverpod`, `go_router`, `dio`, `intl`
- `speech_to_text`, `permission_handler` (voice flow)
- `shared_preferences` (history persistence)
- `google_fonts` (typography)
- `fl_chart` (briefing KPI cards — reserved for v2.3 deeper chart UI)

### 3. Configure backend URL

```
flutter run --dart-define=FORTUNAS_API=http://10.0.2.2:8000  # Android emulator
flutter run --dart-define=FORTUNAS_API=http://localhost:8000  # iOS simulator
flutter run --dart-define=FORTUNAS_API=http://192.168.40.6:8000  # Physical phone on same WiFi
```

If you omit `--dart-define`, the client defaults to `http://127.0.0.1:8000`.

### 4. Run

```
# Web preview (fastest — no emulator needed):
flutter run -d chrome

# Android emulator:
flutter run -d emulator-5554

# Physical Android device (USB debugging on):
flutter run

# iOS simulator (Mac only):
flutter run -d iPhone
```

### 5. Permissions on first voice run

Android: the OS dialog asks for microphone — tap Allow.
iOS: the OS dialog asks for **mic** and **speech recognition** — tap Allow on both. (Speech recognition is the second prompt, easy to miss.)

## Migration roadmap from design spec

The design hand-off proposed 4 phases (artboard "07"). Current status:

| Phase | Spec estimate | Status |
|---|---|---|
| Phase 1 · Setup (theme, folder, CI) | 3 hari | ✅ Done (this commit) |
| Phase 2 · Core screens (parity with React) | 1.5 minggu | ✅ Code done; needs device testing |
| Phase 3 · Voice (idle → success) | 1 minggu | ✅ Code done; needs device testing |
| Phase 4 · Polish + offline sync (Drift) + Play Store | 1 minggu | ⏳ Not started |

**Total spec estimate to Play Store 1.0:** ~4-5 weeks. The code piece is largely done; remaining is mostly device QA, polish, and store submission setup.

## Known follow-ups

- **`fl_chart` integration in `BriefingScreen`.** Currently the KPI cards extract a short value via regex from `top_findings`. For a stronger visualization (sparklines, bar charts), wire `fl_chart` once we expose more numeric series from the backend's analyses.
- **Offline sync queue.** Spec calls for Drift/SQLite + sync queue for transactions captured offline. Not yet implemented — voice transactions currently require live network.
- **Whisper fallback for STT.** Same v2.x roadmap item as the React PWA — full-local STT to close the privacy gap. The `whisper_flutter` package can be invoked via FFI when needed.
- **Push notifications** for daily briefing. PWA notification is partially supported; native Flutter version can use `flutter_local_notifications` for proper system notifications.

## Honest caveats

- **No device QA in this commit.** All code was written without running on an emulator or physical device. Compile-time syntax was checked via IDE diagnostics where possible, but pixel-level visual fidelity will need a real test pass.
- **Bottom nav vs `Scaffold.bottomNavigationBar` interactions.** The custom raised mic FAB uses `Transform.translate(offset: Offset(0, -22))` to clip out of the bar — verify on Android edge-to-edge gesture nav that nothing overlaps awkwardly.
- **Theme typography fallback.** `google_fonts` downloads on first run. If the device is offline at first launch, Flutter falls back to system fonts; subsequent launches use the cache. For grant demo reliability, run the app once with internet before showing it offline.
- **iOS speech permission flow** is two-stage (mic + speech_recognition). The `Info.plist` keys `NSMicrophoneUsageDescription` and `NSSpeechRecognitionUsageDescription` will need to be added when `ios/` is scaffolded by `flutter create .` (not done here — run `flutter create . --platforms=android,ios,web` inside `mobile/` before first build).
