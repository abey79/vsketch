import itertools

import numpy as np
import pytest

from .data import POINTS_1000
from .utils import line_count_equal


def _max_segment_length(line: np.ndarray) -> float:
    return np.max(np.abs(np.diff(line)))


@pytest.mark.parametrize("scale", [0.1, 1, 10, 100, 10000])
def test_detail_circle_epsilon_ok(vsk, scale):
    DETAIL = 0.1
    vsk.detail(DETAIL)
    vsk.scale(scale)
    vsk.circle(0, 0, radius=1)

    assert line_count_equal(vsk, 1)
    assert _max_segment_length(vsk.document.layers[1][0]) < DETAIL


PREVIOUSLY_FAILING_POINTS = [
    (
        (96.02651027 + 381.16243022j),
        (120.10840991 + 191.93815412j),
        (13.92826177 + 327.75350727j),
        (64.96878938 + 288.79348818j),
    ),
    (
        (677.24212994 + 189.00554785j),
        (936.94403821 + 333.44931666j),
        (412.61003955 + 72.01428024j),
        (553.20261885 + 134.64983253j),
    ),
    (
        (96.02651027 + 381.16243022j),
        (120.10840991 + 191.93815412j),
        (147.20916819 + 567.45907791j),
        (13.92826177 + 327.75350727j),
    ),
]


@pytest.mark.parametrize("scale", [0.1, 1, 10, 100])
@pytest.mark.parametrize(
    "points",
    list(itertools.combinations(POINTS_1000, 4)) + PREVIOUSLY_FAILING_POINTS,  # type: ignore
)
def test_detail_bezier_epsilon_ok(vsk, scale, points):
    DETAIL = 0.1
    vsk.detail(DETAIL)
    vsk.scale(scale)
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
    assert _max_segment_length(vsk.document.layers[1][0]) < DETAIL
