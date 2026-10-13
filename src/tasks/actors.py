"""Actores Dramatiq: toda la ingesta/entreno/evaluacion corre como tareas.
Worker: uv run dramatiq src.tasks.actors --processes 1 --threads 4
Colas: default (lento: train/build), io (ingestas), live (poll 5min, auto-reagenda)."""
import dramatiq
from . import broker  # noqa: F401  (registra broker global)

@dramatiq.actor(queue_name="io", store_results=True, max_retries=3, min_backoff=30_000)
def ingest_quakes(start: str, end: str, out: str = "data/raw/quakes_full.parquet"):
    import pandas as pd
    from src.ingest.api_usgs import fetch, atomic_parquet
    new = fetch(start, end, minmag=4.0)
    try:
        old = pd.read_parquet(out)
    except FileNotFoundError:
        old = pd.DataFrame(columns=new.columns)
    have = set(old.id) if len(old) else set()
    fresh = new[~new.id.isin(have)] if len(new) else new
    if len(fresh):
        import json
        full = pd.concat([old, fresh], ignore_index=True).drop_duplicates("id")
        atomic_parquet(full, out)
        ev = fresh[["id", "time", "lat", "lon", "depth", "mag", "place"]].copy()
        ev["time"] = pd.to_datetime(ev["time"], utc=True).astype(str)
        with open("data/live_events.jsonl", "a") as f:
            for r in ev.itertuples():
                f.write(json.dumps({"id": r.id, "time": r.time, "lat": r.lat, "lon": r.lon,
                                    "depth": r.depth, "mag": r.mag, "place": r.place}) + "\n")
        _stamp(int(len(fresh)))
        if len(fresh):
            alert_new.send(ev.astype({"mag": float}).to_dict(orient="records"))
        grandes = fresh[pd.to_numeric(fresh.mag, errors="coerce") >= 6.0]
        if len(grandes):
            g0 = grandes.iloc[0]
            refit_etas.send(f"M{float(g0.mag):.1f} {g0.id}")
    return {"nuevos": int(len(fresh))}

def _stamp(n: int):
    import json
    from datetime import datetime, timezone
    import pandas as pd
    full = pd.read_parquet("data/raw/quakes_full.parquet")
    cmax = pd.to_datetime(full.time, utc=True).max()
    now = datetime.now(timezone.utc)
    json.dump({"ts": now.isoformat(), "nuevos": n, "catalog_max": str(cmax),
               "delay_min": round((now - cmax).total_seconds() / 60, 1),
               "total": int(len(full))}, open("data/last_ingest.json", "w"))

@dramatiq.actor(queue_name="io", store_results=True, max_retries=3, min_backoff=30_000)
def ingest_weather_year(year: int):
    from src.ingest.weather import fetch_zone
    from src.features.zones import ZONES
    import pandas as pd
    dfs = [fetch_zone(z, f"{year}-01-01", f"{year}-12-31") for z in ZONES]
    pd.concat(dfs, ignore_index=True).to_parquet(f"data/raw/weather_{year}.parquet", index=False)
    return {"year": year}

@dramatiq.actor(queue_name="default", store_results=True, time_limit=3_600_000)
def build_dataset():
    import subprocess, sys
    r = subprocess.run([sys.executable, "-m", "src.features.build",
                        "--quakes", "data/raw/quakes_full.parquet",
                        "--weather", "data/raw/weather_full.parquet",
                        "--out", "data/processed/dataset_full.parquet"],
                       capture_output=True, text=True)
    return {"rc": r.returncode, "tail": r.stderr[-500:] + r.stdout[-500:]}

@dramatiq.actor(queue_name="io", store_results=True, max_retries=3, min_backoff=30_000)
def resync_catalog():
    """Re-pull amplio anual 2025→hoy: captura backfill tardío de USGS (ej. 20 eventos
    ene–sep 2026 que entraron semanas después). Se auto-reagenda cada 30 días."""
    import pandas as pd
    from datetime import datetime, timezone
    from src.ingest.api_usgs import fetch, atomic_parquet
    now = datetime.now(timezone.utc)
    new = fetch("2025-01-01", now.strftime("%Y-%m-%dT%H:%M:%S"), minmag=4.0)
    old = pd.read_parquet("data/raw/quakes_full.parquet")
    have = set(old.id)
    fresh = new[~new.id.isin(have)]
    if len(fresh):
        atomic_parquet(
            pd.concat([old, fresh], ignore_index=True).drop_duplicates("id"),
            "data/raw/quakes_full.parquet")
    resync_catalog.send_with_options(delay=30 * 86400_000)
    return {"recuperados": int(len(fresh)), "total": int(len(old) + len(fresh))}

@dramatiq.actor(queue_name="io", store_results=True, max_retries=3, min_backoff=30_000)
def ingest_igc():
    """Scrapea lista IGC-UPA (M1.7+, bajo USGS) y anexa con dedupe espacio-temporal."""
    import pandas as pd, numpy as np
    from src.ingest.igc_up import fetch_igc
    igc = fetch_igc()
    old = pd.read_parquet("data/raw/quakes_full.parquet")
    if "src" not in old.columns: old["src"] = "usgs"
    have = set(old.id) if "id" in old.columns else set()
    igc = igc[~igc.id.isin(have)]
    ut = pd.to_datetime(old.time, utc=True).values.astype("datetime64[s]").astype(float)
    keep = []
    for r in igc.itertuples():
        t = r.time.value / 1e9
        near = np.where(np.abs(ut - t) < 120)[0]
        if len(near) and np.sqrt((old.lat.values[near] - r.lat) ** 2 +
                                 (old.lon.values[near] - r.lon) ** 2).min() < 0.3:
            continue
        keep.append(r.Index)
    add = igc.loc[keep]
    if len(add):
        from src.ingest.api_usgs import atomic_parquet
        atomic_parquet(
            pd.concat([old, add], ignore_index=True).drop_duplicates("id"),
            "data/raw/quakes_full.parquet")
        ev = add.copy()
        ev["time"] = pd.to_datetime(ev["time"], utc=True).astype(str)
        alert_new.send(ev[["id", "time", "lat", "lon", "depth", "mag", "place"]].astype(
            {"mag": float}).to_dict(orient="records"))
        big = add[pd.to_numeric(add.mag, errors="coerce") >= 6.0]
        if len(big):
            refit_etas.send(f"M{float(big.iloc[0].mag):.1f} {big.iloc[0].id}")
    return {"nuevos_igc": int(len(add))}

@dramatiq.actor(queue_name="live", store_results=True)
def alert_new(events: list, umbral: float = 4.5):
    """Alerta RT por Telegram para eventos >= umbral en bbox Panamá. Dedupe por id."""
    import json, os
    from src.notify.telegram import send, quake_text
    seen_path = "data/alerts_sent.json"
    seen = set(json.load(open(seen_path))) if os.path.exists(seen_path) else set()
    sent = 0
    for ev in events:
        if ev.get("id") in seen or (ev.get("mag") or 0) < umbral:
            continue
        if not (6.0 <= (ev.get("lat") or 0) <= 10.5 and -84.0 <= (ev.get("lon") or 0) <= -76.5):
            continue
        send(quake_text(ev))
        seen.add(ev["id"]); sent += 1
    json.dump(sorted(seen)[-2000:], open(seen_path, "w"))
    return {"alertados": sent}

@dramatiq.actor(queue_name="io", store_results=True)
def ingest_rss():
    """Lee RSS RSN-Costa Rica (borde Chiriquí/Bocas)."""
    import re
    import requests
    try:
        xml = requests.get("https://rsn.ucr.ac.cr/actividad-sismica/ultimos-sismos",
                           params={"format": "feed", "type": "rss"}, timeout=30,
                           headers={"User-Agent": "SismosPanama-PoC/1.0"}).text
        n = len(re.findall(r"<item>", xml))
        return {"items": n}
    except Exception as e:
        return {"error": str(e)[:100]}

@dramatiq.actor(queue_name="live")
def fast_poll():
    """Carril rápido 60s: IGC-UPA + RSS RSN. USGS queda en el loop de 5min."""
    ingest_igc.send()
    ingest_rss.send()
    fast_poll.send_with_options(delay=60_000)

@dramatiq.actor(queue_name="live")
def live_poll():
    """Sondea ultimas 3h (USGS + IGC) y se auto-reagenda en 5 min (sin scheduler externo)."""
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    start = (now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%S")
    ingest_quakes.send(start, now.strftime("%Y-%m-%dT%H:%M:%S"))
    ingest_igc.send()
    live_poll.send_with_options(delay=300_000)

@dramatiq.actor(queue_name="default", store_results=True, time_limit=600_000)
def refit_etas(trigger: str = "manual"):
    """Reajuste ETAS en vivo sobre ventana movil (ver src.models.etas.refit_recent).
    Se encola solo al ingresar un M6+ nuevo; el dial lo lee sin reinicios."""
    from src.models.etas import refit_recent
    return refit_recent(trigger=trigger)

@dramatiq.actor(queue_name="default", store_results=True)
def prospective_issue():
    from src.eval.prospective import issue
    issue()
    prospective_score.send()  # continuación: score SIEMPRE después de issue
    return {"ok": True}

@dramatiq.actor(queue_name="default", store_results=True)
def prospective_score():
    from src.eval.prospective import score
    score()
    return {"ok": True}
