"""El nivel del dashboard debe responder a secuencias activas.

Regresion: la calibracion isotonica anterior aplanaba todo score alto
(crudo 0.97 -> 0.23 en M4; techos 0.028/0.023 en M5/M6), asi que los niveles
4/5/6 eran inalcanzables y todo quedaba en Nivel 3 aunque ETAS marcara
p24 = 1.0. Estos tests fijan el mecanismo: mapas monotonos, techos que
alcanzan los umbrales de nivel_texto, y fila viva de hoy con features
completos para servir /risk sin rezago.
"""
import pickle

import numpy as np
import pandas as pd


def _bundle():
    return pickle.load(open("models/lgbm_full.pkl", "rb"))


def test_calibracion_monotona_y_alcanza_umbrales():
    from src.serve.app import nivel_texto
    b = _bundle()
    grid = np.linspace(0, 1, 51)
    for c, umbral in (("label_M4_7d", 0.50), ("label_M5_7d", 0.35),
                      ("label_M6_7d", 0.30)):
        v = b["cal"][c].predict(grid)
        assert bool(np.all(np.diff(v) >= 0)), f"{c}: mapa no monotono"
    assert float(b["cal"]["label_M4_7d"].predict([0.97])[0]) >= 0.50, \
        "secuencia activa (crudo .97) debe cruzar el umbral de Nivel 4"
    assert float(b["cal"]["label_M5_7d"].predict([1.0])[0]) >= 0.35, \
        "techo M5 debe permitir Nivel 5 en extremos"
    assert nivel_texto(0.51, 0.0, 0.0)[0] == 4


def test_live_rows_hoy_completas():
    from src.features.live_row import live_rows
    from src.features.zones import ZONES
    b = _bundle()
    out = live_rows()
    assert set(out.zone) == set(ZONES) and out.date.nunique() == 1
    hoy = pd.Timestamp.now(tz="America/Panama").normalize().tz_localize(None)
    assert pd.to_datetime(out.date.iloc[0]).normalize() == hoy, \
        "la fila viva debe fecharse hoy (America/Panama), no ayer"
    faltan = [c for c in b["features"] if c not in out.columns]
    assert not faltan, f"features ausentes en fila viva: {faltan}"
