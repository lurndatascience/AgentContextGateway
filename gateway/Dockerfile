FROM python:3.12-slim
WORKDIR /srv
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY gateway/app ./app
COPY data ./data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=5 CMD curl -fsS http://localhost:8000/health || exit 1
# Ingest is idempotent, so every start reconciles the corpus before serving.
CMD ["sh", "-c", "python -m app.ingest && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
