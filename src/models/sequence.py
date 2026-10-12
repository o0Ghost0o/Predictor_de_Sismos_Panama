"""LSTM + Transformer (TFT-style attention) sequence models, 30-day windows per zone.
Compares against LightGBM baseline on identical time split."""
import numpy as np, pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import average_precision_score, roc_auc_score

W = 30
FEATS = ["n", "n7", "n30", "maxmag7", "logE7", "mean_depth", "days_since_m4",
         "rsi_n14", "rsi_E14", "vol_n30", "roc_E30", "benioff_since_m4",
         "t2m_mean", "rh_mean", "pres_mean", "precip_sum",
         "t2m_mean_anom", "rh_mean_anom", "pres_mean_anom"]

def make_sequences(df: pd.DataFrame):
    df = df.sort_values(["zone", "date"])
    dates = df.date.unique(); n = len(dates)
    cut1, cut2 = dates[int(.7 * n)], dates[int(.85 * n)]
    stats = df[df.date < cut1][FEATS].mean(), df[df.date < cut1][FEATS].std().replace(0, 1)
    out = {}
    for name, mask in [("train", df.date < cut1), ("val", (df.date >= cut1) & (df.date < cut2)),
                       ("test", df.date >= cut2)]:
        Xs, ys = [], []
        sub = df[mask]
        for z, g in df.groupby("zone"):
            g = g.sort_values("date").reset_index(drop=True)
            vals = ((g[FEATS] - stats[0]) / stats[1]).fillna(0).values.astype(np.float32)
            lab = g["label_M4_7d"].values
            idx = g[g.date.isin(sub[sub.zone == z].date)].index
            for i in idx:
                if i >= W - 1:
                    Xs.append(vals[i - W + 1:i + 1]); ys.append(lab[i])
        out[name] = (torch.tensor(np.array(Xs)), torch.tensor(np.array(ys), dtype=torch.float32))
    return out

class LSTMClf(nn.Module):
    def __init__(self, f, h=64):
        super().__init__()
        self.lstm = nn.LSTM(f, h, num_layers=2, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(h, 1)
    def forward(self, x):
        _, (hn, _) = self.lstm(x)
        return self.fc(hn[-1]).squeeze(-1)

class TransClf(nn.Module):
    """Transformer encoder + mean pooling (TFT-style attention, sin quantile heads)."""
    def __init__(self, f, h=64, heads=4, layers=2):
        super().__init__()
        self.proj = nn.Linear(f, h)
        self.pos = nn.Parameter(torch.randn(1, W, h) * 0.1)
        layer = nn.TransformerEncoderLayer(d_model=h, nhead=heads, batch_first=True, dropout=0.1)
        self.enc = nn.TransformerEncoder(layer, num_layers=layers)
        self.fc = nn.Linear(h, 1)
    def forward(self, x):
        h = self.proj(x) + self.pos[:, :x.size(1)]
        return self.fc(self.enc(h).mean(1)).squeeze(-1)

def fit(model, seq, epochs=15, lr=1e-3):
    Xtr, ytr = seq["train"]; Xva, _ = seq["val"]
    pos = (ytr == 0).sum() / max((ytr == 1).sum(), 1)
    loss = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float(pos)))
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    dl = DataLoader(TensorDataset(Xtr, ytr), batch_size=512, shuffle=True)
    model.train()
    for _ in range(epochs):
        for xb, yb in dl:
            opt.zero_grad(); l = loss(model(xb), yb); l.backward(); opt.step()
    return model

def scores(model, seq):
    model.eval(); res = {}
    with torch.no_grad():
        for split in ["val", "test"]:
            X, y = seq[split]
            p = torch.sigmoid(model(X)).numpy()
            res[split] = {"pr_auc": float(average_precision_score(y, p)),
                          "roc": float(roc_auc_score(y, p))}
    return res

if __name__ == "__main__":
    torch.manual_seed(0)
    df = pd.read_parquet("data/processed/dataset_full.parquet")
    df["date"] = pd.to_datetime(df["date"])
    seq = make_sequences(df)
    print({k: (v[0].shape, float(v[1].mean())) for k, v in seq.items()})
    for name, cls in [("lstm", LSTMClf), ("transformer", TransClf)]:
        m = fit(cls(len(FEATS)), seq)
        print(name, scores(m, seq))
        torch.save(m.state_dict(), f"models/{name}_m4.pt")
