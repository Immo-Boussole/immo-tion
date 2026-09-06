# ── Immo-Tion Multi-Arch Production Dockerfile ─────────────────────────
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_PORT=8085 \
    DATA_DIR=/data

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ app/
COPY static/ static/
COPY templates/ templates/
COPY LICENSE .
COPY README.md .

# Create non-root runtime user and data directory
RUN useradd -u 1000 -U -s /bin/bash -m appuser \
    && mkdir -p /data/uploads \
    && chown -R appuser:appuser /app /data

USER appuser

VOLUME ["/data"]

EXPOSE 8085

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${APP_PORT}/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8085"]
