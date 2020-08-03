from typing import Tuple, Union, cast

import numpy as np
import vsketch


def assert_bounds(
    vsk: vsketch.Vsketch, xmin: float, ymin: float, xmax: float, ymax: float
) -> None:
    """Asserts that sketch bounds are approximately equal to those provided"""

    bounds = vsk.vector_data.bounds()
    assert bounds is not None
    assert np.isclose(bounds[0], xmin, rtol=1e-03)
    assert np.isclose(bounds[1], ymin, rtol=1e-03)
    assert np.isclose(bounds[2], xmax, rtol=1e-03)
    assert np.isclose(bounds[3], ymax, rtol=1e-03)


def assert_line_count(vsk: vsketch.Vsketch, *args: Union[int, Tuple[int, int]]) -> None:
    """Asserts that layers have the given number of path. Any number of path count can be
    passed as argument, either as single int (layer ID is then inferred or as (layer_ID, n)
    tuple.

    Examples:

        >>> assert_line_count(vsk, 10, 23)  # 10 lines in layer 1, 23 in layer 2
        >>> assert_line_count(vsk, 10, (4, 22))  # 10 lines in layer 1, 22 in layer 4
    """

    target_layer_counts = set()
    for i, p in enumerate(args):

        if isinstance(p, int):
            desc = (i + 1, p)
        else:
            desc = p
        target_layer_counts.add(desc)

    actual_layer_counts = set()
    for layer_id, layer in vsk.vector_data.layers.items():
        actual_layer_counts.add((layer_id, len(layer)))

    assert target_layer_counts == actual_layer_counts
