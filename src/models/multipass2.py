"""Pase 2 con LR como portero (no como stacker):
A) umbrales por zona (max F1 en val) aplicados en test.
B) LR Gordon: P(LGBM se equivoca | p, incertidumbre, zona) -> abstenerse en top-riesgo.
Solo sklearn+pandas (preds precomputados, sin torch/lightgbm en el proceso)."""
import numpy as np, pandas as pd, pickle
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

if __name__ == "__main__":
    t = pd.read_parquet("data/processed/mp_lgbm.parquet")
    t["date"] = pd.to_datetime(t["date"])
    w = pd.read_parquet("data/processed/dataset_full.parquet",
                        columns=["zone", "date", "days_since_m4", "n30", "maxmag7"])
    w["date"] = pd.to_datetime(w["date"])
    t = t.merge(w, on=["zone", "date"])
    t["unc"] = (t.p_lgbm - 0.5).abs()  # cerca de 0.5 = dudoso
    dates = sorted(t.date.unique()); cut = dates[len(dates) // 2]
    val, tst = t[t.date < cut].copy(), t[t.date >= cut].copy()
    print(f"val={len(val)} test={len(tst)} corte={cut.date()}", flush=True)

    # A) umbral por zona
    thr = {}
    for z, g in val.groupby("zone"):
        best, bt = -1, 0.5
        for th in np.arange(0.2, 0.9, 0.05):
            f = f1_score(g.label_M4_7d, g.p_lgbm >= th, zero_division=0)
            if f > best: best, bt = f, th
        thr[z] = round(float(bt), 2)
    print("umbrales:", thr, flush=True)
    h = fa = m = 0
    for z, g in tst.groupby("zone"):
        al = g.p_lgbm >= thr[z]; y = g.label_M4_7d
        h += int(((al) & (y == 1)).sum()); fa += int(((al) & (y == 0)).sum())
        m += int(((~al) & (y == 1)).sum())
    print(f"A) umbral x zona: hits={h} FA={fa} miss={m}", flush=True)
    al0 = tst.p_lgbm >= 0.5; y0 = tst.label_M4_7d
    h0 = int(((al0) & (y0 == 1)).sum()); fa0 = int(((al0) & (y0 == 0)).sum())
    m0 = int(((~al0) & (y0 == 1)).sum())
    print(f"   global 0.5:    hits={h0} FA={fa0} miss={m0}", flush=True)

    # B) LR portero: predice fallo del pase 1
    val["err"] = (val.p_lgbm >= 0.5).astype(int) != val.label_M4_7d
    ZX = pd.get_dummies(val.zone, prefix="z")
    cols = ["p_lgbm", "unc", "days_since_m4", "n30"] + list(ZX.columns)
    gate = LogisticRegression(max_iter=1000).fit(
        pd.concat([val[["p_lgbm", "unc", "days_since_m4", "n30"]], ZX], axis=1), val.err)
    TX = pd.get_dummies(tst.zone, prefix="z").reindex(columns=ZX.columns, fill_value=0)
    tst["p_err"] = gate.predict_proba(
        pd.concat([tst[["p_lgbm", "unc", "days_since_m4", "n30"]], TX], axis=1))[:, 1]
    print("B) portero: tasa fallo val=%.3f" % val.err.mean(), flush=True)
    for q in [0.8, 0.9]:
        cut_e = tst.p_err.quantile(q)  # abstener el 20%/10% más riesgoso
        keep = tst.p_err < cut_e
        al = (tst.p_lgbm >= 0.5) & keep
        y = tst.label_M4_7d
        cov = keep.mean()
        print(f"   abstiene {100*(1-q):.0f}%: hits={int(((al)&(y==1)).sum())} "
              f"FA={int(((al)&(y==0)).sum())} miss={int((((~al)&(y==1))).sum())} cobertura={cov:.2f}",
              flush=True)
    pickle.dump({"thr": thr, "gate": gate, "zcols": list(ZX.columns)},
                open("models/gate.pkl", "wb"))
    print("gate guardado", flush=True)
