"""Refit isotonic calibration (bundle["cal"]) on a hindcast window with mature labels.

Motivo: la calibracion anterior se ajusto en una ventana tranquila y aplana todo
score alto (crudo 0.97 -> 0.23 en M4; techos 0.028 en M5 y 0.023 en M6), con lo
que los niveles 4/5/6 del dashboard eran matematicamente inalcanzables aunque
hubiera una secuencia M7.7 activa. Este script reajusta los tres mapas
isotonicos sobre filas 2018->hoy con label maduro (+7d) y reporta Brier
viejo vs nuevo (global y ultimos 365d; este ultimo es in-sample para el mapa
nuevo y se reporta como tal). Uso:

    uv run python -m src.models.recalibrate
"""
import pickle
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

LABELS = ["label_M4_7d", "label_M5_7d", "label_M6_7d"]
FIT_START = "2018-04-07"


def brier(p, y):
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)
    return float(np.mean((p - y) ** 2))


def derive_labels(fit):
    """Labels M5/M6 con la misma definicion que build.py para M4 (sismo M>=m en
    los 7d siguientes, misma zona). El dataset solo trae label_M4_7d, asi que
    M5/M6 se derivan del catalogo vivo con identica ventana y zonas."""
    from src.features.zones import assign_zone
    q = pd.read_parquet("data/raw/quakes_full.parquet")
    q["time"] = pd.to_datetime(q["time"], utc=True)
    q["zone"] = [assign_zone(la, lo) for la, lo in zip(q.lat, q.lon)]
    q["date"] = q["time"].dt.tz_convert("America/Panama").dt.tz_localize(None).dt.normalize()
    out = {"label_M4_7d": fit["label_M4_7d"].to_numpy(dtype=float)}
    for c, m in (("label_M5_7d", 5.0), ("label_M6_7d", 6.0)):
        per_zone = {z: np.sort(g[g.mag >= m]["date"].to_numpy().astype("datetime64[D]").astype(int))
                    for z, g in q.groupby("zone")}
        dz = fit["date"].to_numpy().astype("datetime64[D]").astype(int)
        y = np.zeros(len(fit), dtype=float)
        for z, arr in per_zone.items():
            msk = (fit["zone"] == z).to_numpy()
            if msk.any() and len(arr):
                i = np.searchsorted(arr, dz[msk], side="right")
                ok = (i < len(arr)) & (arr[np.clip(i, 0, len(arr) - 1)] - dz[msk] <= 7)
                y[msk] = ok.astype(float)
        out[c] = y
    return out


def main():
    bundle = pickle.load(open("models/lgbm_full.pkl", "rb"))
    df = pd.read_parquet("data/processed/dataset_full.parquet")
    df["date"] = pd.to_datetime(df["date"])
    dmax = df.date.max()
    fit = df[(df.date >= FIT_START) & (df.date <= dmax - pd.Timedelta(days=7))].copy()
    feats = bundle["features"]
    X = fit[feats].fillna(0)
    raw = {c: bundle[c].predict_proba(X)[:, 1] for c in LABELS}
    Y = derive_labels(fit)
    cal_nuevo, reporte = {}, {"n_fit": int(len(fit)), "fit_desde": FIT_START,
                              "fit_hasta": str((dmax - pd.Timedelta(days=7)).date())}
    tail_msk = (fit.date > dmax - pd.Timedelta(days=365)).to_numpy()
    for c in LABELS:
        y = Y[c]
        ir = IsotonicRegression(out_of_bounds="clip")
        ir.fit(raw[c], y)
        cal_nuevo[c] = ir
        p_old = bundle["cal"][c].predict(raw[c])
        p_new = ir.predict(raw[c])
        yt = Y[c][tail_msk]
        reporte[c] = {
            "brier_old": round(brier(p_old, y), 5),
            "brier_new": round(brier(p_new, y), 5),
            "brier_old_365d": round(brier(bundle["cal"][c].predict(raw[c][tail_msk]), yt), 5),
            "brier_new_365d_insample": round(brier(ir.predict(raw[c][tail_msk]), yt), 5),
            "cal_new(0.97)": round(float(ir.predict([0.97])[0]), 4),
            "techo_new": round(float(ir.predict([1.0])[0]), 4),
        }
    bundle["cal"] = cal_nuevo
    bundle["cal_meta"] = {"metodo": "isotonica ventana 2018->hoy labels maduros",
                          "refit_ts": pd.Timestamp.now(tz="UTC").isoformat(), **reporte}
    pickle.dump(bundle, open("models/lgbm_full.pkl", "wb"))
    print(reporte)


if __name__ == "__main__":
    main()
