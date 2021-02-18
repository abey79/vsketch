import math

import numpy as np

import vsketch


class RandomFlowerSketch(vsketch.Vsketch):
    num_line = vsketch.Param(200, 1)
    point_per_line = vsketch.Param(100, 1)
    rdir_range = vsketch.Param(math.pi / 6)

    def draw(self) -> None:
        self.size("a4", landscape=True)
        self.scale("cm")

        self.rotate(-90, degrees=True)

        noise_coord = np.linspace(0, 1, self.point_per_line)
        dirs = np.linspace(0, 2 * math.pi, self.num_line)
        perlin = self.noise(noise_coord, dirs, [0, 100])

        for i, direction in enumerate(dirs):
            rdir = self.map(
                perlin[:, i, 0], 0, 1, direction - self.rdir_range, direction + self.rdir_range
            )
            roffset = self.map(perlin[:, i, 1], 0, 1, 0.05, 0.12)

            xoffset = roffset * np.cos(rdir)
            yoffset = roffset * np.sin(rdir)

            self.polygon(np.cumsum(xoffset), np.cumsum(yoffset))

    def finalize(self) -> None:
        self.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    vsk = RandomFlowerSketch()
    vsk.draw()
    vsk.finalize()
    vsk.display()
