# 07 · Operación y ética

## Servicios (solo `uv` + `bun`; npm/pip proscritos)
`make up` levanta todo (api :8001 + worker + web :3001 + loops); `make down`, `make status`, `make logs`.
- FastAPI `:8001` (`uv run uvicorn src.serve.app:app --port 8001`): `/health /zones /risk /risk/{zona}?date= /backtest /prospective /aftershock /ingesta` + **`ws://:8001/ws/live`** (snapshot + push de sismos nuevos cada 5s).
- Nuxt `:3001` (`cd web && bun run dev`): 7 páginas, proxy Nitro al API, feed USGS en vivo.
- Python siempre vía `uv run` (lockfile `uv.lock`); JS siempre vía `bun` (`bun.lock`).
- Nota: puertos 3000/8000 los ocupan otras apps del equipo.

## Mini-CSEP (protocolo)
1. Diario: `ingest 30d → weather mes → build → prospective issue`.
2. `prospective score` califica ventanas cerradas contra `quakes_full` (acierto/omitido/falsa/correcto-negativo).
3. Regla: el log nunca se reescribe; los experimentos no promueven el bundle sin validación.

## Tareas Dramatiq (alto flujo)
Broker Redis local (`redis://127.0.0.1`, DB 0 colas / DB 1 resultados).
Actores en `src/tasks/actors.py`, colas `io` (ingestas), `default` (build/prospective), `live` (polls + alertas).
Worker: `uv run dramatiq src.tasks.actors --processes 1 --threads 4` (un solo worker, todas
las colas; probado io+live+default en paralelo).
Lección: NO partir en workers con `--threads 1` — la cola `default` muere de hambre
(mensajes a XQ sin procesarse); tampoco mezclar torch+lightgbm en un proceso (segfault libomp).

## Alertas RT (Telegram)
`src/notify/telegram.py` + actor `alert_new` (cola `live`, umbral M4.5, dedupe `data/alerts_sent.json`).
Se dispara solo al anexar eventos frescos (USGS o IGC). Sin credenciales = dry-run en log.
Credenciales: env `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` o `data/telegram.json` (no commitear).
Carriles: `live_poll` USGS 5min + `fast_poll` IGC/RSS 60s (ambos auto-reagendados).
API: `POST /tasks/ingest?start=&end=` · `POST /tasks/live-start` (ambos carriles) ·
`POST /tasks/alert-test` · `POST /tasks/prospective` · `GET /tasks/{message_id}`.

## Live de baja dilatación
`uv run python -m src.ingest.live_loop --interval 300` (o actor `live_poll`): sondea USGS (ventana 3h, M4+),
anexa por `id` a `quakes_full` y escribe `data/last_ingest.json`.
Cada evento nuevo también se anexa a `data/live_events.jsonl`, que el websocket
sigue por offset (sin reentrenar, sin Redis — proceso liviano para 8GB RAM).
Retraso típico ≈ 60–70 min (latencia del propio USGS, no nuestra).
El dial ETAS lee el catálogo al vuelo: un M nuevo mueve p24 en minutos, sin reentrenar.
Estado en `GET /ingesta` y página `/ingesta`.

## Docs como fuente única
`docs/*.md` se renderiza en la web vía `marked` (`/docs/...`, `server/api/docs.get.ts`).
Se escribe una vez en `docs/`, se lee en la página.

## Ética
Probabilidades, no alarmas. Escala topada en 6 con explicación pública.
Fallos (M7.7) publicados junto a aciertos. Sin SMS masivos en PoC.
