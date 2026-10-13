"""IGC-UPA (sismosgeociencias.up.ac.pa): lista publica con eventos M1.7+ (bajo USGS).

La pagina es un listado rodante (sin archivo historico): cada evento enlaza a
`ultimosismo.html?lt=..&ln=..&p=..km&e=..&h=..&f=..&m=..&r=..`, de donde se
extrae todo. Las revisiones (PRELIMINAR -> REVISADO) del mismo sismo se
colapsan quedando la REVISADO."""
import re
import html as _html
from urllib.parse import unquote, parse_qsl
import pandas as pd
import requests

URL = "https://sismosgeociencias.up.ac.pa/"
PANAMA_UTC_OFFSET = 5  # hora local fija, sin DST


def _parse_links(text: str) -> pd.DataFrame:
    out = []
    for m in re.finditer(r"ultimosismo\.html\?([^\"'\s<>]+)", text):
        qs = dict(parse_qsl(m.group(1)))
        try:
            f, h = qs["f"], qs["h"]
            try:
                t = pd.to_datetime(f + " " + h, format="%Y-%m-%d %I:%M:%S%p")
            except ValueError:
                t = pd.to_datetime(f + " " + h, format="%Y-%m-%d %I:%M%p")
            t = (t + pd.Timedelta(hours=PANAMA_UTC_OFFSET)).tz_localize("UTC")
            lat, lon = float(qs["lt"]), float(qs["ln"])
            mag = float(qs["m"])
            out.append({"time": t, "lat": lat, "lon": lon,
                        "depth": float(re.sub(r"[^0-9.]", "", qs.get("p", "")) or 10),
                        "mag": mag, "magType": "ML",
                        "place": unquote(qs.get("r", ""))[:120],
                        "estado": qs.get("e", ""),
                        "id": f"igc-{f}-{h}-{lat:.3f}-{lon:.3f}-{mag}",
                        "src": "igc"})
        except (ValueError, KeyError):
            continue
    df = pd.DataFrame(out)
    if len(df):
        df = df.drop_duplicates("id").sort_values("time").reset_index(drop=True)
    return df


def _parse_rows(text: str) -> pd.DataFrame:
    """Formato anterior (<td>): respaldo si la pagina vuelve a cambiar."""
    rows = re.findall(r"<tr>(.*?)</tr>", text, re.S)
    out = []
    for row in rows:
        cells = [_html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
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
    df = pd.DataFrame(out)
    if len(df):
        df = df.drop_duplicates("id").sort_values("time").reset_index(drop=True)
    return df


def collapse_revisions(df: pd.DataFrame) -> pd.DataFrame:
    """Colapsa revisiones del mismo sismo (ventana 120 s, 0.1°, |dm|<=0.3):
    queda la REVISADO; en enjambre los eventos distintos sobreviven."""
    if not len(df):
        return df
    df = df.sort_values("time").reset_index(drop=True)
    keep = [True] * len(df)
    for i in range(1, len(df)):
        j = i - 1
        while j >= 0 and keep[j] is False:
            j -= 1
        if j < 0:
            continue
        a, b = df.iloc[j], df.iloc[i]
        dt = abs((b.time - a.time).total_seconds())
        dd = abs(b.lat - a.lat) + abs(b.lon - a.lon)
        if dt <= 120 and dd <= 0.1 and abs(b.mag - a.mag) <= 0.3:
            if b.estado == "REVISADO":
                keep[j] = False
            else:
                keep[i] = False
    return df[keep].reset_index(drop=True)


def fetch_igc(timeout: int = 90) -> pd.DataFrame:
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    r.encoding = "utf-8"
    df = _parse_links(r.text)
    if not len(df):
        df = _parse_rows(r.text)
    return collapse_revisions(df)

if __name__ == "__main__":
    df = fetch_igc()
    print(f"{len(df)} eventos, M {df.mag.min():.1f}-{df.mag.max():.1f}, M<4: {(df.mag < 4).sum()}")
    df.to_parquet("data/raw/quakes_igc.parquet", index=False)
