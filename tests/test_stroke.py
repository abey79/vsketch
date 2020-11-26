import numpy as np
import pytest
import vpype as vp

from .utils import line_count_equal


@pytest.mark.parametrize("weight", list(range(1, 10)))
def test_stroke_path_count(vsk, weight):
    vsk.strokeWeight(weight)
    vsk.circle(0, 0, 100)

    assert line_count_equal(vsk, weight)


@pytest.mark.parametrize("weight", list(range(1, 15)))
@pytest.mark.parametrize("detail_mm", [0.001, 0.01, 0.1, 1, 10])
def test_stroke_weight_detail(vsk, weight, detail_mm):
    """We ensure that the desired detail level is respected by strokeWeight"""
    detail_px = vp.convert_length(str(detail_mm) + "mm")
    vsk.detail(detail_px)
    vsk.strokeWeight(weight)

    # large geometries to filter out polygon's edges
    # vsk.triangle(0, 0, 160, 0, 80, 160)
    vsk.square(0, 0, 160)

    assert line_count_equal(vsk, weight)

    for line in vsk.document.layers[1]:
        seg_length = np.abs(np.diff(line))
        idx = (seg_length <= detail_px) | (seg_length > 140)
        assert np.all(idx)
