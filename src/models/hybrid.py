"""Hibrido ETAS x ML: tasa esperada ETAS (ajustada solo en train) como feature de LightGBM."""
import numpy as np, pandas as pd
from src.models.etas import fit_zone, expected_7d_vec, MC
from src.features.zones import assign_zone

if __name__ == "__main__":
    q = pd.read_parquet("data/raw/quakes_full.parquet")
    q["time"] = pd.to_datetime(q["time"], utc=True)
    q["zone"] = [assign_zone(la, lo) for la, lo in zip(q.lat, q.lon)]
    q = q.dropna(subset=["zone"]).sort_values("time")
    t0 = q.time.min()
    q["td"] = (q.time - t0).dt.total_seconds() / 86400
    df = pd.read_parquet("data/processed/dataset_full.parquet")
    df["date"] = pd.to_datetime(df["date"])
    dates = df.date.unique(); n = len(dates)
    cut2 = dates[int(.85 * n)]
    cut2ts = pd.to_datetime(cut2).tz_localize("America/Panama")
    df["etas_rate"] = 0.0
    for z, gq in q.groupby("zone"):
        gtr = gq[gq.time < cut2ts]
        th = fit_zone(gtr.td.values, gtr.mag.values)
        rows = df[df.zone == z].sort_values("date")
        tq = (rows.date.dt.tz_localize("America/Panama") - t0).dt.total_seconds().values / 86400
        e = np.zeros(len(rows))
        for i in range(0, len(tq), 2000):  # batches: historia completa hasta cada fecha
            e[i:i + 2000] = expected_7d_vec(th, gq[gq.td <= tq[i:i + 2000].max()].td.values,
                                            gq[gq.td <= tq[i:i + 2000].max()].mag.values, tq[i:i + 2000])
        df.loc[rows.index, "etas_rate"] = np.minimum(e, 20)
        print(f"{z} ok", flush=True)
    df.to_parquet("data/processed/dataset_hybrid.parquet", index=False)
    print("saved hybrid", flush=True)
