import numpy as np

import vsketch
from vsketch import Vsketch


class EasingSketch(vsketch.SketchClass):
    mode = vsketch.Param("linear", choices=vsketch.EASING_FUNCTIONS.keys())
    low_deadzone = vsketch.Param(0.0, 0.0, 100.0, step=5)
    high_deadzone = vsketch.Param(0.0, 0.0, 100.0, step=5)
    param = vsketch.Param(10.0, step=1.0, decimals=1)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("20x20cm", landscape=False, center=False)
        vsk.scale("cm")

        vsk.translate(2.5, 2.5)
        vsk.scale(15)
        input_coord = np.linspace(0.0, 1.0, num=1000)
        output_coord = Vsketch.easing(
            input_coord,
            mode=self.mode,
            low_dead=self.low_deadzone / 100.0,
            high_dead=self.high_deadzone / 100.0,
            param=self.param,
        )
        vsk.stroke(2)
        vsk.polygon(input_coord, 1.0 - output_coord)
        vsk.point(0.0, 1.0)
        vsk.point(1.0, 0.0)
        if self.low_deadzone > 0.0:
            vsk.point(self.low_deadzone / 100.0, 1.0)
        if self.high_deadzone > 0.0:
            vsk.point(1.0 - self.high_deadzone / 100.0, 0.0)
        vsk.vpype("penwidth --layer 2 .6mm")

        # Draw axes
        vsk.stroke(3)
        vsk.polygon([0, 0, 1, 1], [1.05, 1.07, 1.07, 1.05])
        vsk.polygon([-0.05, -0.07, -0.07, -0.05], [0, 0, 1, 1])
        vsk.vpype("color --layer 3 black")

        # Draw grid
        vsk.stroke(1)
        for coord in np.linspace(0, 1, num=11):
            vsk.line(coord, 0, coord, 1)
            vsk.line(0, coord, 1, coord)
        vsk.vpype("color --layer 1 #eee")

        # Draw text
        vsk.stroke(3)
        vsk.textMode("label")
        vsk.text("0", 0, 1.1, align="center")
        vsk.text("1", 1, 1.1, align="center")
        vsk.text("input", 0.5, 1.1, align="center")
        vsk.text("0", -0.1, 1, align="center")
        vsk.text("1", -0.1, 0, align="center")

        # vsk.text() doesn't support vertical text in label mode
        with vsk.pushMatrix():
            vsk.translate(-0.1, 0.5)
            vsk.rotate(-90, degrees=True)
            vsk.text("output", align="center", mode="transform", size=0.03)

        vsk.stroke(5)
        vsk.text(self.mode, 0.5, -0.07, align="center", size="30pt")
        vsk.vpype(f"color -l5 black")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    EasingSketch.display()
