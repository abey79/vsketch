import numpy as np
from shapely.affinity import translate
from shapely.geometry import Point
from shapely.ops import unary_union

import vsketch


class ShapelySketch(vsketch.SketchClass):
    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=False)
        vsk.scale("4mm")

        for i in range(5):
            for j in range(7):
                shape = unary_union(
                    [
                        Point(*np.random.random(2) * 5).buffer(np.random.random())
                        for _ in range(15)
                    ]
                )
                vsk.geometry(translate(shape, i * 8, j * 8))

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    ShapelySketch.display()
