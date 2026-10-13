"""Salud de los artefactos que la API necesita (evita el "API no disponible").

Se corre desde la raiz del repo: `make test` o `pytest tests/ -q`.
"""
import pickle

import pandas as pd


def test_quakes_catalog_readable():
    q = pd.read_parquet("data/raw/quakes_full.parquet")
    assert len(q) > 0
    assert {"time", "lat", "lon", "depth", "mag", "id"} <= set(q.columns)


def test_dataset_readable():
    df = pd.read_parquet("data/processed/dataset_full.parquet")
    assert len(df) > 0
    assert {"zone", "date"} <= set(df.columns)


def test_dataset_covers_recent_week():
    """El hindcast por fecha cae al ultimo row <= fecha: si el dataset se
    queda atras, todas las fechas recientes devuelven lo mismo sin avisar."""
    import datetime
    df = pd.read_parquet("data/processed/dataset_full.parquet")
    age = datetime.date.today() - pd.to_datetime(df.date.max()).date()
    assert age.days <= 14, f"dataset desactualizado: date_max hace {age.days} dias"


def test_model_bundle_loads():
    bundle = pickle.load(open("models/lgbm_full.pkl", "rb"))
    assert "features" in bundle
    assert len(bundle["features"]) > 0
