FROM python:3.11-slim
WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY collecteur_requirements.txt .
RUN pip install --no-cache-dir -r collecteur_requirements.txt

COPY collecteur.py .
RUN mkdir -p /data

# Create non-root user
RUN useradd -m -u 1000 collecteur && chown -R collecteur:collecteur /app /data

USER collecteur

VOLUME /data
EXPOSE 9000

ENV COLLECTEUR_DATA=/data/collecteur_data.json
ENV COLLECTEUR_TOKENS=/data/collecteur_tokens.json

HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:9000/health || exit 1

CMD ["uvicorn", "collecteur:app", "--host", "0.0.0.0", "--port", "9000", "--workers", "1"]
