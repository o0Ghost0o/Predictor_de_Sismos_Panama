"""Reajuste ETAS en vivo sobre catalogo sintetico (no toca datos ni modelos reales)."""
import os
import pickle

import numpy as np
import pandas as pd

from src.models.etas import refit_recent


def _synth(path, zones=("CHIRIQUI", "AZUERO"), n=40, seed=7):
    from src.features.zones import centroid
    rng = np.random.default_rng(seed)
    base = pd.Timestamp("2024-01-01", tz="utc")
    rows = []
    for z in zones:
        la, lo = centroid(z)
        for i in range(n):
            rows.append({
                "id": f"{z}-{i}", "time": base + pd.Timedelta(days=float(i * 730 / n)),
                "lat": la + float(rng.normal(0, 0.2)), "lon": lo + float(rng.normal(0, 0.2)),
                "depth": 10.0, "mag": float(4.0 + rng.random() * 1.5),
                "magType": "ml", "place": z, "src": "test"})
    rows[0]["mag"] = 6.2  # un grande para que K tenga que moverse
    pd.DataFrame(rows).to_parquet(path, index=False)


def test_refit_fits_zones_and_records_trigger(tmp_path):
    src = str(tmp_path / "q.parquet")
    out = str(tmp_path / "etas.pkl")
    _synth(src)
    r = refit_recent(years=10, path=src, out=out, min_events=10, trigger="M6.2 test")
    assert set(r["zonas_reajustadas"]) == {"AZUERO", "CHIRIQUI"}
    assert r["conservadas"] == [] and r["trigger"] == "M6.2 test"
    b = pickle.load(open(out, "rb"))
    assert set(b["thetas"]) == {"AZUERO", "CHIRIQUI"}
    for th in b["thetas"].values():
        assert len(th) == 5 and all(np.isfinite(th))
    assert b["refit_ts"] and b["trigger"] == "M6.2 test"
    assert not [f for f in os.listdir(tmp_path) if f.endswith(".tmp") or "tmp" in f and f.endswith(".pkl")]


def test_refit_keeps_zone_without_enough_data(tmp_path):
    src = str(tmp_path / "q.parquet")
    out = str(tmp_path / "etas.pkl")
    _synth(src)
    refit_recent(years=10, path=src, out=out, min_events=10, trigger="base")
    antes = pickle.load(open(out, "rb"))["thetas"]["AZUERO"]
    _synth(src, zones=("CHIRIQUI",), n=40, seed=11)  # AZUERO desaparece
    r = refit_recent(years=10, path=src, out=out, min_events=10, trigger="solo-chiriqui")
    assert r["conservadas"] == ["AZUERO"]
    despues = pickle.load(open(out, "rb"))["thetas"]["AZUERO"]
    assert antes == despues
