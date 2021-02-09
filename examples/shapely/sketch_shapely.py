import numpy as np
from shapely.affinity import translate
from shapely.geometry import Point
from shapely.ops import unary_union

import vsketch


class ShapelySketch(vsketch.Vsketch):
    def draw(self) -> None:
        self.size("a4", landscape=False)
        self.scale("4mm")

        for i in range(5):
            for j in range(7):
                shape = unary_union(
                    [
                        Point(*np.random.random(2) * 5).buffer(np.random.random())
                        for _ in range(15)
                    ]
                )
                self.geometry(translate(shape, i * 8, j * 8))

    def finalize(self) -> None:
        self.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    vsk = ShapelySketch()
    vsk.draw()
    vsk.finalize()
    vsk.display()
