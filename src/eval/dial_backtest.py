"""Valida el dial 24h en hindcast: P(M4+ manana) ETAS vs observado, periodo test."""
import numpy as np, pandas as pd, pickle
from src.models.aftershock import expected_h
from src.features.zones import assign_zone
from sklearn.metrics import average_precision_score, roc_auc_score

if __name__ == "__main__":
    b = pickle.load(open("models/etas_params.pkl", "rb"))
    q = pd.read_parquet("data/raw/quakes_full.parquet")
    q["time"] = pd.to_datetime(q["time"], utc=True)
    q["zone"] = [assign_zone(la, lo) for la, lo in zip(q.lat, q.lon)]
    q = q.dropna(subset=["zone"]).sort_values("time")
    t0 = pd.to_datetime(b["t0"], utc=True)
    q["td"] = (q.time - t0).dt.total_seconds() / 86400
    q["date"] = q.time.dt.tz_convert("America/Panama").dt.tz_localize(None).dt.normalize()
    df = pd.read_parquet("data/processed/dataset_full.parquet")
    df["date"] = pd.to_datetime(df["date"])
    dates = df.date.unique(); cut2 = dates[int(.85 * len(dates))]
    te = df[df.date >= cut2].sort_values(["zone", "date"])
    P, Y = [], []
    per = {}
    for z, th in b["thetas"].items():
        g = q[q.zone == z]
        rows = te[te.zone == z].sort_values("date")
        tq = (rows.date.dt.tz_localize("America/Panama") - t0).dt.total_seconds().values / 86400
        e = np.zeros(len(rows))
        for i in range(0, len(tq), 2000):
            sl = slice(i, i + 2000)
            gh = g[g.td <= tq[sl].max()]
            e[sl] = np.array([expected_h(th, gh.td.values, gh.mag.values, t, 1.0) for t in tq[sl]])
        p = 1 - np.exp(-np.minimum(e, 20))
        # observado: hubo M4+ al dia siguiente (ventana 24h emitida el dia D)
        qd = set(g[g.mag >= 4.0].date)
        y = np.array([1 if d + pd.Timedelta(days=1) in qd else 0 for d in rows.date])
        P.append(p); Y.append(y)
        per[z] = (float(average_precision_score(y, p)), float(roc_auc_score(y, p)), float(y.mean()))
    P = np.concatenate(P); Y = np.concatenate(Y)
    print(f"DIAL-24h test PR-AUC={average_precision_score(Y, P):.4f} ROC={roc_auc_score(Y, P):.4f} (base={Y.mean():.4f})")
    for z, (ap, ro, bs) in per.items():
        print(f"  {z}: PR-AUC={ap:.4f} ROC={ro:.4f} base={bs:.4f}")
