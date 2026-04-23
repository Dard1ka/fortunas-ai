# ============================================================
#  Fortunas AI — Backend Dockerfile
#  Base: python:3.11-slim
#  Exposes: port 8000 (FastAPI / uvicorn)
# ============================================================

FROM python:3.11-slim

# ── System dependencies ─────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies first (cache layer) ─────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Copy application source ──────────────────────────────────
COPY app/ ./app/

# ── Entrypoint script ────────────────────────────────────────
COPY docker/backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ── Create directories for mounted volumes ───────────────────
RUN mkdir -p /data/chroma_db /app/app/data /app/credentials

# ── Expose port ──────────────────────────────────────────────
EXPOSE 8000

# ── Health check ─────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
