"""La capa de calor no debe usar google.maps.visualization.HeatmapLayer.

Google elimino HeatmapLayer en Maps JavaScript API v3.65; mapa.vue dibuja el
calor con un OverlayView + canvas propio. Este test estatico evita que la
dependencia eliminada vuelva a colarse.

Se corre desde la raiz del repo: `make test` o `pytest tests/ -q`.
"""
from pathlib import Path

MAPA = Path("web/pages/mapa.vue")


def _src() -> str:
    return MAPA.read_text(encoding="utf-8")


def test_sin_visualization_heatmap_layer():
    src = _src()
    assert "maps.visualization" not in src
    assert "libraries=visualization" not in src


def test_calor_con_overlay_propio():
    src = _src()
    assert "OverlayView" in src
    assert "createElement('canvas')" in src
    # El peso por magnitud y el radio original se conservan.
    assert "Math.pow(2, q.mag - 4)" in src
    assert "buildHeat" in src


def test_calor_sin_sumar_luz():
    # 'lighter' suma luz por mancha y el enjambre quema a blanco;
    # con 'source-over' lo denso converge al color del dato.
    src = _src()
    assert "source-over" in src
    assert "'lighter'" not in src
