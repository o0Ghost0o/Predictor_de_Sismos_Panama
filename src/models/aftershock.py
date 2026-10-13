"""Segundo evaluador: dial de replicas ETAS a 24h/1h (numpy/pandas puro, sin torch/lgbm).
Modo secuencia activo si hubo M6+ en los ultimos 30 dias."""
import numpy as np, pandas as pd, pickle
from src.features.zones import assign_zone

def _load():
    b = pickle.load(open("models/etas_params.pkl", "rb"))
    q = pd.read_parquet("data/raw/quakes_full.parquet")
    q["time"] = pd.to_datetime(q["time"], utc=True)
    q["zone"] = [assign_zone(la, lo) for la, lo in zip(q.lat, q.lon)]
    q = q.dropna(subset=["zone"]).sort_values("time")
    t0 = pd.to_datetime(b["t0"], utc=True)
    q["td"] = (q.time - t0).dt.total_seconds() / 86400
    return b["thetas"], q, t0, b

def expected_h(th, thist, mhist, t_now, h_days):
    mu, K, c, p, alpha = th
    dt = np.maximum(t_now - thist, 0) + c
    a = (dt + h_days) ** (1 - p) - dt ** (1 - p)
    return mu * h_days + float((K * np.exp(alpha * (mhist - 4.0)) * a / (1 - p)).sum())

def dial(now=None):
    thetas, q, t0, b = _load()
    now = pd.to_datetime(now, utc=True) if now else q.time.max()
    t_now = (now - t0).total_seconds() / 86400
    big = q[(q.mag >= 6.0) & (q.time > now - pd.Timedelta(days=30))]
    out = {"modo_secuencia": bool(len(big)), "grandes_30d": int(len(big)),
           "now": str(now.date()), "refit_ts": b.get("refit_ts"),
           "refit_trigger": b.get("trigger"), "zonas": {}}
    for z, th in thetas.items():
        g = q[(q.zone == z) & (q.time <= now)]
        e24 = expected_h(th, g.td.values, g.mag.values, t_now, 1.0)
        e1 = expected_h(th, g.td.values, g.mag.values, t_now, 1 / 24)
        out["zonas"][z] = {"p24": round(float(1 - np.exp(-min(e24, 20))), 4),
                           "p1h": round(float(1 - np.exp(-min(e1, 20))), 4)}
    return out

def m6_curve(zone: str, date=None):
    """P(M6+ dia k) = 1-exp(-E_k * r), E_k tasa ETAS diaria, r = frac M6/M4 historica.
    Sin leakage: todo con historia <= fecha."""
    thetas, q, t0, _ = _load()
    now = pd.to_datetime(date, utc=True) if date else q.time.max()
    t_now = (now - t0).total_seconds() / 86400
    g = q[(q.zone == zone) & (q.time <= now)]
    m4 = g[g.mag >= 4.0]
    r = (len(g[g.mag >= 6.0]) / max(len(m4), 1)) if len(m4) else 0.038
    th = thetas[zone]
    out = []
    for k in range(7):
        e = expected_h(th, g.td.values, g.mag.values, t_now + k, 1.0)
        out.append(round(float(1 - np.exp(-min(e, 20) * r)), 4))
    return out

if __name__ == "__main__":
    import json
    print(json.dumps(dial(), indent=1))
