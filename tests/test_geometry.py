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

from tests.utils import bounds_equal, line_count_equal, line_exists


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
                [1 + 1j, 3 + 3j, 2 + 3j, 1 + 1j],
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
        [Point(0, 0).buffer(1).intersection(Point(10, 10).buffer(1)), []],
        [Point(2, 3.5), 1],
        [MultiPoint([(3, 2), (3, 4)]), 2],
    ],
)
def test_geometry_single_path(vsk, data, expected):
    if data.geom_type in ["Point", "MultiPoint"]:
        vsk.detail(0.001)
        vsk.geometry(data)
        offset = vsk.strokePenWidth / 2
        assert line_count_equal(vsk, expected)
        bounds = data.bounds
        assert bounds_equal(
            vsk, bounds[0] - offset, bounds[1] - offset, bounds[2] + offset, bounds[3] + offset
        )
    else:
        vsk.geometry(data)
        assert line_count_equal(vsk, len(expected))
        for line in expected:
            assert line_exists(vsk, np.array(line, dtype=complex))


def test_geometry_wrong_arg(vsk):
    with pytest.raises(ValueError):
        vsk.geometry(np.arange(10))
