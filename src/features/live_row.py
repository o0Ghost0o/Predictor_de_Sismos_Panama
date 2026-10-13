"""Fila de features de HOY por zona para servir /risk en vivo.

El dataset versionado termina ayer (o antes); este helper calcula la fila de
hoy desde el catalogo vivo + colas de 400d del dataset, con las mismas
ventanas que build.py. El clima se arrastra (ultimo dia disponible por zona:
la ingesta meteorologica va dias por detras; mejor que ceros). Las ventanas
tecnicas largas (RSI/roc 90d, Benioff) se aproximan sobre la cola; documentado
porque el arranque de la cola parte de 0 en zonas quietas.
"""
import numpy as np
import pandas as pd
from src.features.zones import assign_zone, ZONES
from src.features.build import add_technical

TAIL_DAYS = 400


def _hoy_panama(hoy=None):
    if hoy is None:
        hoy = pd.Timestamp.now(tz="America/Panama").normalize().tz_localize(None)
    return pd.to_datetime(hoy).normalize()


def live_rows(hoy=None):
    hoy = _hoy_panama(hoy)
    ds = pd.read_parquet("data/processed/dataset_full.parquet")
    ds["date"] = pd.to_datetime(ds["date"])
    tail = ds.sort_values("date").groupby("zone").tail(TAIL_DAYS)

    q = pd.read_parquet("data/raw/quakes_full.parquet")
    q["time"] = pd.to_datetime(q["time"], utc=True)
    q["zone"] = [assign_zone(la, lo) for la, lo in zip(q.lat, q.lon)]
    q = q.dropna(subset=["zone"]).copy()
    q["date"] = q["time"].dt.tz_convert("America/Panama").dt.tz_localize(None).dt.normalize()
    q["energy"] = 10 ** (1.5 * q["mag"])
    qd = q[q.date == hoy].groupby("zone").agg(
        n=("mag", "size"), maxmag=("mag", "max"),
        mean_depth=("depth", "mean"), energy=("energy", "sum"),
        m4=("mag", lambda s: int((s >= 4.0).sum()))).reset_index()
    qd["date"] = hoy

    base_cols = ["zone", "date", "n", "maxmag", "mean_depth", "energy", "m4"]
    # El dataset puede ya traer `hoy`: se descarta y hoy se recalcula del catalogo.
    base = tail[tail.date < hoy][base_cols].copy()
    mis = set(ZONES) - set(tail.zone.unique())
    for z in mis:  # zona sin historia: fila semilla
        base = pd.concat([base, pd.DataFrame(
            [{"zone": z, "date": hoy - pd.Timedelta(days=1), "n": 0, "maxmag": 0,
              "mean_depth": np.nan, "energy": 0.0, "m4": 0}])], ignore_index=True)
    for z in ZONES:
        if z not in set(qd.zone):
            qd = pd.concat([qd, pd.DataFrame(
                [{"zone": z, "n": 0, "maxmag": 0, "mean_depth": np.nan,
                  "energy": 0.0, "m4": 0, "date": hoy}])], ignore_index=True)
    df = pd.concat([base, qd[base_cols]], ignore_index=True).sort_values(["zone", "date"])
    g = df.groupby("zone")
    df["n7"] = g["n"].transform(lambda s: s.rolling(7, min_periods=1).sum())
    df["n30"] = g["n"].transform(lambda s: s.rolling(30, min_periods=1).sum())
    df["maxmag7"] = g["maxmag"].transform(lambda s: s.rolling(7, min_periods=1).max())
    df["logE7"] = np.log10(g["energy"].transform(
        lambda s: s.rolling(7, min_periods=1).sum()) + 1)
    last, dsl = {}, []
    for _, r in df.iterrows():
        if r["m4"] > 0:
            last[r["zone"]] = r["date"]
        dsl.append((r["date"] - last.get(r["zone"], r["date"])).days
                    if r["zone"] in last else 999)
    df["days_since_m4"] = dsl
    df = add_technical(df)
    try:
        w = pd.read_parquet("data/raw/weather_full.parquet")
        w["date"] = pd.to_datetime(w["date"])
        wlast = w.sort_values("date").groupby("zone").tail(1).drop(columns=["date"])
    except FileNotFoundError:
        wlast = pd.DataFrame(columns=["zone"])
    out = df[df.date == hoy].copy()
    out = out.merge(wlast, on="zone", how="left")
    out["label_M4_7d"] = None  # ventana futura aun abierta: sin label
    return out.reset_index(drop=True)
