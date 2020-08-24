from typing import Sequence, Tuple

import numpy as np
import pytest

import vsketch

from .utils import line_count_equal, line_exists


@pytest.mark.parametrize(
    ["data", "mode", "expected"],
    [
        [(0, 0, 2, 4), "corner", (0, 2, 2 + 4j, 4j, 0)],
        [(1, 2, 5, 4), "corners", (1 + 2j, 5 + 2j, 5 + 4j, 1 + 4j, 1 + 2j)],
        [(3, 3, 1, 2), "center", (2.5 + 2j, 3.5 + 2j, 3.5 + 4j, 2.5 + 4j, 2.5 + 2j)],
        [(3, 3, 1, 2), "radius", (2 + 1j, 4 + 1j, 4 + 5j, 2 + 5j, 2 + 1j)],
    ],
)
def test_rect_mode_rect_success(
    vsk: vsketch.Vsketch,
    data: Tuple[float, float, float, float],
    mode: str,
    expected: Sequence[float],
) -> None:
    vsk.rectMode(mode)
    vsk.rect(*data)
    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, np.array(expected, dtype=complex), strict=False)


# noinspection DuplicatedCode
@pytest.mark.parametrize(
    ["data", "mode", "expected"],
    [
        [(2, 2, 2.5), "corner", (2 + 2j, 4.5 + 2j, 4.5 + 4.5j, 2 + 4.5j, 2 + 2j)],
        [(1, 2, 5), "corners", (1 + 2j, 6 + 2j, 6 + 7j, 1 + 7j, 1 + 2j)],
        [(3, 3, 2), "center", (2 + 2j, 4 + 2j, 4 + 4j, 2 + 4j, 2 + 2j)],
        [(1.5, 3, 1), "radius", (0.5 + 2j, 2.5 + 2j, 2.5 + 4j, 0.5 + 4j, 0.5 + 2j)],
    ],
)
def test_rect_mode_square_success(
    vsk: vsketch.Vsketch,
    data: Tuple[float, float, float],
    mode: str,
    expected: Sequence[float],
) -> None:
    vsk.rectMode(mode)
    vsk.square(*data)
    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, np.array(expected, dtype=complex), strict=False)


def test_rect_mode_fail(vsk: vsketch.Vsketch) -> None:
    with pytest.raises(ValueError):
        vsk.rectMode("jumbo")
