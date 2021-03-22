from shapely.affinity import translate
from shapely.geometry import Polygon

import vsketch


class StrokeFillSketch(vsketch.SketchClass):
    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=True)
        vsk.scale("1cm")
        vsk.penWidth("0.5mm")

        p = translate(
            Polygon(
                [(-3, -1), (1.5, -2), (1.4, 2), (0, 1.5), (-1, 2.3)],
                holes=[[(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)]],
            ),
            2.5,
            14,
        )

        # the default is no fill and stroke to layer 1
        vsk.square(0, 0, 4)
        vsk.circle(2, 8, 4)
        vsk.geometry(p)

        vsk.translate(7, 0)

        # add some fill to layer 2
        vsk.fill(2)
        vsk.penWidth("1mm", 2)
        vsk.square(0, 0, 4)
        vsk.circle(2, 8, 4)
        vsk.geometry(p)

        vsk.translate(7, 0)

        # with thick stroke
        vsk.fill(2)
        vsk.penWidth("1mm", 2)
        vsk.strokeWeight(4)
        vsk.square(0, 0, 4)
        vsk.circle(2, 8, 4)
        vsk.geometry(p)

        vsk.translate(7, 0)

        # remove stroke and set fill to layer 3 with a thicker pen
        vsk.fill(3)
        vsk.penWidth("2mm", 3)
        vsk.noStroke()
        vsk.square(0, 0, 4)
        vsk.circle(2, 8, 4)
        vsk.geometry(p)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    StrokeFillSketch.display()
