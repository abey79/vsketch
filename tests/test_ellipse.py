from typing import Sequence, Tuple

import pytest

import vsketch

from .utils import bounds_equal, line_count_equal


def test_ellipse_default_success(vsk: vsketch.Vsketch) -> None:
    vsk.detail(0.01)
    vsk.ellipse(2, 2, 1, 2)
    assert line_count_equal(vsk, 1)
    assert bounds_equal(vsk, 1.5, 1, 2.5, 3)


@pytest.mark.parametrize(
    ["data", "mode", "expected"],
    [
        [(2, 2, 1, 2), "center", (1.5, 1, 2.5, 3)],
        [(3, 3, 1, 2), "radius", (2, 1, 4, 5)],
        [(3, 3, 1, 2), "corner", (3, 3, 4, 5)],
        # 'corners' mode finds the top-left corner
        [(1, 2, 5, 4), "corners", (1, 2, 5, 4)],
        [(5, 4, 1, 2), "corners", (1, 2, 5, 4)],
        [(1, 4, 5, 2), "corners", (1, 2, 5, 4)],
        [(5, 2, 1, 4), "corners", (1, 2, 5, 4)],
    ],
)
def test_ellipse_mode_success(
    vsk: vsketch.Vsketch,
    data: Tuple[float, float, float, float],
    mode: str,
    expected: Tuple[float, float, float, float],
) -> None:
    vsk.detail(0.01)
    vsk.ellipse(*data, mode=mode)
    assert line_count_equal(vsk, 1)
    assert bounds_equal(vsk, *expected)


def test_ellipse_bad_args(vsk: vsketch.Vsketch) -> None:
    with pytest.raises(TypeError):
        vsk.ellipse(0.5, 3, mode="radius")  # type: ignore
    with pytest.raises(TypeError):
        vsk.ellipse("hey", 2, 0.5, 4)  # type: ignore
    with pytest.raises(ValueError):
        vsk.ellipse(2, 2, 1, 3, mode="jumbo")
