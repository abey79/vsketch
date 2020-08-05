from .utils import bounds_equal, line_count_equal


def test_line(vsk):
    vsk.line(5, 5, 10, 5)
    assert line_count_equal(vsk, 1)
    assert bounds_equal(vsk, 5, 5, 10, 5)
