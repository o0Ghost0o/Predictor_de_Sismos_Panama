"""SismoLive MUPA (sismolive.mupa.gob.pa): agregador USGS+EMSC+IGC con GeoJSON
paginable (from/to). Es la fuente densa multi-origen del catalogo."""
import pandas as pd
import requests

BASE = "https://sismolive.mupa.gob.pa/api/v1/earthquakes/geojson"
BBOX = "-83.5,6.5,-77,10"


def fetch_sismolive(start: str, end: str, minmag: float = 0.0) -> pd.DataFrame:
    """Una ventana [start, end). Columnas catalogo + portal_id/usgs_id/srcs."""
    r = requests.get(BASE, params={"bbox": BBOX, "limit": 2000, "minMagnitude": minmag,
                                   "from": start, "to": end},
                     timeout=90, headers={"User-Agent": "SismosPanama-PoC/1.0"})
    r.raise_for_status()
    out = []
    for f in r.json().get("features", []):
        p = f.get("properties", {}) or {}
        g = (f.get("geometry", {}) or {}).get("coordinates", [None, None])
        srcs = p.get("sources", []) or []
        try:
            out.append({
                "portal_id": f.get("id"),
                "time": pd.to_datetime(p.get("eventTime"), utc=True),
                "lat": float(g[1]), "lon": float(g[0]),
                "depth": float(p.get("depthKm")) if p.get("depthKm") is not None else 10.0,
                "mag": float(p.get("magnitude")),
                "magType": (p.get("magnitudeType") or "ml")[:8],
                "place": (p.get("displayPlace") or p.get("placeRaw") or "")[:160],
                "estado": p.get("status"),
                "srcs": ";".join(s.get("code", "") for s in srcs),
                "usgs_id": next((s.get("sourceEventId") for s in srcs
                                 if s.get("code") == "USGS"), None)})
        except (TypeError, ValueError):
            continue
    df = pd.DataFrame(out)
    if len(df):
        df = df.drop_duplicates("portal_id").sort_values("time").reset_index(drop=True)
    return df


def merge_portal(old: pd.DataFrame, sl: pd.DataFrame):
    """Cruza filas del portal contra el catalogo: enlazadas a USGS existentes
    se descartan (queda la nuestra), resto con guardia espacio-temporal
    (120 s / 0.3°). Devuelve (merged, n_nuevos)."""
    import numpy as np
    old = old.copy()
    old["time"] = pd.to_datetime(old["time"], utc=True)
    sl = sl[~sl.usgs_id.isin(set(old.id))].copy()
    ut = old.time.values.astype("datetime64[s]").astype(float)
    olat, olon = old.lat.values, old.lon.values
    keep = []
    for r in sl.itertuples():
        try:
            t = r.time.value / 1e9
        except AttributeError:
            continue
        near = np.where(np.abs(ut - t) < 120)[0]
        if len(near) and float(np.sqrt((olat[near] - r.lat) ** 2 +
                                        (olon[near] - r.lon) ** 2).min()) < 0.3:
            continue
        keep.append(r.Index)
    add = sl.loc[keep].copy()
    add["id"] = "sl-" + add.portal_id.astype(str)
    add["src"] = add.srcs.str.split(";").str[0].str.lower().replace("", "sismolive")
    add["place"] = add.place.fillna("")
    cols = ["id", "time", "lat", "lon", "depth", "mag", "magType", "place", "estado", "src"]
    merged = pd.concat([old, add[cols]], ignore_index=True).drop_duplicates("id", keep="first")
    return merged.sort_values("time").reset_index(drop=True), len(add)
