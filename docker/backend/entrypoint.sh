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

# ── 1. Wait for Ollama — ONLY if the app would actually route to it ──
# Mirrors app/llm_provider.py's routing exactly, not just its default:
# get_provider() does os.getenv("LLM_PROVIDER", "gemini").strip().lower(), and
# llm_generate() special-cases only "openai" and "gemini" — everything else
# (a typo, an empty string, or "ollama" itself) falls through a bare `else`
# into _ollama_generate(). So the gate below skips the wait for openai/gemini
# and waits for anything else, instead of matching "ollama" specifically —
# that keeps it correct even for values neither side pins in practice.
#
# `${LLM_PROVIDER-gemini}` (no colon) applies the default only when the
# variable is completely unset, matching os.getenv's own default behavior;
# an explicitly empty `LLM_PROVIDER=` is left empty, same as Python sees it.
LLM_PROVIDER="${LLM_PROVIDER-gemini}"
LLM_PROVIDER_TRIMMED="$(printf '%s' "$LLM_PROVIDER" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
LLM_PROVIDER_LOWER="$(printf '%s' "$LLM_PROVIDER_TRIMMED" | tr '[:upper:]' '[:lower:]')"

if [ "$LLM_PROVIDER_LOWER" = "openai" ] || [ "$LLM_PROVIDER_LOWER" = "gemini" ]; then
    echo "[1/3] LLM_PROVIDER=${LLM_PROVIDER} — skipping Ollama wait (not selected)."
else
    OLLAMA_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
    echo "[1/3] LLM_PROVIDER=${LLM_PROVIDER} — waiting for Ollama at ${OLLAMA_URL}..."

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
