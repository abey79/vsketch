import numpy as np
import pytest

from .utils import line_count_equal, line_exists

POLYGON = np.array([0, 1, 3 + 1j, 4 - 2j])


@pytest.mark.parametrize(
    ["scale", "expected"],
    [
        [(1, 1), POLYGON],
        [(2, 2), 2 * POLYGON],
        [(2, None), 2 * POLYGON],
        [(2, 3), 2 * POLYGON.real + 3j * POLYGON.imag],
        [("in", None), 96.0 * POLYGON],
        [("2in", 3), 2 * 96 * POLYGON.real + 3j * POLYGON.imag],
    ],
)
def test_scale(vsk, scale, expected):
    vsk.scale(*scale)
    vsk.polygon(POLYGON.real, POLYGON.imag)

    assert line_count_equal(vsk, 1)
    # noinspection PyTypeChecker
    assert line_exists(vsk, expected)


def test_scale_no_y(vsk):
    vsk.scale(2)
    vsk.polygon(POLYGON.real, POLYGON.imag)

    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, 2 * POLYGON)


def test_resetMatrix(vsk):
    vsk.scale(10, 2)
    vsk.resetMatrix()
    vsk.polygon(POLYGON.real, POLYGON.imag)

    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, POLYGON)
