# `_legacy/` — Pre-mobile-redesign UI

These files are the **v1 desktop UI** of Fortunas AI, kept for two reasons:

1. **Reference for pre-auth backend wiring** — `App.legacy.jsx` shows the exact fetch shape, error handling (`humanizeError`), latency tracking (`fortunas.latencies.v1`), and multi-section briefing rendering against the same backend (`/ask`, `/briefing`, `/report/latest`). Note: these calls predate auth — the production client is `frontend/` itself now (ADR-0002).
2. **Rollback safety** — kept as a historical fallback reference near the MIS Grant deadline.

**These files are NOT imported by any current route.** They live outside the build graph. Vite tree-shakes them away at build time. Safe to leave; do not build new features on them.

The new entry point is `frontend/src/App.jsx` (router root) + `frontend/src/screens/` + `frontend/src/voice/`.
