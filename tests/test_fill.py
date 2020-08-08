import pytest
import vpype as vp
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import unary_union

from vsketch.fill import generate_fill
from vsketch.utils import complex_to_2d


def _simulate_pen(lc: vp.LineCollection, lw: float) -> MultiPolygon:
    return unary_union(
        [
            LineString(complex_to_2d(line)).buffer(lw, join_style=2, mitre_limit=10.0)
            for line in lc
        ]
    )


@pytest.mark.skip(reason="this cannot work until Toblerity/Shapely#958 is fixed")
@pytest.mark.parametrize("line", [vp.circle(0, 0, 10), vp.rect(0, 0, 10, 20)])
@pytest.mark.parametrize("lw", [0.01, 0.1, 1, 10])
def test_fill(line, lw):
    """Let's use some computational geometry to ensure the fill pattern properly covers the
    desired area
    """

    p = Polygon(complex_to_2d(line))
    fill_lc = generate_fill(line, lw)

    overfill_p = _simulate_pen(fill_lc, 1.2 * lw / 2)
    underfill_p = _simulate_pen(fill_lc, 0.8 * lw / 2)

    assert overfill_p.contains(p)
    assert p.contains(underfill_p)
