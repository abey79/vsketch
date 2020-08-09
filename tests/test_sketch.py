import numpy as np

import vsketch

from .utils import line_count_equal, line_exists

UNIT_SQUARE = np.array([0, 1, 1 + 1j, 1j, 0])


# noinspection DuplicatedCode
def test_sketch(vsk):
    sub = vsketch.Vsketch()
    sub.polygon(UNIT_SQUARE.real, UNIT_SQUARE.imag)

    vsk.sketch(sub)
    vsk.translate(2, 0)
    vsk.sketch(sub)
    vsk.translate(0, 2)
    vsk.sketch(sub)
    vsk.translate(-2, 0)
    vsk.sketch(sub)

    assert line_count_equal(vsk, 4)
    assert line_exists(vsk, UNIT_SQUARE)
    assert line_exists(vsk, UNIT_SQUARE + 2)
    assert line_exists(vsk, UNIT_SQUARE + 2j)
    assert line_exists(vsk, UNIT_SQUARE + 2 + 2j)


# noinspection DuplicatedCode
def test_sketch_layers(vsk):
    sub = vsketch.Vsketch()
    sub.stroke(5)
    sub.polygon(UNIT_SQUARE.real, UNIT_SQUARE.imag)
    sub.stroke(7)
    sub.polygon(UNIT_SQUARE.real, UNIT_SQUARE.imag)

    vsk.sketch(sub)
    vsk.translate(2, 0)
    vsk.sketch(sub)
    vsk.translate(0, 2)
    vsk.sketch(sub)
    vsk.translate(-2, 0)
    vsk.sketch(sub)

    assert line_count_equal(vsk, (5, 4), (7, 4))


def test_sketch_recursive(vsk):
    vsk.polygon(UNIT_SQUARE.real, UNIT_SQUARE.imag)
    with vsk.pushMatrix():
        vsk.translate(2, 0)
        vsk.sketch(vsk)

    with vsk.pushMatrix():
        vsk.translate(0, 2)
        vsk.sketch(vsk)

    assert line_count_equal(vsk, 4)
    assert line_exists(vsk, UNIT_SQUARE)
    assert line_exists(vsk, UNIT_SQUARE + 2)
    assert line_exists(vsk, UNIT_SQUARE + 2j)
    assert line_exists(vsk, UNIT_SQUARE + 2 + 2j)
