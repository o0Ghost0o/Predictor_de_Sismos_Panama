"""Open-Meteo archive ingest per zone centroid (hourly -> daily)."""
import argparse, requests, pandas as pd
from src.features.zones import ZONES, centroid

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"

def fetch_zone(zone: str, start: str, end: str) -> pd.DataFrame:
    lat, lon = centroid(zone)
    params = {"latitude": lat, "longitude": lon, "start_date": start[:10], "end_date": end[:10],
              "hourly": "temperature_2m,relative_humidity_2m,precipitation,surface_pressure",
              "timezone": "auto"}
    r = requests.get(ARCHIVE, params=params, timeout=60)
    r.raise_for_status()
    h = r.json()["hourly"]
    df = pd.DataFrame(h)
    df["time"] = pd.to_datetime(df["time"])
    df["date"] = df["time"].dt.date
    daily = df.groupby("date").agg(t2m_mean=("temperature_2m", "mean"),
        rh_mean=("relative_humidity_2m", "mean"), precip_sum=("precipitation", "sum"),
        pres_mean=("surface_pressure", "mean")).reset_index()
    daily["zone"] = zone
    daily["date"] = pd.to_datetime(daily["date"])
    # 30d climatology anomaly
    for c in ["t2m_mean", "rh_mean", "pres_mean"]:
        daily[c + "_anom"] = daily[c] - daily[c].rolling(30, min_periods=7).mean()
    return daily

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True); ap.add_argument("--end", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import os; os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    dfs = [fetch_zone(z, a.start, a.end) for z in ZONES]
    out = pd.concat(dfs, ignore_index=True)
    out.to_parquet(a.out, index=False)
    print(f"saved {len(out)} zone-days -> {a.out}")
