#!/bin/bash
# ============================================================
#  Fortunas AI — Backend Entrypoint
#  1. Wait for Ollama to be ready (ONLY when LLM_PROVIDER=ollama is selected)
#  2. Run knowledge base ingest (only on first boot)
#  3. Start uvicorn
# ============================================================

set -e

echo "================================================"
echo " Fortunas AI Backend Starting..."
echo "================================================"

# ── 1. Wait for Ollama — ONLY if it's the selected provider ──
# Default matches app/llm_provider.py's get_provider() default ("gemini"), so
# this never disagrees with what the app itself will actually use. Ollama is
# archived behind docker-compose's `profiles: ["archive"]` (Task 1c) — under
# the default provider there is no `ollama` service in the stack to wait for,
# so skip the wait instead of blocking ~2.5 minutes (30 retries x 5s) for a
# host that will never come up.
LLM_PROVIDER="${LLM_PROVIDER:-gemini}"
LLM_PROVIDER_LOWER="$(echo "$LLM_PROVIDER" | tr '[:upper:]' '[:lower:]')"

if [ "$LLM_PROVIDER_LOWER" = "ollama" ]; then
    OLLAMA_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
    echo "[1/3] LLM_PROVIDER=ollama — waiting for Ollama at ${OLLAMA_URL}..."

    MAX_RETRIES=30
    COUNT=0
    until curl -sf "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; do
        COUNT=$((COUNT + 1))
        if [ "$COUNT" -ge "$MAX_RETRIES" ]; then
            echo "⚠  Ollama not ready after ${MAX_RETRIES} attempts. Starting anyway..."
            break
        fi
        echo "   ... attempt ${COUNT}/${MAX_RETRIES}, retrying in 5s"
        sleep 5
    done
    echo "✓ Ollama is ready."
else
    echo "[1/3] LLM_PROVIDER=${LLM_PROVIDER} — skipping Ollama wait (not selected)."
fi

# ── 2. Run knowledge base ingest (only if chroma_db empty) ──
CHROMA_PATH="${CHROMA_DB_PATH:-/data/chroma_db}"
MARKER="${CHROMA_PATH}/.ingest_done"

if [ ! -f "$MARKER" ]; then
    echo "[2/3] First boot — running knowledge base ingest..."
    cd /app
    python -m app.knowledge.ingest
    touch "$MARKER"
    echo "✓ Knowledge base ingest complete."
else
    echo "[2/3] Knowledge base already indexed. Skipping ingest."
fi

# ── 3. Start FastAPI ─────────────────────────────────────────
echo "[3/3] Starting FastAPI (uvicorn)..."
cd /app
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info
