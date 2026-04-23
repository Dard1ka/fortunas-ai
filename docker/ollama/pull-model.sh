#!/bin/bash
# ============================================================
#  Pull Qwen3:8b into the running Ollama container.
#  Run this ONCE after `docker compose up ollama` completes.
#
#  Usage:
#    bash docker/ollama/pull-model.sh
#  Or via Makefile:
#    make pull-model
# ============================================================

MODEL="${OLLAMA_MODEL:-qwen3:8b}"
OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"

echo "Pulling model: ${MODEL}"
echo "Ollama endpoint: ${OLLAMA_URL}"
echo ""

docker compose exec ollama ollama pull "${MODEL}"

echo ""
echo "✓ Model ${MODEL} is ready."
echo "  Verify with: docker compose exec ollama ollama list"
