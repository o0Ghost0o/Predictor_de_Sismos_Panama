"""Features GNSS NGL por zona: velocidad 30d (tasa de carga) + salto residual (detector cosismico).
Estaciones: BOCAS=CN20, CHIRIQUI=VLCN, CENTRAL=CN28, AZUERO=CN33, DARIEN=CN34.
Uso: python -m src.features.add_gnss  (lee dataset_full, escribe dataset_gnss)"""
import numpy as np, pandas as pd

MAP = {"BOCAS": "CN20", "CHIRIQUI": "VLCN", "CENTRAL": "CN28", "AZUERO": "CN33", "DARIEN": "CN34"}
COLS = ["site", "date", "dy", "mjd", "w", "d", "rlon", "e0", "east", "n0", "north",
        "u0", "up", "ant", "se", "sn", "su", "cen", "ceu", "cnu", "lat", "lon", "h"]

def station_feats(st: str) -> pd.DataFrame:
    df = pd.read_csv(f"data/raw/gnss_{st}.tenv3", sep=r"\s+", names=COLS, skiprows=1)
    df["date"] = pd.to_datetime(df["date"], format="%y%b%d")
    df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    h = np.sqrt(df.east ** 2 + df.north ** 2)
    # velocidad trailing 30d (ajuste lineal, mm/dia)
    vel = [np.polyfit(np.arange(max(0, i - 29), i + 1),
                      h[max(0, i - 29):i + 1], 1)[0] * 1000 if i >= 7 else 0.0 for i in range(len(h))]
    med = h.rolling(30, min_periods=7).median()
    jump = ((h - med).abs() * 1000).fillna(0)  # salto vs mediana 30d, mm
    return pd.DataFrame({"date": df.date, "gnss_vel30": vel, "gnss_jump": jump,
                         "gnss_span_d": df.date.sub(df.date.iloc[0]).dt.days})

def main():
    df = pd.read_parquet("data/processed/dataset_full.parquet")
    df["date"] = pd.to_datetime(df["date"])
    parts = []
    for z, st in MAP.items():
        g = station_feats(st)
        print(z, st, len(g), "dias", g.date.min().date(), "->", g.date.max().date(), flush=True)
        parts.append(g.assign(zone=z))
    gn = pd.concat(parts, ignore_index=True)
    out = df.merge(gn, on=["zone", "date"], how="left").fillna({"gnss_vel30": 0, "gnss_jump": 0})
    out.to_parquet("data/processed/dataset_gnss.parquet", index=False)
    print(f"saved {len(out)} rows, cobertura gnss={(out.gnss_span_d > 0).mean():.2f}")

if __name__ == "__main__":
    main()
