import numpy as np
import pytest


@pytest.mark.parametrize(
    ["params", "expected"],
    [
        [("15in", "10in"), (1440.0, 960.0)],
        [("15inx10in", None), (1440.0, 960.0)],
        [("15in", 960), (1440.0, 960.0)],
        [("a4", None), (21 / 2.54 * 96, 29.7 / 2.54 * 96)],
    ],
)
def test_size(vsk, params, expected):
    if params[1] is None:
        vsk.size(params[0])
    else:
        vsk.size(*params)

    assert np.isclose(vsk.width, expected[0]) and np.isclose(vsk.height, expected[1])
