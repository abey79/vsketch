import numpy as np

from .utils import bounds_equal, length_equal, line_count_equal, line_exists


def test_line(vsk):
    vsk.line(5, 5, 10, 5)
    assert line_count_equal(vsk, 1)
    assert line_exists(vsk, np.array([5 + 5j, 10 + 5j]))
    assert length_equal(vsk, 5)
    assert bounds_equal(vsk, 5, 5, 10, 5)
