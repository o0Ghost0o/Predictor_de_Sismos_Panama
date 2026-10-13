"""Procedencia del catalogo: cada evento expone fuente y enlace verificable."""
from src.serve.app import event_url


def test_usgs_enlaza_a_eventpage():
    url = event_url("us6000u18k", "usgs")
    assert url == "https://earthquake.usgs.gov/earthquakes/eventpage/us6000u18k"


def test_igc_enlaza_al_portal():
    # El detalle ultimosismo.html rota y no se guarda: se enlaza el portal.
    url = event_url("igc-2026-10-13-11:59:29AM-9.199--76.267-7.2", "igc")
    assert url == "https://sismosgeociencias.up.ac.pa/"


def test_sismolive_y_emsc_enlazan_a_su_portal():
    assert event_url("sl-emsc-20260804_0000232", "emsc") == "https://www.emsc.eu/"
    assert event_url("sl-igc-1791847235", "igc") == "https://sismosgeociencias.up.ac.pa/"
    assert event_url("sl-123", "sismolive") == "https://sismolive.mupa.gob.pa/"


def test_sin_id_no_hay_enlace():
    assert event_url(None, "usgs") is None
    assert event_url("", "usgs") is None


def test_nan_no_rompe():
    import math
    assert event_url(math.nan, math.nan) is None
    assert event_url("us6000u18k", math.nan) == \
        "https://earthquake.usgs.gov/earthquakes/eventpage/us6000u18k"


def test_quakes_devuelve_url_para_todo_el_catalogo():
    """Regresion: una fila con src/id vacio no debe tumbar /quakes
    (el frontend muestra '0 eventos en rango' ante un 500)."""
    from src.serve.app import quakes
    rows = quakes(minmag=0.0, limit=5000)
    assert len(rows) > 0
    assert all("url" in r and "src" in r for r in rows)
