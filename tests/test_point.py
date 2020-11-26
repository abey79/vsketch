import pytest

from .utils import bounds_equal, line_count_equal


def test_point_success(vsk):
    vsk.detail(0.001)
    vsk.point(2, 3.5)
    offset = vsk.strokePenWidth / 2
    assert line_count_equal(vsk, 1)
    assert bounds_equal(vsk, 2 - offset, 3.5 - offset, 2 + offset, 3.5 + offset)


def test_point_transform_success(vsk):
    vsk.detail(0.001)
    vsk.scale(3, 2)
    vsk.translate(5, 3)
    vsk.point(2, 4)
    offset = vsk.strokePenWidth / 2
    assert line_count_equal(vsk, 1)
    assert bounds_equal(vsk, 21 - offset, 14 - offset, 21 + offset, 14 + offset)


def test_point_bad_args(vsk):
    with pytest.raises(TypeError):
        vsk.point(0)
    with pytest.raises(TypeError):
        vsk.point("hey", 2)
