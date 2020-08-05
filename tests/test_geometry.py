import numpy as np
import pytest
from shapely.geometry import (
    LinearRing,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

from tests.utils import line_count_equal, line_exists


@pytest.mark.parametrize(
    ["data", "expected"],
    [
        [LinearRing([(0, 0), (1, 0), (0, 2)]), [[0, 1, 2j, 0]]],
        [LineString([(1, 1), (0, 3), (10, 0), (4, 3)]), [[1 + 1j, 3j, 10, 4 + 3j]]],
        [
            MultiLineString([[(0, 0), (0, 1), (3, 4)], [(1, 0), (4, 3), (1, 2)]]),
            [[0, 1j, 3 + 4j], [1, 4 + 3j, 1 + 2j]],
        ],
        [Polygon([(0, 0), (3, 0), (1, 2)]), [[0, 3, 1 + 2j, 0]]],
        [
            Polygon(
                [(0, 0), (30, 0), (30, 30), (0, 30)],
                holes=[[(1, 1), (3, 3), (2, 3)], [(10, 10), (12, 10), (10, 12)]],
            ),
            [
                [0, 30, 30 + 30j, 30j, 0],
                [(1 + 1j, 3 + 3j, 2 + 3j, 1 + 1j)],
                [10 + 10j, 12 + 10j, 10 + 12j, 10 + 10j],
            ],
        ],
        [
            MultiPolygon(
                [
                    (
                        [(0, 0), (30, 0), (30, 30), (0, 30)],
                        [[(1, 1), (3, 3), (2, 3)], [(10, 10), (12, 10), (10, 12)]],
                    ),
                    ([(0, 0), (3, 0), (1, 2)], []),
                ]
            ),
            [
                [0, 30, 30 + 30j, 30j, 0],
                [1 + 1j, 3 + 3j, 2 + 3j, 1 + 1j],
                [10 + 10j, 12 + 10j, 10 + 12j, 10 + 10j],
                [0, 3, 1 + 2j, 0],
            ],
        ],
    ],
)
def test_geometry_single_path(vsk, data, expected):
    vsk.geometry(data)
    assert line_count_equal(vsk, len(expected))
    for line in expected:
        assert line_exists(vsk, np.array(line, dtype=complex))


def test_geometry_wrong_arg(vsk):
    with pytest.raises(ValueError):
        vsk.geometry(np.arange(10))

    with pytest.raises(ValueError):
        vsk.geometry(Point([10, 12]))

    with pytest.raises(ValueError):
        vsk.geometry(MultiPoint([(3, 2), (3, 4)]))
