from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from functools import lru_cache
from contextlib import asynccontextmanager
import pandas as pd, pickle

def _edad_archivo_min(path: str, clave: str = "ts") -> float | None:
    """Edad en minutos de un stamp JSON; None si no existe o es ilegible."""
    import json
    from datetime import datetime, timezone
    try:
        ts = json.load(open(path))[clave]
        return (datetime.now(timezone.utc) - datetime.fromisoformat(ts)).total_seconds() / 60
    except Exception:
        return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-arranque de ingesta en vivo: en produccion nadie pulsa /tasks/live-start
    # tras cada despliegue/reinicio. El heartbeat lo toca cada pasada de live_poll;
    # solo encolamos si no hay latido reciente (los loops se auto-reagendan solos).
    # Nunca tumba el arranque del API.
    latido = _edad_archivo_min("data/live_heartbeat.json")
    if latido is not None and latido < 10:
        yield
        return
    edad = _edad_archivo_min("data/last_ingest.json")
    if edad is None or edad > 15:
        try:
            from src.tasks.actors import live_poll, fast_poll, resync_catalog
            live_poll.send(); fast_poll.send()
            if edad is None or edad > 7 * 24 * 60:
                resync_catalog.send()  # backfill tardio USGS, caro: solo si >7d
            print(f"[boot] loops de ingesta encolados (edad stamp: {edad})", flush=True)
        except Exception as e:
            print(f"[boot] ingesta auto no disponible ({e}); usar POST /tasks/live-start",
                  flush=True)
    yield

app = FastAPI(title="Sismos Panama PoC", lifespan=lifespan)

@lru_cache
def _load():
    bundle = pickle.load(open("models/lgbm_full.pkl", "rb"))
    df = pd.read_parquet("data/processed/dataset_full.parquet")
    df["date"] = pd.to_datetime(df["date"])
    return bundle, df

def nivel_texto(p4: float, p5: float, p6: float):
    if p6 >= 0.30:
        return 6, "🔴 Alto — posible sismo fuerte (M6+). Revisa tu plan familiar, no entres en pánico."
    if p5 >= 0.35:
        return 5, "🟠 Moderado-Alto — posible sismo intermedio (M5+). Atento a réplicas."
    if p4 >= 0.50:
        return 4, "🟡 Moderado — posible sismo leve (M4+). Actividad habitual de Panamá."
    return 3, "🟢 Tranquilo — baja probabilidad esta semana."

@app.get("/health")
def health(): return {"ok": True}

@app.get("/zones")
def zones():
    _, df = _load()
    return {"zones": sorted(df.zone.unique().tolist()),
            "date_min": str(df.date.min().date()), "date_max": str(df.date.max().date())}

@lru_cache
def _daily():
    import pickle
    return pickle.load(open("models/daily_7x.pkl", "rb"))

def _predict(zone: str, date: str | None):
    bundle, df = _load()
    feats = bundle["features"]
    zone = zone.upper()
    if date is None:
        # Fila viva de hoy (catalogo + colas del dataset): las replicas M4/M5
        # entran al nivel el mismo dia. Si falla, ultima fila versionada.
        try:
            from src.features.live_row import live_rows
            lv = live_rows()
            row = lv[lv.zone == zone].iloc[-1:]
            assert len(row) == 1 and all(c in row.columns for c in feats)
        except Exception:
            row = df[df.zone == zone].sort_values("date").iloc[-1:]
    else:
        d = pd.to_datetime(date)
        rows = df[(df.zone == zone) & (df.date == d)]
        if len(rows) == 0:
            rows = df[(df.zone == zone) & (df.date <= d)].sort_values("date").tail(1)
        row = rows
    if len(row) == 0: return {"error": f"no data for {zone} {date}"}
    r = row.iloc[0]
    X = row[feats].fillna(0)
    p4 = float(bundle["label_M4_7d"].predict_proba(X)[:, 1][0])
    p5 = float(bundle["label_M5_7d"].predict_proba(X)[:, 1][0])
    p6 = float(bundle["label_M6_7d"].predict_proba(X)[:, 1][0])
    if "cal" in bundle:  # recalibracion isotonica (val): p cruda -> p honesta
        import numpy as np
        p4 = float(bundle["cal"]["label_M4_7d"].predict([p4])[0])
        p5 = float(bundle["cal"]["label_M5_7d"].predict([p5])[0])
        p6 = float(bundle["cal"]["label_M6_7d"].predict([p6])[0])
    niv, txt = nivel_texto(p4, p5, p6)
    try:
        db = _daily()
        Xd = row[db["features"]].fillna(0).values.reshape(1, -1)
        curva = [round(float(db["daily"][k].predict_proba(Xd)[:, 1][0]), 4) for k in range(1, 8)]
        curva5 = [round(float(db["daily5"][k].predict_proba(Xd)[:, 1][0]), 4) for k in range(1, 8)] if "daily5" in db else []
    except Exception:
        curva, curva5 = [], []
    try:
        from src.models.aftershock import m6_curve
        curva6 = m6_curve(zone, r["date"].date().isoformat())
    except Exception:
        curva6 = []
    # bandas altas por Gutenberg-Richter (b=1): visibles solo si >=1%
    gr = {m: round(p6 / (10 ** (m - 6)), 7) for m in (7, 8, 9, 10)}
    return {"zone": zone, "date": str(r["date"].date()),
            "p_M4_7d": round(p4, 4), "p_M5_7d": round(p5, 4), "p_M6_7d": round(p6, 4),
            "bandas_gr": {str(m): v for m, v in gr.items() if v >= 0.01},
            "curva_diaria": curva, "curva_m5": curva5, "curva_m6": curva6,
            "nivel": niv, "mensaje": txt,
            "observed_M4_next7d": (None if pd.isna(r["label_M4_7d"])
                                   else int(r["label_M4_7d"]))}

@app.get("/backtest")
def backtest():
    import numpy as np
    bundle, df = _load()
    feats = bundle["features"]
    df = df.sort_values("date")
    dates = df.date.unique(); n = len(dates); te = dates[int(.85 * n):]
    t = df[df.date.isin(te)].copy()
    for col in ["label_M4_7d", "label_M5_7d", "label_M6_7d"]:
        p = bundle[col].predict_proba(t[feats].fillna(0))[:, 1]
        if "cal" in bundle:
            p = bundle["cal"][col].predict(p)
        t["pred_" + col] = p
    per_zone = []
    thr = {}
    for z, g in t.groupby("zone"):
        th = float(g.pred_label_M4_7d.quantile(0.90))  # alerta el 10% top por zona
        thr[z] = round(th, 3)
        al = g["pred_label_M4_7d"] >= th
        per_zone.append({"zone": z, "n": int(len(g)), "positivos": int(g.label_M4_7d.sum()),
            "umbral": round(th, 3),
            "aciertos": int(((al == 1) & (g.label_M4_7d == 1)).sum()),
            "falsas_alarmas": int(((al == 1) & (g.label_M4_7d == 0)).sum()),
            "omitidos": int(((al == 0) & (g.label_M4_7d == 1)).sum())})
    notable = t[t.label_M4_7d == 1].groupby("zone", as_index=False).tail(3)
    events = [{"zone": r.zone, "date": str(r.date.date()),
               "p4": round(float(r.pred_label_M4_7d), 3),
               "p5": round(float(r.pred_label_M5_7d), 3),
               "p6": round(float(r.pred_label_M6_7d), 3)} for r in notable.itertuples()]
    return {"periodo": f"{str(te[0].date())} → {str(te[-1].date())}",
            "umbral_alerta": "top 10% semanas más riesgosas por zona (probs calibradas)",
            "por_zona": per_zone, "ultimos_eventos_acertar": events}

@app.websocket("/ws/live")
async def ws_live(ws: WebSocket):
    """Push de sismos nuevos: snapshot + tail de data/live_events.jsonl cada 5s."""
    import asyncio, json, os
    await ws.accept()
    try:
        await ws.send_json({"tipo": "snapshot", "ingesta": ingesta()})
    except Exception:
        pass
    pos = os.path.getsize("data/live_events.jsonl") if os.path.exists("data/live_events.jsonl") else 0
    try:
        while True:
            await asyncio.sleep(5)
            if not os.path.exists("data/live_events.jsonl"):
                continue
            size = os.path.getsize("data/live_events.jsonl")
            if size < pos:
                pos = 0  # rotado
            if size > pos:
                with open("data/live_events.jsonl") as f:
                    f.seek(pos)
                    for line in f:
                        line = line.strip()
                        if line:
                            await ws.send_json({"tipo": "sismo", **json.loads(line)})
                    pos = f.tell()
    except WebSocketDisconnect:
        pass

def _reg(mid: str, actor: str, queue: str):
    import json, os
    p = "data/tasks.json"
    reg = json.load(open(p)) if os.path.exists(p) else {}
    import datetime
    reg[mid] = {"actor": actor.split(".")[-1], "queue": queue, "ts": datetime.datetime.now().isoformat()}
    json.dump(reg, open(p, "w"))

@app.post("/tasks/ingest")
def task_ingest(start: str, end: str):
    from src.tasks.actors import ingest_quakes
    m = ingest_quakes.send(start, end)
    _reg(m.message_id, m.actor_name, m.queue_name)
    return {"message_id": m.message_id, "queue": "io"}

@app.post("/tasks/live-start")
def task_live_start():
    from src.tasks.actors import live_poll, fast_poll
    a = live_poll.send(); b = fast_poll.send()
    _reg(a.message_id, a.actor_name, a.queue_name)
    _reg(b.message_id, b.actor_name, b.queue_name)
    return {"message_ids": [a.message_id, b.message_id],
            "nota": "USGS 5min + IGC/RSS 60s, auto-reagendados"}

@app.post("/tasks/alert-test")
def task_alert_test():
    from src.tasks.actors import alert_new
    m = alert_new.send([{"id": "test-rt", "time": "2026-10-10", "lat": 7.5, "lon": -80.5,
                         "depth": 10, "mag": 5.0, "place": "PRUEBA canal de alertas"}])
    _reg(m.message_id, m.actor_name, m.queue_name)
    return {"message_id": m.message_id, "nota": "sin credenciales Telegram = dry-run en log"}

@app.post("/tasks/refit-etas")
def task_refit_etas(trigger: str = "manual"):
    from src.tasks.actors import refit_etas
    m = refit_etas.send(trigger)
    _reg(m.message_id, m.actor_name, m.queue_name)
    return {"message_id": m.message_id, "queue": "default"}

@app.post("/tasks/prospective")
def task_prospective():
    from src.tasks.actors import prospective_issue
    m = prospective_issue.send()  # al terminar, el actor encadena score
    _reg(m.message_id, m.actor_name, m.queue_name)
    return {"message_ids": [m.message_id]}

@app.get("/tasks/{message_id}")
def task_status(message_id: str):
    try:
        import json
        from types import SimpleNamespace
        from dramatiq.results.backends import RedisBackend
        import redis as redislib
        reg = json.load(open("data/tasks.json"))
        e = reg[message_id]
        stub = SimpleNamespace(queue_name=e["queue"], actor_name=e["actor"], message_id=message_id)
        from src.tasks.broker import RESULTS_URL
        key = RedisBackend(url=RESULTS_URL).build_message_key(stub)
        raw = redislib.Redis.from_url(RESULTS_URL).lindex(key, 0)
        if raw:
            return {"status": "terminado", "result": json.loads(raw)}
        return {"status": "en_cola_o_corriendo", "actor": e["actor"]}
    except Exception as e:
        return {"status": "desconocido", "detail": str(e)[:200]}

@app.get("/quakes")
def quakes(minmag: float = 0.0, limit: int = 5000, start: str | None = None, end: str | None = None):
    q = pd.read_parquet("data/raw/quakes_full.parquet")
    q["time"] = pd.to_datetime(q["time"], utc=True)
    if start:
        q = q[q.time >= pd.to_datetime(start, utc=True)]
    if end:
        q = q[q.time <= pd.to_datetime(end, utc=True) + pd.Timedelta(days=1)]
    q = q[q.mag >= minmag].sort_values("time").tail(limit)
    q["time"] = q.time.astype(str)
    return q[["time", "lat", "lon", "depth", "mag", "place"]].to_dict(orient="records")

@app.get("/ingesta")
def ingesta():
    import json, os
    try:
        st = json.load(open("data/last_ingest.json"))
    except FileNotFoundError:
        st = {"nota": "live_loop sin correr: python -m src.ingest.live_loop --once"}
    return st

@app.get("/aftershock")
def aftershock():
    from src.models.aftershock import dial
    try:
        return dial()
    except FileNotFoundError:
        return {"modo_secuencia": False, "nota": "ETAS sin ajustar: corre src.models.etas"}

@app.get("/prospective")
def prospective():
    try:
        log = pd.read_parquet("data/forecast_log.parquet").fillna("pendiente")
        return {"n": len(log), "log": log.to_dict(orient="records"),
                "nota": "Mini-CSEP: emitido hacia adelante desde 2026-10-09, se califica al cerrar ventana 7d."}
    except FileNotFoundError:
        return {"n": 0, "log": []}

@app.get("/risk/{zone}")
def risk(zone: str, date: str | None = Query(default=None, description="YYYY-MM-DD, hindcast date")):
    return _predict(zone, date)

@app.get("/risk")
def risk_all(date: str | None = Query(default=None)):
    _, df = _load()
    return [_predict(z, date) for z in sorted(df.zone.unique().tolist())]
