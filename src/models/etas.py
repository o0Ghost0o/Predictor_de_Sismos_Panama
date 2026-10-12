"""Baseline ETAS temporal por zona (Ogata 1988). Fit SOLO en train (<2018-04-04).
lambda(t) = mu + sum K*exp(alpha*(Mj-Mc))*(t-tj+c)^-p ; Mc=4.0. Params en log-escala."""
import numpy as np, pandas as pd
from scipy.optimize import minimize
from sklearn.metrics import average_precision_score, roc_auc_score

MC = 4.0

def nll_logphi(phi, t, m, T):
    mu, K, p = np.exp(phi[0]), np.exp(phi[1]), 1 + np.exp(phi[2])
    c, alpha = 0.01, 1.0  # fijos (literatura) para catálogos ralos
    dt = t[:, None] - t[None, :]
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        kern = np.where(dt > 0, K * np.exp(alpha * (m[None, :] - MC)) * (dt + c) ** -p, 0.0)
    lam = mu + kern.sum(axis=1)
    ll = np.sum(np.log(np.maximum(lam, 1e-300)))
    with np.errstate(over="ignore", invalid="ignore"):
        integ = mu * T + np.sum(K * np.exp(alpha * (m - MC)) * ((T - (t - t[0]) + c) ** (1 - p) - c ** (1 - p)) / (1 - p))
    if not np.isfinite(ll) or not np.isfinite(integ): return 1e18
    return float(-ll + integ)

def fit_zone(t, m):
    """Ajuste estable: p=1.1 fijo (Omori), solo (mu, K). Si falla, params genéricos."""
    T = (t[-1] - t[0]) + 30
    c, alpha, p = 0.01, 1.0, 1.1
    def nll2(phi):
        mu, K = np.exp(phi[0]), np.exp(phi[1])
        dt = t[:, None] - t[None, :]
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            kern = np.where(dt > 0, K * np.exp(alpha * (m[None, :] - MC)) * (dt + c) ** -p, 0.0)
        lam = mu + kern.sum(axis=1)
        ll = np.sum(np.log(np.maximum(lam, 1e-300)))
        with np.errstate(over="ignore", invalid="ignore"):
            integ = mu * T + np.sum(K * np.exp(alpha * (m - MC)) * ((T - (t - t[0]) + c) ** (1 - p) - c ** (1 - p)) / (1 - p))
        if not np.isfinite(ll) or not np.isfinite(integ): return 1e18
        return float(-ll + integ)
    r = minimize(nll2, [-4, -4], method="Nelder-Mead",
                 options={"maxiter": 300, "xatol": 1e-3, "fatol": 1e-3})
    if np.isfinite(r.fun):
        return np.exp(r.x[0]), np.exp(r.x[1]), c, p, alpha
    mu_gen = len(t) / T  # fallback: tasa media
    return mu_gen, 0.02, c, p, alpha

def expected_7d_vec(th, thist, mhist, tq):
    mu, K, c, p, alpha = th
    dt = tq[:, None] - thist[None, :]
    dt = np.maximum(dt, 0) + c
    a = (dt + 7) ** (1 - p) - dt ** (1 - p)
    trig = (K * np.exp(alpha * (mhist[None, :] - MC)) * a / (1 - p)).sum(axis=1)
    return mu * 7 + trig

if __name__ == "__main__":
    from src.features.zones import assign_zone
    q = pd.read_parquet("data/raw/quakes_full.parquet")
    q["time"] = pd.to_datetime(q["time"], utc=True)
    q["zone"] = [assign_zone(la, lo) for la, lo in zip(q.lat, q.lon)]
    q = q.dropna(subset=["zone"]).sort_values("time")
    t0 = q.time.min()
    q["td"] = (q.time - t0).dt.total_seconds() / 86400
    df = pd.read_parquet("data/processed/dataset_full.parquet")
    df["date"] = pd.to_datetime(df["date"])
    dates = df.date.unique(); n = len(dates)
    cut1, cut2 = dates[int(.7 * n)], dates[int(.85 * n)]
    cut2ts = pd.to_datetime(cut2).tz_localize("America/Panama")
    print(f"train<{pd.to_datetime(cut1).date()} val<{pd.to_datetime(cut2).date()} test>=...", flush=True)
    te = df[df.date >= cut2].copy()
    Pall, Yall = [], []
    for z, gq in q.groupby("zone"):
        gtr = gq[gq.time < cut2ts]
        th = fit_zone(gtr.td.values, gtr.mag.values)
        print(f"{z}: mu={th[0]:.4f} K={th[1]:.4f} c={th[2]:.4f} p={th[3]:.2f} a={th[4]:.2f} ntr={len(gtr)}", flush=True)
        rows = te[te.zone == z].sort_values("date")
        tq = (rows.date.dt.tz_localize("America/Panama") - t0).dt.total_seconds().values / 86400
        e = expected_7d_vec(th, gq[gq.time < cut2ts].td.values, gq[gq.time < cut2ts].mag.values, tq)
        e = np.minimum(e, 20)
        Pall.append(1 - np.exp(-e)); Yall.append(rows.label_M4_7d.values)
    Y = np.concatenate(Yall); P = np.concatenate(Pall)
    print(f"ETAS test PR-AUC={average_precision_score(Y, P):.4f} ROC={roc_auc_score(Y, P):.4f} (base={Y.mean():.4f})")
    import pickle
    thetas = {}
    for z, gq in q.groupby("zone"):
        gtr = gq[gq.time < cut2ts]
        thetas[z] = fit_zone(gtr.td.values, gtr.mag.values)
    pickle.dump({"thetas": thetas, "t0": t0, "cut2": str(pd.to_datetime(cut2).date())},
                open("models/etas_params.pkl", "wb"))
    print("params guardados")
