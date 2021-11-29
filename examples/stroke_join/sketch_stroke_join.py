from shapely.affinity import translate
from shapely.geometry import Polygon

import vsketch


class StrokeJoinSketch(vsketch.SketchClass):
    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=False)
        vsk.scale("cm")

        p = translate(
            Polygon(
                [(-3, -1), (1.5, -2), (1.4, 2), (0, 1.5), (-1, 2.3)],
                holes=[[(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)]],
            ),
            2.5,
            14,
        )

        # round join style (default)
        vsk.strokeWeight(10)
        vsk.square(0, 0, 4)
        vsk.triangle(0, 6, 2, 10, 4, 7)
        vsk.geometry(p)

        vsk.translate(7, 0)

        # bevel join style
        vsk.strokeJoin("bevel")
        vsk.square(0, 0, 4)
        vsk.triangle(0, 6, 2, 10, 4, 7)
        vsk.geometry(p)

        vsk.translate(7, 0)

        # mitre join style
        vsk.strokeJoin("mitre")
        vsk.square(0, 0, 4)
        vsk.triangle(0, 6, 2, 10, 4, 7)
        vsk.geometry(p)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    StrokeJoinSketch.display()
