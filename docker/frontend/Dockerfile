# ============================================================
#  Fortunas AI — Frontend Dockerfile (multi-stage)
#
#  Stage 1 (builder): Node 20 — install deps + build React app
#  Stage 2 (runner):  nginx:alpine — serve the built dist/
# ============================================================

# ── Stage 1: Build ───────────────────────────────────────────
FROM node:20-alpine AS builder

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
