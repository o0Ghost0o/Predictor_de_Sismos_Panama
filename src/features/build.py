"""Build zone-day dataset: seismic features + weather join + M4+/7d label."""
import argparse, numpy as np, pandas as pd
from src.features.zones import assign_zone, ZONES

def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    """RSI estilo trading (Wilder) sobre tasa sísmica o energía: 0-100, 50 neutro."""
    d = s.diff()
    g, l = d.clip(lower=0), -d.clip(upper=0)
    ag = g.ewm(alpha=1 / n, min_periods=n).mean()
    al = l.ewm(alpha=1 / n, min_periods=n).mean()
    out = 100 - 100 / (1 + ag / al.replace(0, np.nan))
    return out.fillna(50)

def add_technical(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["zone", "date"]).copy()
    g = df.groupby("zone")
    df["rsi_n14"] = g["n"].transform(lambda s: rsi(s)).clip(0, 100)
    df["rsi_E14"] = g["energy"].transform(lambda s: rsi(s)).clip(0, 100)
    df["vol_n30"] = g["n"].transform(lambda s: s.rolling(30, min_periods=7).std()).fillna(0)
    df["roc_E30"] = g["energy"].transform(
        lambda s: s.rolling(30, min_periods=7).sum() / (s.rolling(90, min_periods=30).sum() + 1) - 1).fillna(0)
    # deformación de Benioff acumulada desde último M4+ (acumulación de strain)
    cum = []
    for z, gd in df.groupby("zone"):
        c, out = 0.0, []
        for _, r in gd.iterrows():
            c = 0.0 if r["m4"] > 0 else c + np.sqrt(r["energy"] + 1)
            out.append(c)
        cum.extend(out)
    df["benioff_since_m4"] = np.log10(np.array(cum) + 1)
    return df

def build(quakes: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    quakes["time"] = pd.to_datetime(quakes["time"], utc=True)
    quakes["zone"] = [assign_zone(la, lo) for la, lo in zip(quakes.lat, quakes.lon)]
    quakes = quakes.dropna(subset=["zone"]).copy()
    quakes["date"] = quakes["time"].dt.tz_convert("America/Panama").dt.tz_localize(None).dt.normalize()

    days = pd.date_range(quakes["date"].min(), quakes["date"].max(), freq="D")
    idx = pd.MultiIndex.from_product([list(ZONES), days], names=["zone", "date"]).to_frame(index=False)

    # daily seismic aggregates per zone
    q = quakes.copy()
    q["energy"] = 10 ** (1.5 * q["mag"])
    daily = q.groupby(["zone", "date"]).agg(n=("mag", "size"), maxmag=("mag", "max"),
        mean_depth=("depth", "mean"), energy=("energy", "sum")).reset_index()
    df = idx.merge(daily, on=["zone", "date"], how="left").fillna({"n": 0, "maxmag": 0, "energy": 0})
    df = df.sort_values(["zone", "date"])
    g = df.groupby("zone")
    df["n7"] = g["n"].transform(lambda s: s.rolling(7, min_periods=1).sum())
    df["n30"] = g["n"].transform(lambda s: s.rolling(30, min_periods=1).sum())
    df["maxmag7"] = g["maxmag"].transform(lambda s: s.rolling(7, min_periods=1).max())
    df["logE7"] = np.log10(df.groupby("zone")["energy"].transform(lambda s: s.rolling(7, min_periods=1).sum()) + 1)
    # days since last M4+
    m4 = quakes[quakes.mag >= 4.0].groupby(["zone", "date"]).size().reset_index(name="m4")
    df = df.merge(m4, on=["zone", "date"], how="left").fillna({"m4": 0})
    last = {}
    dsl = []
    for _, r in df.iterrows():
        if r["m4"] > 0: last[r["zone"]] = r["date"]
        dsl.append((r["date"] - last.get(r["zone"], r["date"])).days if r["zone"] in last else 999)
    df["days_since_m4"] = dsl
    df = add_technical(df)  # RSI + volatilidad + Benioff acumulado
    # label: any M4+ in next 7d same zone
    has = set(zip(m4.zone, m4.date))
    dates = {z: sorted([d for (zz, d) in has if zz == z]) for z in ZONES}
    def label(z, d):
        return int(any(d < x <= d + pd.Timedelta(days=7) for x in dates.get(z, [])))
    df["label_M4_7d"] = [label(z, d) for z, d in zip(df.zone, df.date)]
    # weather join
    weather["date"] = pd.to_datetime(weather["date"])
    df = df.merge(weather, on=["zone", "date"], how="left")
    return df

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quakes", required=True); ap.add_argument("--weather", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import os; os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    out = build(pd.read_parquet(a.quakes), pd.read_parquet(a.weather))
    out.to_parquet(a.out, index=False)
    print(f"saved {len(out)} rows, pos_rate={out.label_M4_7d.mean():.3f} -> {a.out}")
