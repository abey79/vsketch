import pytest

import vsketch

from .utils import bounds_equal, line_count_equal


def test_triangle_success(vsk: vsketch.Vsketch):
    vsk.triangle(2, 2, 2, 3, 3, 2.5)
    assert line_count_equal(1)
    assert line_exists(vsk, np.ndarray([2 + 2j, 2 + 3j, 3 + 2.5j, 2 + 2j]))


def test_triangle_arg(vsk: vsketch.Vsketch):
    # vsk.triangle() expects exactly 6 args
    with pytest.raises(TypeError):
        vsk.triangle(2, 2, 2, 4, 3)

    with pytest.raises(ValueError):
        vsk.triangle("hey", 3, 3, 5, 5, 4)
