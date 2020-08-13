from typing import Sequence

import numpy as np
import pytest

import vsketch

from .utils import line_count_equal, line_exists


def test_rect_default_success(vsk: vsketch.Vsketch):
    vsk.rect(0, 0, 2, 4)
    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, np.array([0, 2, 2 + 4j, 4j, 0], dtype=complex))


@pytest.mark.parametrize(
    ["data", "mode", "expected"],
    [
        [(0, 0, 2, 4), "corner", (0, 2, 2 + 4j, 4j, 0)],
        [(3, 3, 1, 2), "center", (2.5 + 2j, 3.5 + 2j, 3.5 + 4j, 2.5 + 4j, 2.5 + 2j)],
        [(1, 2, 5, 4), "corners", (1 + 2j, 5 + 2j, 5 + 4j, 1 + 4j, 1 + 2j)],
        # 'corners' mode finds the top-left corner
        [(5, 4, 1, 2), "corners", (1 + 2j, 5 + 2j, 5 + 4j, 1 + 4j, 1 + 2j)],
        [(3, 3, 1, 2), "radius", (2 + 1j, 4 + 1j, 4 + 5j, 2 + 5j, 2 + 1j)],
    ],
)
def test_rect_mode_succes(
    vsk: vsketch.Vsketch, data, mode: str, expected: Sequence[float],
):
    vsk.rect(*data, mode=mode)  # type: ignore
    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, np.array(expected, dtype=complex))


def test_rect_arg_fail(vsk: vsketch.Vsketch):
    # vsk.rect() expects 3 float args + optional `h` float and `mode` arg
    with pytest.raises(TypeError):
        vsk.rect(0, 4, mode="corners")  # type: ignore

    with pytest.raises(TypeError):
        vsk.rect("hey", 0, 2.5, 4)  # type: ignore

    # vsk.rect() expects `mode` parameter to be one of "corner", "corners", "center", "radius"
    with pytest.raises(ValueError):
        vsk.rect(0, 0, 2, 4, mode="jumbo")


# TODO: test round corners
