from typing import Tuple

import numpy as np
import pytest

import vsketch

from .utils import bounds_equal, length_equal, line_count_equal


def test_circle_default(vsk: vsketch.Vsketch) -> None:
    # default should be diameter
    vsk.detail(0.01)  # make sure we have a tight bound match
    vsk.circle(0, 0, 5)
    assert line_count_equal(vsk, 1)
    assert length_equal(vsk, 5 * np.pi)
    assert bounds_equal(vsk, -2.5, -2.5, 2.5, 2.5)


def test_circle_radius(vsk: vsketch.Vsketch) -> None:
    vsk.circle(0, 0, radius=5)
    assert line_count_equal(vsk, 1)
    assert length_equal(vsk, 5 * 2 * np.pi)
    assert bounds_equal(vsk, -5, -5, 5, 5)


def test_circle_diameter(vsk: vsketch.Vsketch) -> None:
    vsk.detail(0.01)  # make sure we have a tight bound match
    vsk.circle(0, 0, diameter=5)
    assert line_count_equal(vsk, 1)
    assert length_equal(vsk, 5 * np.pi)
    assert bounds_equal(vsk, -2.5, -2.5, 2.5, 2.5)


@pytest.mark.parametrize(
    ["data", "mode", "expected"],
    [
        [(0, 0, 5), "center", (-2.5, -2.5, 2.5, 2.5)],
        [(3, 3, 1), "radius", (2, 2, 4, 4)],
        [(3, 3, 1), "corner", (3, 3, 4, 4)],
        # 'corners' == 'corner' for circle()
        [(3, 3, 1), "corners", (3, 3, 4, 4)],
    ],
)
def test_circle_mode(
    vsk: vsketch.Vsketch,
    data: Tuple[float, float, float],
    mode: str,
    expected: Tuple[float, float, float, float],
) -> None:
    vsk.detail(0.01)
    vsk.circle(*data, mode=mode)
    assert line_count_equal(vsk, 1)
    assert bounds_equal(vsk, *expected)


def test_circle_bad_args(vsk: vsketch.Vsketch) -> None:
    with pytest.raises(ValueError):
        vsk.circle(0, 0)  # type: ignore
    with pytest.raises(ValueError):
        vsk.circle(0, 0, radius=10, diameter=20)
    with pytest.raises(ValueError):
        vsk.circle(2, 2, 5, mode="jumbo")
