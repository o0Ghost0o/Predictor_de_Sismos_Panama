"""Ingesta SismoLive MUPA: cruce contra el catalogo sin duplicar."""
import pandas as pd

from src.ingest.sismolive import merge_portal


def _sl():
    return pd.DataFrame([
        {"portal_id": "emsc-1", "time": pd.Timestamp("2026-10-10 12:00", tz="utc"),
         "lat": 7.5, "lon": -80.5, "depth": 10.0, "mag": 4.2, "magType": "ml",
         "place": "Azuero", "estado": "reviewed", "srcs": "EMSC", "usgs_id": "usgs-x1"},
        {"portal_id": "emsc-2", "time": pd.Timestamp("2026-10-10 12:01", tz="utc"),
         "lat": 7.51, "lon": -80.51, "depth": 10.0, "mag": 4.2, "magType": "ml",
         "place": "Azuero dup", "estado": "reviewed", "srcs": "EMSC", "usgs_id": None},
        {"portal_id": "emsc-3", "time": pd.Timestamp("2026-10-11 12:00", tz="utc"),
         "lat": 8.5, "lon": -82.5, "depth": 33.0, "mag": 2.8, "magType": "ml",
         "place": "Chiriqui", "estado": "automatic", "srcs": "EMSC", "usgs_id": None},
    ])


def _old():
    return pd.DataFrame([
        {"id": "usgs-x1", "time": pd.Timestamp("2026-10-10 12:00", tz="utc"),
         "lat": 7.5, "lon": -80.5, "depth": 10.0, "mag": 4.2, "magType": "mw",
         "place": "Azuero USGS", "estado": None, "src": "usgs"},
    ])


def test_merge_descarta_enlazado_y_duplicado():
    merged, n = merge_portal(_old(), _sl())
    assert n == 1  # solo emsc-3 es nuevo
    row = merged[merged.id == "sl-emsc-3"].iloc[0]
    assert row.src == "emsc" and row.mag == 2.8 and row.place == "Chiriqui"
    assert "sl-emsc-1" not in set(merged.id)  # enlazado a USGS existente
    assert "sl-emsc-2" not in set(merged.id)  # duplicado espacio-temporal
