import numpy as np
import pytest

import vsketch

from .utils import line_count_equal, line_exists


def test_quad_success(vsk: vsketch.Vsketch) -> None:
    vsk.quad(0, 0, 1, 3.5, 4.5, 4.5, 3.5, 1)
    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, np.array([0 + 0j, 1 + 3.5j, 4.5 + 4.5j, 3.5 + 1j, 0 + 0j]))


def test_quad_arg(vsk: vsketch.Vsketch) -> None:
    # vsk.quad() expects exactly 8 args
    with pytest.raises(TypeError):
        # noinspection PyArgumentList
        vsk.quad(0.5, 2, 3, 3)  # type: ignore

    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        vsk.quad("hey", 3, 5, 2.5, 2.5, 6, 3, 2)  # type: ignore
