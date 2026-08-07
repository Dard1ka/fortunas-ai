# `_legacy/` — Pre-mobile-redesign UI

These files are the **v1 desktop UI** of Fortunas AI, kept for two reasons:

1. **Reference for backend wiring** — `App.legacy.jsx` shows the exact fetch shape, error handling (`humanizeError`), latency tracking (`fortunas.latencies.v1`), and multi-section briefing rendering that the new mobile screens need to replicate against the same backend (`/ask`, `/briefing`, `/report/latest`).
2. **Rollback safety** — if the new mobile UI hits a release-blocking bug close to MIS Grant deadline, we can temporarily restore this entry point.

**These files are NOT imported by any current route.** They live outside the build graph. Vite tree-shakes them away at build time. Safe to leave; safe to delete after v2 mobile is locked in.

The new entry point is `frontend/src/App.jsx` (router root) + `frontend/src/screens/` + `frontend/src/voice/`.
