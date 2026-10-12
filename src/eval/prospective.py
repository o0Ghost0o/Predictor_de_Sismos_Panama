"""Mini-CSEP Panama: emite pronostico prospectivo diario y lo califica al cerrar la ventana.
Uso: python -m src.eval.prospective issue   -> registra P(M4+/M5+/M6+ 7d) de hoy por zona
     python -m src.eval.prospective score  -> resuelve vencidos contra USGS/dataset"""
import sys, pickle, pandas as pd

LOG = "data/forecast_log.parquet"

def issue():
    b = pickle.load(open("models/lgbm_full.pkl", "rb"))
    df = pd.read_parquet("data/processed/dataset_hybrid.parquet")
    df["date"] = pd.to_datetime(df["date"])
    feats = b["features"]  # bundle validado: 14 feats exactos, sin experimentos
    today = df.date.max()
    rows = []
    for z, g in df[df.date == today].groupby("zone"):
        X = g[feats].fillna(0)
        rows.append({"issued": str(today.date()), "target_end": str((today + pd.Timedelta(days=7)).date()),
                     "zone": z, "p4": round(float(b["label_M4_7d"].predict_proba(X)[:, 1][0]), 4),
                     "p5": round(float(b["label_M5_7d"].predict_proba(X)[:, 1][0]), 4),
                     "p6": round(float(b["label_M6_7d"].predict_proba(X)[:, 1][0]), 4)})
    new = pd.DataFrame(rows)
    try:
        old = pd.read_parquet(LOG)
        log = pd.concat([old, new]).drop_duplicates(subset=["issued", "zone"], keep="last")
    except FileNotFoundError:
        log = new
    import os; os.makedirs("data", exist_ok=True)
    log.to_parquet(LOG, index=False)
    print(log.to_string())

def score():
    from src.features.zones import assign_zone
    log = pd.read_parquet(LOG)
    q = pd.read_parquet("data/raw/quakes_full.parquet")
    q["time"] = pd.to_datetime(q["time"], utc=True)
    q["date"] = q["time"].dt.tz_convert("America/Panama").dt.tz_localize(None).dt.normalize()
    q["zone"] = [assign_zone(la, lo) for la, lo in zip(q.lat, q.lon)]
    data_max = q.date.max()
    res = []
    for r in log.itertuples():
        i, e = pd.to_datetime(r.issued), pd.to_datetime(r.target_end)
        if data_max < e:
            res.append("pendiente")
            continue
        hit = ((q.zone == r.zone) & (q.date > i) & (q.date <= e) & (q.mag >= 4.0)).any()
        res.append("acierto" if (hit and r.p4 >= 0.5) else ("omitido" if hit else
                   ("falsa_alarma" if r.p4 >= 0.5 else "correcto_negativo")))
    log["resultado"] = res
    log.to_parquet(LOG, index=False)
    print(log.to_string())

if __name__ == "__main__":
    (score if len(sys.argv) > 1 and sys.argv[1] == "score" else issue)()
