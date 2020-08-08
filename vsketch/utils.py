from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import vsketch


class MatrixPopper:
    def __init__(self, vsk: "vsketch.Vsketch"):
        self._vsk = vsk

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._vsk.popMatrix()


def complex_to_2d(line: np.ndarray) -> np.ndarray:
    return np.vstack([line.real, line.imag]).T
