"""Parser IGC-UPA: enlaces ultimosismo + colapso de revisiones."""
import pandas as pd

from src.ingest.igc_up import _parse_links, collapse_revisions

HTML = """
<a href="ultimosismo.html?z=8&lt=7.54&ln=-80.83&p=20km&e=PRELIMINAR&h=1:56:41AM&f=2026-10-12&m=2.9&r=Al%20noroeste%20de%20Tonos%C3%AD">x</a>
<a href="ultimosismo.html?z=8&lt=7.545&ln=-80.831&p=20km&e=REVISADO&h=1:57:10AM&f=2026-10-12&m=2.9&r=Al%20noroeste%20de%20Tonos%C3%AD">x</a>
<a href="ultimosismo.html?z=8&lt=8.10&ln=-81.20&p=10km&e=REVISADO&h=3:00:00PM&f=2026-10-11&m=4.5&r=Otro%20lugar">x</a>
"""


def test_parse_links_extrae_campos():
    df = _parse_links(HTML)
    assert len(df) == 3
    r = df[df.estado == "PRELIMINAR"].iloc[0]
    assert r.lat == 7.54 and r.lon == -80.83 and r.mag == 2.9 and r.depth == 20.0
    assert r.src == "igc"
    assert str(r.time) == "2026-10-12 06:56:41+00:00"  # +5h Panama -> UTC
    assert "Tonos" in r.place


def test_collapse_queda_revisado():
    df = collapse_revisions(_parse_links(HTML))
    assert len(df) == 2
    assert df.estado.tolist() == ["REVISADO", "REVISADO"]
    assert df.mag.tolist() == [4.5, 2.9]
