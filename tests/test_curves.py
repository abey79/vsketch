import itertools

import pytest

from .data import POINTS_1000
from .utils import line_count_equal


@pytest.mark.parametrize("points", list(itertools.combinations(POINTS_1000, 4)))
def test_bezier_endpoints_included(vsk, points):
    vsk.bezier(
        points[0].real,
        points[0].imag,
        points[1].real,
        points[1].imag,
        points[2].real,
        points[2].imag,
        points[3].real,
        points[3].imag,
    )

    assert line_count_equal(vsk, 1)
    assert vsk.document.layers[1][0][0] == points[0]
    assert vsk.document.layers[1][0][-1] == points[-1]
