from typing import Iterable, Optional, Tuple, Union, cast

import numpy as np
import vsketch


def bounds_equal(
    vsk: vsketch.Vsketch, xmin: float, ymin: float, xmax: float, ymax: float
) -> bool:
    """Asserts that sketch bounds are approximately equal to those provided"""

    bounds = vsk.vector_data.bounds()
    return (
        bounds is not None
        and np.isclose(bounds[0], xmin, rtol=1e-03)
        and np.isclose(bounds[1], ymin, rtol=1e-03)
        and np.isclose(bounds[2], xmax, rtol=1e-03)
        and np.isclose(bounds[3], ymax, rtol=1e-03)
    )


def line_count_equal(vsk: vsketch.Vsketch, *args: Union[int, Tuple[int, int]]) -> bool:
    """Asserts that layers have the given number of path. Any number of path count can be
    passed as argument, either as single int (layer ID is then inferred or as (layer_ID, n)
    tuple.

    Examples:

        >>> assert line_count_equal(vsk, 10, 23)  # 10 lines in layer 1, 23 in layer 2
        >>> assert line_count_equal(vsk, 10, (4, 22))  # 10 lines in layer 1, 22 in layer 4

    Args:
        vsk: the sketch to test
        args (int or Tuple[int, int]): line number for each layer
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

    return target_layer_counts == actual_layer_counts


def line_exists(
    vsk: vsketch.Vsketch,
    line: np.ndarray,
    layer_ids: Optional[Union[int, Iterable[int]]] = None,
) -> bool:
    """Asserts that a given line exists in the vsketch

    Args:
        vsk: the vsketch
        line (Nx1 ndarray of complex): the line to look for
        layer_ids: the layer IDs to consider (can be a int, an iterable of int or None for all
            layers, which is the default)
    """

    if isinstance(layer_ids, int):
        layer_ids = [layer_ids]
    elif layer_ids is None:
        layer_ids = list(vsk.vector_data.layers.keys())

    for layer_id in layer_ids:
        if layer_id in vsk.vector_data.layers:
            for line_ in vsk.vector_data.layers[layer_id]:
                if np.all(line_ == line):
                    return True
    return False
