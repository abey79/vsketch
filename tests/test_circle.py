import pytest

from .utils import bounds_equal, line_count_equal


def test_circle_radius(vsk):
    vsk.circle(0, 0, radius=5)
    assert line_count_equal(vsk, 1)
    assert bounds_equal(vsk, -5, -5, 5, 5)


def test_circle_diameter(vsk):
    vsk.detail(0.01)  # make sure we have a tight bound match
    vsk.circle(0, 0, diameter=5)
    assert line_count_equal(vsk, 1)
    assert bounds_equal(vsk, -2.5, -2.5, 2.5, 2.5)


def test_circle_default(vsk):
    # default should be diameter
    vsk.detail(0.01)  # make sure we have a tight bound match
    vsk.circle(0, 0, 5)
    assert line_count_equal(vsk, 1)
    assert bounds_equal(vsk, -2.5, -2.5, 2.5, 2.5)


def test_circle_bad_args(vsk):
    with pytest.raises(ValueError):
        vsk.circle(0, 0)
    with pytest.raises(ValueError):
        vsk.circle(0, 0, radius=10, diameter=20)
