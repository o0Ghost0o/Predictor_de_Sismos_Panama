# Predictor de Sismos Panama — imagen API + worker (misma imagen, distinto comando).
# Worker: mismo build, command override en docker-compose.yml.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

# libgomp1 = runtime OpenMP que exige lightgbm; curl = healthchecks del compose.
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Deps primero (cache de capas): solo se reinstalan si cambia pyproject/uv.lock.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Codigo + artefactos de inferencia (sin torch: servir no lo necesita).
COPY src/ ./src/
COPY models/ ./models/
COPY docs/ ./docs/
COPY data/alerts_sent.json data/last_ingest.json data/live_events.jsonl data/tasks.json ./data/
COPY data/raw/quakes_full.parquet ./data/raw/quakes_full.parquet
COPY data/processed/dataset_full.parquet ./data/processed/dataset_full.parquet
COPY data/forecast_log.parquet ./data/forecast_log.parquet
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8001

CMD ["uvicorn", "src.serve.app:app", "--host", "0.0.0.0", "--port", "8001"]
