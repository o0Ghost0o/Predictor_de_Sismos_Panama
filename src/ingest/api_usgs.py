"""USGS FDSN ingest for Panama bbox. Validated: earthquake.usgs.gov/fdsnws/event/1."""
import argparse, time, requests, pandas as pd

BASE = "https://earthquake.usgs.gov/fdsnws/event/1/query"
BBOX = dict(minlatitude=6.5, maxlatitude=10.0, minlongitude=-83.5, maxlongitude=-77.0)

def fetch(start: str, end: str, minmag: float = 2.5) -> pd.DataFrame:
    params = {"format": "geojson", "starttime": start, "endtime": end,
              "minmagnitude": minmag, "orderby": "time", **BBOX}
    r = requests.get(BASE, params=params, timeout=60)
    r.raise_for_status()
    feats = r.json().get("features", [])
    rows = []
    for f in feats:
        p, g = f["properties"], f["geometry"]
        lon, lat, depth = g["coordinates"]
        rows.append({"time": pd.to_datetime(p["time"], unit="ms", utc=True),
                     "lat": lat, "lon": lon, "depth": depth,
                     "mag": p.get("mag"), "magType": p.get("magType"),
                     "place": p.get("place"), "id": f["id"]})
    if not rows:
        return pd.DataFrame(columns=["time", "lat", "lon", "depth", "mag", "magType", "place", "id"])
    df = pd.DataFrame(rows).dropna(subset=["mag"]).sort_values("time").reset_index(drop=True)
    return df

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True); ap.add_argument("--end", required=True)
    ap.add_argument("--minmag", type=float, default=4.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import os; os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    df = fetch(a.start, a.end, a.minmag)
    df.to_parquet(a.out, index=False)
    print(f"saved {len(df)} events -> {a.out}" + (f" | M range {df.mag.min():.1f}-{df.mag.max():.1f}" if len(df) else " (quiet window — widen dates)"))
