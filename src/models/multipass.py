"""Multipass por fases (bajo pico de RAM): ventanas -> torch -> lgbm -> stacking.
Stacker entrenado en val, evaluado en test. Alineado por (zone, date)."""
import gc, numpy as np, pandas as pd

W = 30
FEATS = ["n", "n7", "n30", "maxmag7", "logE7", "mean_depth", "days_since_m4",
         "rsi_n14", "rsi_E14", "vol_n30", "roc_E30", "benioff_since_m4",
         "t2m_mean", "rh_mean", "pres_mean", "precip_sum",
         "t2m_mean_anom", "rh_mean_anom", "pres_mean_anom"]  # = sequence.FEATS, sin importar torch

USE = ["zone", "date"] + FEATS + ["label_M4_7d"]

def phase1_windows():
    print("fase1: ventanas", flush=True)
    df = pd.read_parquet("data/processed/dataset_full.parquet", columns=USE)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["zone", "date"])
    dates = df.date.unique(); n = len(dates)
    cut1, cut2 = dates[int(.7 * n)], dates[int(.85 * n)]
    mu, sd = df[df.date < cut1][FEATS].mean(), df[df.date < cut1][FEATS].std().replace(0, 1)
    Xs, keys = [], []
    need = df[df.date >= cut1]
    for z, g in df.groupby("zone"):
        g = g.sort_values("date").reset_index(drop=True)
        vals = ((g[FEATS] - mu) / sd).fillna(0).values.astype(np.float32)
        want = set(need[need.zone == z].date)
        for i in range(W - 1, len(g)):
            if g.date.iloc[i] in want:
                Xs.append(vals[i - W + 1:i + 1]); keys.append((z, g.date.iloc[i]))
    Xn = np.array(Xs)
    np.save("data/processed/mp_Xn.npy", Xn)
    pd.DataFrame(keys, columns=["zone", "date"]).to_parquet("data/processed/mp_keys.parquet")
    print(f"fase1 ok: {Xn.shape}", flush=True)
    del df, Xs, Xn, keys, need; gc.collect()
    return str(cut1.date()), str(cut2.date())

def phase2_torch():
    import torch
    from src.models.sequence import LSTMClf, TransClf
    print("fase2: torch", flush=True)
    Xn = np.load("data/processed/mp_Xn.npy", mmap_mode="r")
    out = {}
    for name, fn in [("lstm", "models/lstm_m4.pt"), ("trans", "models/transformer_m4.pt")]:
        m = LSTMClf(len(FEATS)) if name == "lstm" else TransClf(len(FEATS))
        m.load_state_dict(torch.load(fn, map_location="cpu")); m.eval()
        ps = []
        with torch.no_grad():
            for i in range(0, len(Xn), 512):
                ps.append(torch.sigmoid(m(torch.from_numpy(np.array(Xn[i:i + 512])))).numpy())
        out[name] = np.concatenate(ps)
        print(f"fase2 {name} ok", flush=True)
        del m; gc.collect()
    np.save("data/processed/mp_plstm.npy", out["lstm"])
    np.save("data/processed/mp_ptrans.npy", out["trans"])

def phase3a_lgbm():
    """Solo lightgbm (sin sklearn en el proceso)."""
    import pickle
    print("fase3a: lgbm preds", flush=True)
    b = pickle.load(open("models/lgbm_full.pkl", "rb"))
    keys = pd.read_parquet("data/processed/mp_keys.parquet")
    df = pd.read_parquet("data/processed/dataset_full.parquet",
                         columns=["zone", "date", "label_M4_7d"] + b["features"])
    df["date"] = pd.to_datetime(df["date"])
    t = df.merge(keys, on=["zone", "date"])
    t["p_lgbm"] = b["label_M4_7d"].predict_proba(t[b["features"]].fillna(0))[:, 1]
    t[["zone", "date", "label_M4_7d", "p_lgbm"]].to_parquet("data/processed/mp_lgbm.parquet")
    print("fase3a ok", flush=True)

def phase3b_stack():
    """Solo sklearn/scipy (sin lightgbm en el proceso)."""
    import pickle
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, roc_auc_score
    print("fase3b: stacking", flush=True)
    t = pd.read_parquet("data/processed/mp_lgbm.parquet")
    t["date"] = pd.to_datetime(t["date"])
    t["p_lstm"] = np.load("data/processed/mp_plstm.npy")
    t["p_trans"] = np.load("data/processed/mp_ptrans.npy")
    dates = t.date.unique()
    cut = sorted(dates)[int(len(dates) * 0.5)]
    val, tst = t[t.date < cut], t[t.date >= cut]
    cols = ["p_lgbm", "p_lstm", "p_trans"]
    st = LogisticRegression(max_iter=1000).fit(val[cols], val.label_M4_7d)
    print("coef:", dict(zip(cols, st.coef_[0].round(3))), flush=True)
    for name, pred in [("lgbm", tst.p_lgbm.values), ("stack", st.predict_proba(tst[cols])[:, 1])]:
        print("%s test PR-AUC=%.4f ROC=%.4f" % (
            name, average_precision_score(tst.label_M4_7d, pred),
            roc_auc_score(tst.label_M4_7d, pred)), flush=True)
    pickle.dump(st, open("models/stacker.pkl", "wb"))
    for tl in [0.3, 0.5]:
        al = (tst.p_lgbm.values >= 0.5) & (tst.p_lstm.values >= tl)
        y = tst.label_M4_7d.values
        print(f"cascada lstm>={tl}: hits={int(((al) & (y == 1)).sum())} "
              f"FA={int(((al) & (y == 0)).sum())} miss={int(((~al) & (y == 1)).sum())}", flush=True)
    al0 = tst.p_lgbm.values >= 0.5; y = tst.label_M4_7d.values
    print("lgbm solo: hits=%d FA=%d miss=%d" % (int(((al0) & (y == 1)).sum()),
          int(((al0) & (y == 0)).sum()), int(((~al0) & (y == 1)).sum())), flush=True)

def phase3_stack():
    phase3a_lgbm()

if __name__ == "__main__":
    import sys
    phase = sys.argv[1] if len(sys.argv) > 1 else "all"
    if phase in ("all", "1"): phase1_windows()
    if phase in ("all", "2"): phase2_torch()
    if phase in ("all", "3"): phase3_stack()
    if phase == "3b": phase3b_stack()
