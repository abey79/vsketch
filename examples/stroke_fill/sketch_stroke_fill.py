from shapely.affinity import translate
from shapely.geometry import Polygon

import vsketch


class StrokeFillSketch(vsketch.Vsketch):
    def draw(self) -> None:
        self.size("a4", landscape=True)
        self.scale("1cm")
        self.penWidth("0.5mm")

        p = translate(
            Polygon(
                [(-3, -1), (1.5, -2), (1.4, 2), (0, 1.5), (-1, 2.3)],
                holes=[[(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)]],
            ),
            2.5,
            14,
        )

        # the default is no fill and stroke to layer 1
        self.square(0, 0, 4)
        self.circle(2, 8, 4)
        self.geometry(p)

        self.translate(7, 0)

        # add some fill to layer 2
        self.fill(2)
        self.penWidth("1mm", 2)
        self.square(0, 0, 4)
        self.circle(2, 8, 4)
        self.geometry(p)

        self.translate(7, 0)

        # with thick stroke
        self.fill(2)
        self.penWidth("1mm", 2)
        self.strokeWeight(4)
        self.square(0, 0, 4)
        self.circle(2, 8, 4)
        self.geometry(p)

        self.translate(7, 0)

        # remove stroke and set fill to layer 3 with a thicker pen
        self.fill(3)
        self.penWidth("2mm", 3)
        self.noStroke()
        self.square(0, 0, 4)
        self.circle(2, 8, 4)
        self.geometry(p)

    def finalize(self) -> None:
        self.vpype("linemerge linesimplify reloop linesort")
