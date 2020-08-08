import numpy as np
import pytest

from .utils import line_count_equal


@pytest.mark.parametrize("scale", [0.1, 1, 10, 10, 10000])
def test_detail_epsilon_ok(vsk, scale):
    DETAIL = 0.1
    vsk.detail(DETAIL)
    vsk.scale(scale)
    vsk.circle(0, 0, radius=1)

    assert line_count_equal(vsk, 1)

    # no segment should ever be longer than the desired detail level.
    line = vsk.vector_data.layers[1][0]
    assert np.max(np.abs(np.diff(line))) < DETAIL
