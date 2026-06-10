# ============================================================
#  Fortunas AI — Makefile
#  Shortcut commands for Docker operations
#
#  Usage: make <target>
#  Example: make up
# ============================================================

.PHONY: help up down logs build restart shell-backend shell-frontend \
        pull-model ingest clean dev dev-down ps zip

# ── Default target ───────────────────────────────────────────
help:
	@echo ""
	@echo "  Fortunas AI — Docker Commands"
	@echo "  ─────────────────────────────────────────────────"
	@echo "  make up            Build + start all services (production)"
	@echo "  make up-d          Start in background (detached)"
	@echo "  make down          Stop all services"
	@echo "  make down-v        Stop + delete all volumes"
	@echo "  make build         Rebuild images without starting"
	@echo "  make restart       Restart all services"
	@echo "  make logs          Stream all logs"
	@echo "  make logs-backend  Stream backend logs only"
	@echo "  make ps            Show running containers"
	@echo ""
	@echo "  make dev           Start in DEVELOPMENT mode (hot reload)"
	@echo "  make dev-down      Stop development stack"
	@echo ""
	@echo "  make pull-model    Pull qwen3:8b into Ollama (run once)"
	@echo "  make ingest        Re-run knowledge base ingest manually"
	@echo "  make shell-backend Open shell inside backend container"
	@echo "  make clean         Remove stopped containers + dangling images"
	@echo ""
	@echo "  make zip           Package fortunas-ai.zip for submission"
	@echo "                     (excludes CLAUDE.md, .git, node_modules, credentials, etc.)"
	@echo ""

# ── Production ───────────────────────────────────────────────
up:
	docker compose up --build

up-d:
	docker compose up --build -d

down:
	docker compose down

down-v:
	docker compose down -v

build:
	docker compose build

restart:
	docker compose restart

# ── Logs ─────────────────────────────────────────────────────
logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-frontend:
	docker compose logs -f frontend

logs-ollama:
	docker compose logs -f ollama

# ── Status ───────────────────────────────────────────────────
ps:
	docker compose ps

# ── Development ──────────────────────────────────────────────
dev:
	docker compose -f docker-compose.dev.yml up --build

dev-down:
	docker compose -f docker-compose.dev.yml down

# ── Ollama model ─────────────────────────────────────────────
pull-model:
	docker compose exec ollama ollama pull qwen3:8b
	@echo "✓ Model ready. Verify: make model-list"

model-list:
	docker compose exec ollama ollama list

# ── Knowledge base ───────────────────────────────────────────
ingest:
	docker compose exec backend python -m app.knowledge.ingest
	@echo "✓ Ingest complete."

# ── Shell access ─────────────────────────────────────────────
shell-backend:
	docker compose exec backend bash

shell-frontend:
	docker compose exec frontend sh

shell-ollama:
	docker compose exec ollama bash

# ── Cleanup ──────────────────────────────────────────────────
clean:
	docker compose down
	docker image prune -f
	docker container prune -f
	@echo "✓ Cleanup done."

# ── Submission packaging ─────────────────────────────────────
# Build a clean zip for grant submission. Excludes:
#   - CLAUDE.md      (assistant-only context, not part of source)
#   - .git/          (git history)
#   - node_modules/  (frontend deps)
#   - credentials/   (service account JSON)
#   - .env           (secrets)
#   - .venv/         (Python venv)
#   - chroma_db/     (locally-built vector index)
#   - frontend/dist  (built artifacts, regenerated on install)
#   - _decoded_*     (mockup exploration artifacts)
#   - docs/          (internal overview PDF + Claude plan files — not for handoff)
#   - package.ps1    (packaging script itself — teammate uses `make zip`)
#
# Run only when explicitly preparing a submission archive.
zip:
	@echo "Packaging fortunas-ai.zip for submission..."
	@rm -f fortunas-ai.zip
	@cd .. && zip -r fortunas-ai/fortunas-ai.zip fortunas-ai \
		-x "fortunas-ai/CLAUDE.md" \
		-x "fortunas-ai/.git/*" \
		-x "fortunas-ai/node_modules/*" \
		-x "fortunas-ai/frontend/node_modules/*" \
		-x "fortunas-ai/credentials/*" \
		-x "fortunas-ai/.env" \
		-x "fortunas-ai/.venv/*" \
		-x "fortunas-ai/chroma_db/*" \
		-x "fortunas-ai/frontend/dist/*" \
		-x "fortunas-ai/_decoded_assets/*" \
		-x "fortunas-ai/_decoded_mobile.html" \
		-x "fortunas-ai/fortunas-ai.zip" \
		-x "fortunas-ai/docs/*" \
		-x "fortunas-ai/package.ps1" \
		-x "fortunas-ai/mobile/.dart_tool/*" \
		-x "fortunas-ai/mobile/build/*" \
		-x "fortunas-ai/mobile/pubspec.lock"
	@echo "✓ fortunas-ai.zip ready."
	@echo "  Verify CLAUDE.md is absent:"
	@unzip -l fortunas-ai.zip | grep -i claude.md || echo "  (none — good)"
