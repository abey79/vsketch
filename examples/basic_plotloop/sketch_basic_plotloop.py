import math

import vsketch


class BasicPlotloopSketch(vsketch.SketchClass):
    frame_count = vsketch.Param(50)
    frame = vsketch.Param(0)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("5x5cm", center=False)
        vsk.scale("cm")

        radius = 2
        vsk.circle(2.5, 2.5, radius=radius)
        angle = 360 / self.frame_count * self.frame
        vsk.circle(
            2.5 + radius * math.cos(math.radians(angle)),
            2.5 + radius * math.sin(math.radians(angle)),
            radius=0.1,
        )

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    BasicPlotloopSketch.display()
