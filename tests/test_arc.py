from typing import Sequence, Tuple

import numpy as np
import pytest

import vsketch

from .utils import bounds_equal, line_count_equal


def test_arc_default_success(vsk: vsketch.Vsketch) -> None:
    vsk.detail(0.01)
    vsk.arc(2, 2, 1, 3, 0, np.pi)
    assert line_count_equal(vsk, 1)
    assert bounds_equal(vsk, 1.5, 0.5, 2.5, 2)


@pytest.mark.parametrize(
    ["data", "mode", "expected"],
    [
        [(5, 5, 2, 1, np.pi / 2, np.pi), "center", (4, 4.5, 5, 5)],
        [(5, 5, 2, 1, np.pi / 2, 1.5 * np.pi), "radius", (3, 4, 5, 6)],
        [(3, 3, 2, 1, 0, np.pi), "corner", (3, 3, 5, 3.5)],
        [(2, 2, 5, 6, 0, np.pi), "corners", (2, 2, 5, 4)],
    ],
)
def test_arc_mode_success(
    vsk: vsketch.Vsketch, data: Sequence[float], mode: str, expected: Sequence[float]
) -> None:
    vsk.detail(0.01)
    vsk.arc(*data, mode=mode)  # type: ignore
    assert line_count_equal(vsk, 1)
    assert bounds_equal(vsk, *expected)


@pytest.mark.parametrize(
    ["data", "close", "expected"],
    [
        [(5, 5, 2, 1, np.pi / 2, np.pi), "no", (4, 4.5, 5, 5)],
        [(5, 5, 2, 1, np.pi / 2, np.pi), "chord", (4, 4.5, 5, 5)],
        [(5, 5, 2, 1, np.pi / 2, np.pi), "pie", (4, 4.5, 5, 5)],
    ],
)
def test_arc_close_success(
    vsk: vsketch.Vsketch, data: Sequence[float], close: str, expected: Sequence[float]
) -> None:
    vsk.detail(0.01)
    vsk.arc(*data, close=close)  # type: ignore
    assert line_count_equal(vsk, 1)
    assert bounds_equal(vsk, *expected)


@pytest.mark.parametrize(
    ["data", "mode", "close", "expected"],
    [
        [(3, 3, 2, 1, 0, np.pi), "corner", "chord", (3, 3, 5, 3.5)],
        [(3, 3, 2, 1, 0, np.pi), "corner", "pie", (3, 3, 5, 3.5)],
        [(2, 2, 5, 6, 0, np.pi), "corners", "chord", (2, 2, 5, 4)],
        [(2, 2, 5, 6, 0, np.pi), "corners", "pie", (2, 2, 5, 4)],
    ],
)
def test_arc_mode_close_success(
    vsk: vsketch.Vsketch,
    data: Sequence[float],
    mode: str,
    close: str,
    expected: Sequence[float],
) -> None:
    vsk.detail(0.01)
    vsk.arc(*data, mode=mode, close=close)  # type: ignore
    assert line_count_equal(vsk, 1)
    assert bounds_equal(vsk, *expected)


def test_arc_bad_args(vsk: vsketch.Vsketch) -> None:
    with pytest.raises(TypeError):
        vsk.arc(2, 3, mode="radius")  # type: ignore
    with pytest.raises(ValueError):
        vsk.arc(2, 3, 1, 1, 0, 120, close="yes")
    with pytest.raises(ValueError):
        vsk.arc(2, 3, 1, 1, 0, -30, mode="jumbo")
    with pytest.raises(ValueError):
        vsk.arc(2, 3, 1, 1, 30, 30)
