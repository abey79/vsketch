import numpy as np

import vsketch


class RandomLinesSketch(vsketch.SketchClass):
    num_line = vsketch.Param(200, 1)
    y_offset = vsketch.Param(18.0)
    x_freq = vsketch.Param(0.25)
    y_freq = vsketch.Param(4)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=True)
        vsk.scale("cm")

        x_coords = np.linspace(0, 25, 1000)

        perlin = vsk.noise(
            x_coords * self.x_freq, np.arange(self.num_line) / self.num_line * self.y_freq
        )

        for i in range(self.num_line):
            y_coords = perlin[:, i] + self.y_offset / self.num_line * i
            vsk.polygon(x_coords, y_coords)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    RandomLinesSketch.display()
