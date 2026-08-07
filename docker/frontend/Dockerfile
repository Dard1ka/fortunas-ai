# ============================================================
#  Fortunas AI — Frontend Dockerfile (multi-stage)
#  Builds the PRODUCTION React client (frontend/ — ADR-0002).
#
#  Stage 1 (builder): Node 22 — install deps + build React app
#                     (Vite 8 requires Node ^20.19 || >=22.12; pin 22 to
#                     match the CI job "Frontend (lint + test + build)")
#  Stage 2 (runner):  nginx:alpine — serve the built dist/
# ============================================================

# ── Stage 1: Build ───────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

# Install dependencies (cached layer — only re-runs if package files change)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent

# Copy source and build
COPY frontend/ .
RUN npm run build
# Output: /app/dist/

# ── Stage 2: Serve with nginx ────────────────────────────────
FROM nginx:alpine AS runner

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom nginx config
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/fortunas.conf

# Copy built React app
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
