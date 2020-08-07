from typing import List, Tuple, Union

import matplotlib
import matplotlib.pyplot as plt
import vpype as vp

COLORS = [
    (0, 0, 1),
    (0, 0.5, 0),
    (1, 0, 0),
    (0, 0.75, 0.75),
    (0, 1, 0),
    (0.75, 0, 0.75),
    (0.75, 0.75, 0),
    (0, 0, 0),
]


# noinspection PyUnresolvedReferences
def plot_vector_data(
    vector_data: Union[vp.LineCollection, vp.VectorData],
    show_axes: bool = True,
    show_grid: bool = False,
    show_pen_up: bool = False,
    colorful: bool = False,
    unit: str = "px",
):
    if isinstance(vector_data, vp.LineCollection):
        vector_data = vp.VectorData(vector_data)

    scale = 1 / vp.convert(unit)

    plt.cla()

    color_idx = 0
    collections = {}
    for layer_id, lc in vector_data.layers.items():
        if colorful:
            color: Union[
                Tuple[float, float, float], List[Tuple[float, float, float]]
            ] = COLORS[color_idx:] + COLORS[:color_idx]
            color_idx += len(lc)
        else:
            color = COLORS[color_idx]
            color_idx += 1
        if color_idx >= len(COLORS):
            color_idx = color_idx % len(COLORS)

        layer_lines = matplotlib.collections.LineCollection(
            (vp.as_vector(line) * scale for line in lc),
            color=color,
            lw=1,
            alpha=0.5,
            label=str(layer_id),
        )
        collections[layer_id] = [layer_lines]
        plt.gca().add_collection(layer_lines)

        if show_pen_up:
            pen_up_lines = matplotlib.collections.LineCollection(
                (
                    (vp.as_vector(lc[i])[-1] * scale, vp.as_vector(lc[i + 1])[0] * scale,)
                    for i in range(len(lc) - 1)
                ),
                color=(0, 0, 0),
                lw=0.5,
                alpha=0.5,
            )
            collections[layer_id].append(pen_up_lines)
            plt.gca().add_collection(pen_up_lines)

    plt.gca().invert_yaxis()
    plt.axis("equal")
    plt.margins(0, 0)

    if show_axes or show_grid:
        plt.axis("on")
        plt.xlabel(f"[{unit}]")
        plt.ylabel(f"[{unit}]")
    else:
        plt.axis("off")
    if show_grid:
        plt.grid("on")
    plt.show()

    return vector_data
