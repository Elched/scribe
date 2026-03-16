# ── SCRIBE — Dockerfile (version open-source) ─────────────────────────────
FROM python:3.11-slim

LABEL maintainer="github.com/nocomp/scribe"
LABEL description="SCRIBE — Main courante de crise hospitalière"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SCRIBE_DATA_DIR=/data

WORKDIR /app

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code applicatif
COPY . .

# Dossier de données persistantes (base SQLite + uploads + config.js généré)
RUN mkdir -p /data/uploads /data/db && \
    ln -sf /data/uploads /app/uploads && \
    ln -sf /data/db/scribe.db /app/scribe.db 2>/dev/null || true

# Script d'entrée
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
