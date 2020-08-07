from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import vsketch


class MatrixPopper:
    def __init__(self, vsk: "vsketch.Vsketch"):
        self._vsk = vsk

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._vsk.popMatrix()
