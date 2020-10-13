from typing import Iterable, Sequence

import numpy as np
import pytest

import vsketch

from .utils import line_count_equal, line_exists


@pytest.mark.parametrize(
    ["data", "expected"],
    [
        [[(0, 0), (1, 2), (3, 2)], (0, 1 + 2j, 3 + 2j)],
        [[[0, 0], [1, 2], [3, 2]], (0, 1 + 2j, 3 + 2j)],
        [np.array([(3, 2), (4, 3), (1, 2)]), (3 + 2j, 4 + 3j, 1 + 2j)],
        # pure iterable should be accepted
        [zip([3, 2, 4], [3, 5, 7]), (3 + 3j, 2 + 5j, 4 + 7j)],
        # one complex arg should be accepted
        [np.array([3 + 3j, 2 + 5j, 4 + 7j]), (3 + 3j, 2 + 5j, 4 + 7j)],
    ],
)
def test_polygon_1arg_success(
    vsk: vsketch.Vsketch, data: Iterable[Sequence[float]], expected: Sequence[complex]
) -> None:
    # polygon() with a single arg, polygon should accept an iterable of 2-size iterable
    vsk.polygon(data)
    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, np.array(expected, dtype=complex))


def test_polygon_1arg_fail(vsk: vsketch.Vsketch) -> None:
    # 1D arrays are not
    with pytest.raises(ValueError):
        vsk.polygon([1, 3, 2])


@pytest.mark.parametrize(
    ["x", "y", "expected"],
    [
        [[2, 4, 6], (1, 3, 5), (2 + 1j, 4 + 3j, 6 + 5j)],
        [range(4), range(4), (0, 1 + 1j, 2 + 2j, 3 + 3j)],
        [np.arange(4), np.arange(4), (0, 1 + 1j, 2 + 2j, 3 + 3j)],
        # extra length is ignored
        [range(4), range(10), (0, 1 + 1j, 2 + 2j, 3 + 3j)],
        [np.arange(4), np.arange(10), (0, 1 + 1j, 2 + 2j, 3 + 3j)],
    ],
)
def test_polygon_2args_success(
    vsk: vsketch.Vsketch, x: Iterable[float], y: Iterable[float], expected: Sequence[complex]
) -> None:
    vsk.polygon(x, y)
    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, np.array(expected, dtype=complex))


def test_polygon_2args_fail(vsk: vsketch.Vsketch) -> None:
    # wrong array dimensions
    with pytest.raises(ValueError):
        vsk.polygon(np.random.rand(5, 2), np.random.rand(5, 2))

    # wrong array content
    with pytest.raises(ValueError):
        vsk.polygon(["red", "blue"], [1, 2])  # type: ignore


def test_polygon_close(vsk: vsketch.Vsketch) -> None:
    vsk.polygon([(0, 0), (1, 0), (3, 3)], close=True)
    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, np.array([0, 1, 3 + 3j, 0]))
