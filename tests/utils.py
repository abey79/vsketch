from typing import Iterable, Optional, Tuple, Union

import numpy as np

import vsketch


def bounds_equal(
    vsk: vsketch.Vsketch, xmin: float, ymin: float, xmax: float, ymax: float
) -> bool:
    """Asserts that sketch bounds are approximately equal to those provided"""

    bounds = vsk.document.bounds()
    return bool(
        bounds is not None
        and np.isclose(bounds[0], xmin, rtol=1e-03)
        and np.isclose(bounds[1], ymin, rtol=1e-03)
        and np.isclose(bounds[2], xmax, rtol=1e-03)
        and np.isclose(bounds[3], ymax, rtol=1e-03)
    )


def length_equal(vsk: vsketch.Vsketch, length: float) -> bool:
    """Asserts that sketch length is approximately equal to those provided"""

    length_ = vsk.document.length()
    return bool(length is not None and np.isclose(length_, length, rtol=1e-03))


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

    target_layer_counts = {}
    for i, p in enumerate(args):

        if isinstance(p, int):
            target_layer_counts[i + 1] = p
        else:
            target_layer_counts[p[0]] = p[1]

    actual_layer_counts = {}
    for layer_id, layer in vsk.document.layers.items():
        actual_layer_counts[layer_id] = len(layer)

    # this is needed when some layer are explicitly specified to 0
    for k in target_layer_counts:
        if k not in actual_layer_counts:
            actual_layer_counts[k] = 0

    return target_layer_counts == actual_layer_counts


def line_exists(
    vsk: vsketch.Vsketch,
    line: np.ndarray,
    layer_ids: Optional[Union[int, Iterable[int]]] = None,
    strict: Optional[bool] = True,
) -> bool:
    """Asserts that a given line exists in the vsketch

    Args:
        vsk: the vsketch
        line (Nx1 ndarray of complex): the line to look for
        layer_ids: the layer IDs to consider (can be a int, an iterable of int or None for all
            layers, which is the default)
        strict: if True, checks for hard equality. Otherwise checks for equality with equivalent
            lines (reversed, or closed at different points)
    """

    if isinstance(layer_ids, int):
        layer_ids = [layer_ids]
    elif layer_ids is None:
        layer_ids = list(vsk.document.layers.keys())

    for layer_id in layer_ids:
        if layer_id in vsk.document.layers:
            for line_ in vsk.document.layers[layer_id]:
                if len(line_) == len(line):
                    if strict:
                        if np.all(line_ == line):
                            return True
                    else:
                        # closed lines case
                        if line[0] == line[-1] and line_[0] == line[-1]:
                            tmp_line = line[:-1]
                            tmp_line_ = line_[:-1]
                            for i in range(len(tmp_line)):
                                rolled_line = np.roll(tmp_line, i)
                                if np.all(rolled_line == tmp_line_) or np.all(
                                    rolled_line == tmp_line_[::-1]
                                ):
                                    return True
                        # open lines case
                        else:
                            if np.all(line == line_) or np.all(line == line_[::-1]):
                                return True
    return False
