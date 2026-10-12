"""IGC-UPA (sismosgeociencias.up.ac.pa): lista publica con eventos M1.7+ (bajo USGS).
Sin archivo historico: se sondea como feed live y se anexa por (tiempo,lat,lon,mag)."""
import re, html
import pandas as pd
import requests

URL = "https://sismosgeociencias.up.ac.pa/"
PANAMA_UTC_OFFSET = 5  # hora local fija, sin DST

def fetch_igc(timeout: int = 90) -> pd.DataFrame:
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    r.encoding = "utf-8"
    rows = re.findall(r"<tr>(.*?)</tr>", r.text, re.S)
    out = []
    for row in rows:
        cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        if len(cells) < 8 or not re.match(r"^\d{4}-\d{2}-\d{2}$", cells[1] or ""):
            continue
        try:
            t = pd.to_datetime(cells[1] + " " + cells[2]) + pd.Timedelta(hours=PANAMA_UTC_OFFSET)
            out.append({"time": t.tz_localize("UTC"), "lat": float(cells[3]), "lon": float(cells[4]),
                        "depth": float(re.sub(r"[^0-9.]", "", cells[5]) or 10),
                        "mag": float(cells[6]), "magType": "ML",
                        "place": cells[7][:120], "estado": cells[0],
                        "id": f"igc-{cells[1]}-{cells[2]}-{cells[3]}-{cells[4]}-{cells[6]}",
                        "src": "igc"})
        except (ValueError, IndexError):
            continue
    df = pd.DataFrame(out).drop_duplicates("id").sort_values("time").reset_index(drop=True)
    return df

if __name__ == "__main__":
    df = fetch_igc()
    print(f"{len(df)} eventos, M {df.mag.min():.1f}-{df.mag.max():.1f}, M<4: {(df.mag < 4).sum()}")
    df.to_parquet("data/raw/quakes_igc.parquet", index=False)
