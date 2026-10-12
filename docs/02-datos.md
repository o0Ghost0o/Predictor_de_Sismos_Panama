# 02 · Datos y fuentes

## Fuentes
| Fuente | Qué | Acceso |
|---|---|---|
| USGS FDSN Event API | Catálogo sísmico (tiempo, lat, lon, prof, mag) | `src/ingest/api_usgs.py` |
| Open-Meteo Archive | Clima histórico horario → diario (t2m, humedad, presión, lluvia) | `src/ingest/weather.py` (por año) |
| Open-Meteo Forecast | Clima operativo + `past_days` (auditoría) | API directa |
| USGS GeoJSON feeds | Sismicidad en vivo (4.5+día, 2.5+semana) | `web/server/api/live.get.ts` |
| IGC-UPA | Lista pública M1.7+ ([link](https://sismosgeociencias.up.ac.pa/)), scraper `igc_up.py`, actor `ingest_igc` | Sin archivo: solo últimos ~7d; 175 ev/sem, 39 sub-M4; dedupe 120s/0.3° vs USGS |
| IGC-Wayback | 3 snapshots (nov-2025×2, ene-2026) → 32 eventos (21 sub-M4), enero 0→15 | Límite: no hay más snapshots; feb–sep sub-M4 irrecuperable por ahora |

## Cobertura auditada (oct-2026, M4+ por mes, nuestro vs USGS)
2024-06 3/3 · 2024-12 3/3 · 2025-02 0/0 · 2025-06 3/3 · 2025-09 0/0 · 2025-12 2/2 ·
2026-02 4/3 · 2026-05 3/3 · 2026-08 2/2 · 2026-09 2/2. Sin lagunas: los ceros son quietud real.
El gap ene–sep 2026 fue backfill (resuelto con `resync_catalog`).

## Volúmenes (verificado oct-2026)
- `quakes_full`: **1,622 eventos M4.0–7.7 (1970–2026)**, 72KB. Completitud USGS en Panamá ≈ M4.0
  (2024: 39 eventos tanto en M≥2.5 como M≥4.0 → bajo M4 no se registra).
- `weather_full`: **103,660 zone-days**, 2.3MB. `dataset_hybrid`: **103,685 filas**, 2.5MB.
- Total datos ≈ 5MB. Crece ~200KB/año. Lo pesado es `.venv` (~656MB), no los datos.

## Zonas (disjuntas, 6.8–10N / 83.5–77W) — `src/features/zones.py`
BOCAS (Caribe oeste) · CHIRIQUI (Pacífico oeste) · CENTRAL · AZUERO · DARIEN.
Positivos 7d: CHIRIQUI 3,625 (17.7%) · DARIEN 1,903 · BOCAS 706 · AZUERO 583 · CENTRAL 309 (1.5%).

## Ingesta recurrente
Lotes anuales + cron diario propuesto: `api_usgs` 30d → `weather` mes → `build` →
`prospective issue/score`. Detalle en `07-operacion.md`.
