# ============================================================
#  Fortunas AI — Makefile
#  Shortcut commands for Docker operations
#
#  Usage: make <target>
#  Example: make up
# ============================================================

.PHONY: help up down logs build restart shell-backend shell-frontend \
        pull-model ingest clean dev dev-down ps

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
