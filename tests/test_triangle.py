import numpy as np
import pytest

import vsketch

from .utils import line_count_equal, line_exists


def test_triangle_success(vsk: vsketch.Vsketch) -> None:
    vsk.triangle(2, 2, 2, 3, 3, 2.5)
    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, np.array([2 + 2j, 2 + 3j, 3 + 2.5j, 2 + 2j]))


def test_triangle_arg(vsk: vsketch.Vsketch) -> None:
    # vsk.triangle() expects exactly 6 args
    with pytest.raises(TypeError):
        # noinspection PyArgumentList
        vsk.triangle(2, 2, 2, 4, 3)  # type: ignore

    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        vsk.triangle("hey", 3, 3, 5, 5, 4)  # type: ignore
