# `frontend/` — Archive / Design Reference (NOT the shipping client)

This React + Vite app is **archived**. It is **not** the app Fortunas AI ships to UMKM users.

## What actually ships

The shipping client is the **Flutter app in `mobile/`**, released as a **PWA** (installable,
service-worker-backed web app served same-origin behind nginx/HTTPS). See
[`docs/handoff/day-16.md`](../docs/handoff/day-16.md) for the current PWA/responsive-shell
architecture, and the repository root [`README.md`](../README.md) for the overall project
layout.

## Why this folder is kept instead of deleted

This app's 6 screens and its Web Speech API voice flow
(`src/voice/useSpeechRecognition.js`) remain the **design reference** the Flutter UMKM
screens (`mobile/lib/screens/`, 13 screens) were built against. Deleting it would remove that
reference with no replacement, so it stays in the repo as a read-only historical artifact.

## What this means in practice

- **Not built.** No CI job runs `npm run build` or `vite build` against this folder.
- **Not tested.** No CI job runs tests against this folder.
- **Not gated by CI** at all — `.github/workflows/ci.yml` has no job referencing `frontend/`.
- Nothing here should be assumed to compile against current dependency versions; `package.json`
  and `node_modules` are exactly as they were left, not maintained going forward.

Do not build product features on top of this app. If you need to compare a Flutter UMKM screen
against its original design intent, read the matching screen under `src/screens/` here, but make
any actual UI changes in `mobile/lib/screens/`.
