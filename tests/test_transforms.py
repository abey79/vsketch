import numpy as np
import pytest

from .utils import bounds_equal, line_count_equal, line_exists

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


def test_translate(vsk):
    vsk.translate(12, 23)
    vsk.polygon(POLYGON.real, POLYGON.imag)

    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, POLYGON + 12 + 23j)


def test_rotate_radians(vsk):
    vsk.rotate(np.pi / 2)
    vsk.rect(5, 0, 1, 2)

    assert line_count_equal(vsk, 1)
    assert bounds_equal(vsk, -2, 5, 0, 6)


def test_rotate_deg_rad(vsk):
    vsk.rotate(np.pi / 2)
    vsk.rotate(-90, degrees=True)
    vsk.polygon(POLYGON.real, POLYGON.imag)

    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, POLYGON)


def test_resetMatrix(vsk):
    vsk.scale(10, 2)
    vsk.resetMatrix()
    vsk.polygon(POLYGON.real, POLYGON.imag)

    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, POLYGON)


def test_resetMatrix_context(vsk):
    vsk.scale(10, 2)
    vsk.rotate(42)
    with vsk.resetMatrix():
        vsk.polygon(POLYGON)

    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, POLYGON)


def test_pushMatrix(vsk):
    vsk.pushMatrix()
    vsk.scale(100, 200)
    vsk.rotate(34)
    vsk.popMatrix()

    vsk.polygon(POLYGON.real, POLYGON.imag)
    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, POLYGON)


def test_pushMatrix_context(vsk):
    with vsk.pushMatrix():
        vsk.scale(100, 200)
        vsk.rotate(34)

    vsk.polygon(POLYGON.real, POLYGON.imag)
    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, POLYGON)
