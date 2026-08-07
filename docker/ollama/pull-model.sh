#!/bin/bash
# ============================================================
#  ARSIP — LLM produksi = Gemini 2.5 Flash via API (lihat app/llm_provider.py).
#  Script ini hanya relevan kalau kamu sengaja menjalankan jalur lokal dengan
#  LLM_PROVIDER=ollama. Service ollama ada di profile "archive" (lihat
#  docker-compose.yml), jadi tidak ikut `docker compose up` biasa.
#
#  Pull Qwen3:8b into the running Ollama container.
#  Run this ONCE after `docker compose --profile archive up ollama` completes.
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

docker compose --profile archive exec ollama ollama pull "${MODEL}"

echo ""
echo "✓ Model ${MODEL} is ready."
echo "  Verify with: docker compose --profile archive exec ollama ollama list"
