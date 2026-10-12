"""Ingesta live de baja dilatacion: sondea USGS cada N minutos, anexa eventos M4+ nuevos.
Uso: python -m src.ingest.live_loop --once | --interval 300
Escribe data/last_ingest.json {ts, nuevos, catalog_max, delay_min}.
El dial ETAS lee el catalogo al vuelo: un M nuevo mueve p24 en minutos."""
import argparse, json, time
from datetime import datetime, timezone, timedelta
import pandas as pd
from src.ingest.api_usgs import fetch

RAW = "data/raw/quakes_full.parquet"
STATE = "data/last_ingest.json"

def poll() -> dict:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%S")
    new = fetch(start, now.strftime("%Y-%m-%dT%H:%M:%S"), minmag=4.0)
    try:
        old = pd.read_parquet(RAW)
    except FileNotFoundError:
        old = pd.DataFrame(columns=new.columns)
    have = set(old.id) if len(old) else set()
    fresh = new[~new.id.isin(have)] if len(new) else new
    if len(fresh):
        pd.concat([old, fresh], ignore_index=True).drop_duplicates("id").to_parquet(RAW, index=False)
        ev = fresh[["id", "time", "lat", "lon", "depth", "mag", "place"]].copy()
        ev["time"] = pd.to_datetime(ev["time"], utc=True).astype(str)
        with open("data/live_events.jsonl", "a") as f:
            for r in ev.itertuples():
                f.write(json.dumps({"id": r.id, "time": r.time, "lat": r.lat, "lon": r.lon,
                                    "depth": r.depth, "mag": r.mag, "place": r.place}) + "\n")
    full = pd.read_parquet(RAW)
    cmax = pd.to_datetime(full.time, utc=True).max()
    state = {"ts": now.isoformat(), "nuevos": int(len(fresh)),
             "catalog_max": str(cmax), "delay_min": round((now - cmax).total_seconds() / 60, 1),
             "total": int(len(full))}
    json.dump(state, open(STATE, "w"))
    return state

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true"); ap.add_argument("--interval", type=int, default=300)
    a = ap.parse_args()
    while True:
        print(poll(), flush=True)
        if a.once: break
        time.sleep(a.interval)
