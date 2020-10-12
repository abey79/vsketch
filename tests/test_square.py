from typing import Sequence, Tuple

import numpy as np
import pytest

import vsketch

from .utils import line_count_equal, line_exists


def test_square_default_success(vsk: vsketch.Vsketch) -> None:
    vsk.square(2, 2, 2.5)
    assert line_count_equal(vsk, 1)
    assert line_exists(
        vsk, np.array([2 + 2j, 4.5 + 2j, 4.5 + 4.5j, 2 + 4.5j, 2 + 2j]), strict=False
    )


# noinspection DuplicatedCode
@pytest.mark.parametrize(
    ["data", "mode", "expected"],
    [
        [(2, 2, 2.5), "corner", (2 + 2j, 4.5 + 2j, 4.5 + 4.5j, 2 + 4.5j, 2 + 2j)],
        # 'corners' == 'corner' for square()
        [(1, 2, 5), "corners", (1 + 2j, 6 + 2j, 6 + 7j, 1 + 7j, 1 + 2j)],
        [(3, 3, 2), "center", (2 + 2j, 4 + 2j, 4 + 4j, 2 + 4j, 2 + 2j)],
        [(1.5, 3, 1), "radius", (0.5 + 2j, 2.5 + 2j, 2.5 + 4j, 0.5 + 4j, 0.5 + 2j)],
    ],
)
def test_square_mode_success(
    vsk: vsketch.Vsketch,
    data: Tuple[float, float, float],
    mode: str,
    expected: Sequence[float],
) -> None:
    vsk.square(*data, mode=mode)  # type: ignore
    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, np.array(expected, dtype=complex), strict=False)


def test_square_arg(vsk: vsketch.Vsketch) -> None:
    # vsk.square() expects exactly 6 args
    with pytest.raises(TypeError):
        # noinspection PyArgumentList
        vsk.square(0.5, 2)  # type: ignore

    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        vsk.square("hey", 3, 5)  # type: ignore

    with pytest.raises(ValueError):
        vsk.square(2, 2, 2.5, mode="jumbo")
