import pytest

from .utils import assert_bounds, assert_line_count


def test_line(vsk):
    vsk.line(5, 5, 10, 5)
    assert_line_count(vsk, 1)
    assert_bounds(vsk, 5, 5, 10, 5)


def test_circle_radius(vsk):
    vsk.circle(0, 0, radius=5)
    assert_line_count(vsk, 1)
    assert_bounds(vsk, -5, -5, 5, 5)


def test_circle_diameter(vsk):
    vsk.circle(0, 0, diameter=5)
    assert_line_count(vsk, 1)
    assert_bounds(vsk, -2.5, -2.5, 2.5, 2.5)


def test_circle_default(vsk):
    # default should be diameter
    vsk.circle(0, 0, 5)
    assert_line_count(vsk, 1)
    assert_bounds(vsk, -2.5, -2.5, 2.5, 2.5)


def test_circle_bad_args(vsk):
    with pytest.raises(ValueError):
        vsk.circle(0, 0)
    with pytest.raises(ValueError):
        vsk.circle(0, 0, radius=10, diameter=20)
