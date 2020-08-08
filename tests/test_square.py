import numpy as np
import pytest

import vsketch

from .utils import line_count_equal, line_exists


def test_square_success(vsk: vsketch.Vsketch):
    vsk.square(2, 2, 2.5)
    assert line_count_equal(vsk, 1)
    vd = vsk.vector_data
    assert line_exists(vsk, np.array([2 + 2j, 4.5 + 2j, 4.5 + 4.5j, 2 + 4.5j, 2 + 2j]))


def test_square_arg(vsk: vsketch.Vsketch):
    # vsk.square() expects exactly 6 args
    with pytest.raises(TypeError):
        # noinspection PyArgumentList
        vsk.square(0.5, 2)  # type: ignore

    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        vsk.square("hey", 3, 5)  # type: ignore
