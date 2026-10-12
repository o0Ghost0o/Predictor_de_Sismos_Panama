# Predictor de Sismos Panamá — PoC Research

Probabilistic forecasting (NOT deterministic prediction): `P(M4+ in next 7 days)` per zone.

Zones (disjoint, cover 6.8–10.0N, 83.5–77W):
- BOCAS (Caribe Oeste), CHIRIQUI (Pacífico Oeste), CENTRAL, AZUERO, DARIEN

## Quickstart (Mac local) — solo `uv` y `bun`, nada de npm/pip
```bash
uv sync                                  # crea .venv + uv.lock
# 1-month spike
uv run python -m src.ingest.api_usgs --start 2025-09-01 --end 2025-10-01 --out data/raw/quakes_spike.parquet
uv run python -m src.ingest.weather --start 2025-09-01 --end 2025-10-01 --out data/raw/weather_spike.parquet
uv run python -m src.features.build --quakes data/raw/quakes_spike.parquet --weather data/raw/weather_spike.parquet --out data/processed/dataset_spike.parquet
# full
uv run python -m src.ingest.api_usgs --start 1970-01-01 --end 2026-01-01 --out data/raw/quakes_full.parquet
uv run python -m src.models.train --input data/processed/dataset_full.parquet
uv run uvicorn src.serve.app:app --port 8001
```

Ethics: research probabilities only. No public alert SMS in PoC.

## Web (Nuxt 4 + Tailwind, ligero: sin UI lib ni charts lib)
```bash
cd web && bun install && bun run dev   # http://localhost:3001 (3000 suele estar ocupado)
```
Páginas: `/` (por qué existe + niveles live) · `/pronostico` (tester por fecha) ·
`/comparativa` (tabla modelos + backtest live) · `/alertas` (escala 3–6 + log mini-CSEP) ·
`/estudios` (hipótesis y veredictos + referencias CSEP/ETAS/RECAST) · `/ingesta`
(lotes, cron recurrente, sismicidad USGS en vivo filtrada a Panamá).
Proxy Nitro → FastAPI `:8001`; los feeds USGS se filtran al bbox 6.5–10N/83.5–77W en `server/api/live.get.ts`.
