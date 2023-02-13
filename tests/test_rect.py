from typing import Sequence, Tuple

import numpy as np
import pytest

import vsketch

from .utils import bounds_equal, length_equal, line_count_equal, line_exists


def test_rect_default_success(vsk: vsketch.Vsketch) -> None:
    vsk.rect(0, 0, 2, 4)
    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, np.array([0, 2, 2 + 4j, 4j, 0], dtype=complex), strict=False)
    assert length_equal(vsk, (2 + 4) * 2)


@pytest.mark.parametrize(
    ["data", "mode", "expected"],
    [
        [(0, 0, 2, 4), "corner", (0, 2, 2 + 4j, 4j, 0)],
        [(3, 3, 1, 2), "center", (2.5 + 2j, 3.5 + 2j, 3.5 + 4j, 2.5 + 4j, 2.5 + 2j)],
        [(1, 2, 5, 4), "corners", (1 + 2j, 5 + 2j, 5 + 4j, 1 + 4j, 1 + 2j)],
        # 'corners' mode finds the top-left corner
        [(5, 4, 1, 2), "corners", (1 + 2j, 5 + 2j, 5 + 4j, 1 + 4j, 1 + 2j)],
        [(1, 4, 5, 2), "corners", (1 + 2j, 5 + 2j, 5 + 4j, 1 + 4j, 1 + 2j)],
        [(5, 2, 1, 4), "corners", (1 + 2j, 5 + 2j, 5 + 4j, 1 + 4j, 1 + 2j)],
        [(3, 3, 1, 2), "radius", (2 + 1j, 4 + 1j, 4 + 5j, 2 + 5j, 2 + 1j)],
    ],
)
def test_rect_mode_success(
    vsk: vsketch.Vsketch,
    data: Tuple[float, float, float, float],
    mode: str,
    expected: Sequence[float],
) -> None:
    vsk.rect(*data, mode=mode)  # type: ignore
    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, np.array(expected, dtype=complex), strict=False)


def test_rect_arg_fail(vsk: vsketch.Vsketch) -> None:
    # vsk.rect() expects 3 float args + optional `h` float and `mode` arg
    with pytest.raises(TypeError):
        # noinspection PyArgumentList
        vsk.rect(0, 4, mode="corners")  # type: ignore

    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        vsk.rect("hey", 0, 2.5, 4)  # type: ignore

    # vsk.rect() expects `mode` parameter to be one of "corner", "corners", "center", "radius"
    with pytest.raises(ValueError):
        vsk.rect(0, 0, 2, 4, mode="jumbo")


@pytest.mark.parametrize(
    ["data", "expected"],
    [
        [(0, 0, 2, 4, 1, 0, 1.5, 1), (0, 0, 2, 4)],
        # radii should be scaled to fit
        [(0, 0, 5, 4, 8), (0, 0, 5, 4)],
    ],
)
def test_rect_round_corners_success(
    vsk: vsketch.Vsketch, data: Sequence[float], expected: Tuple[float, float, float, float]
) -> None:
    vsk.rect(*data)  # type: ignore
    assert line_count_equal(vsk, 1)
    assert bounds_equal(vsk, *expected)
