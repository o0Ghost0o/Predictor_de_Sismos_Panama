"""Baseline LightGBM + calibration, time split, MLflow. Includes seismic-only ablation."""
import argparse, mlflow, pandas as pd, numpy as np
import lightgbm as lgb
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss

SEIS = ["n", "n7", "n30", "maxmag7", "logE7", "mean_depth", "days_since_m4",
        "rsi_n14", "rsi_E14", "vol_n30", "roc_E30", "benioff_since_m4"]
WX = ["t2m_mean", "rh_mean", "pres_mean", "precip_sum", "t2m_mean_anom", "rh_mean_anom", "pres_mean_anom"]

def run(df: pd.DataFrame):
    df = df.sort_values("date")
    dates = df.date.unique()
    n = len(dates)
    tr, va = dates[:int(.7 * n)], dates[int(.7 * n):int(.85 * n)]
    trm, vam, tem = df[df.date.isin(tr)], df[df.date.isin(va)], df[~df.date.isin(list(tr) + list(va))]
    results = {}
    for name, feats in {"seismic_only": SEIS, "seismic_plus_weather": SEIS + [c for c in WX if c in df.columns]}.items():
        Xtr, ytr = trm[feats].fillna(0), trm.label_M4_7d
        Xva, yva = vam[feats].fillna(0), vam.label_M4_7d
        Xte, yte = tem[feats].fillna(0), tem.label_M4_7d
        base = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, class_weight="balanced", verbose=-1)
        base.fit(Xtr, ytr, eval_set=[(Xva, yva)])
        cal = base  # skip isotonic for PoC baseline; add calibration after more data
        for split, X, y in [("val", Xva, yva), ("test", Xte, yte)]:
            p = cal.predict_proba(X)[:, 1]
            results[f"{name}/{split}"] = {"pr_auc": float(average_precision_score(y, p)),
                "roc": float(roc_auc_score(y, p)) if y.nunique() > 1 else 0.0,
                "brier": float(brier_score_loss(y, p)), "pos_rate": float(y.mean())}
        results[name + "/model"] = cal
    return results

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--input", required=True); ap.add_argument("--experiment", default="panama-m4-7d")
    a = ap.parse_args()
    mlflow.set_experiment(a.experiment)
    df = pd.read_parquet(a.input)
    with mlflow.start_run():
        res = run(df)
        for k, v in res.items():
            if isinstance(v, dict): mlflow.log_metrics({k.replace("/", "_") + "__" + mk: mv for mk, mv in v.items()})
        print(res)
