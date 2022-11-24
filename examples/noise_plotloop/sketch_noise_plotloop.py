import math

import numpy as np

import vsketch


class NoisePlotloopSketch(vsketch.SketchClass):
    frame_count = vsketch.Param(50)
    frame = vsketch.Param(0)

    noise_radius = vsketch.Param(5)
    noise_span = vsketch.Param(90)
    point_count = vsketch.Param(200)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("5x5cm", center=False)
        vsk.scale("cm")

        # cylindrical sampling of noise
        noise_angle_start = np.pi / self.frame_count * self.frame
        noise_angle_end = noise_angle_start + math.radians(self.noise_span)
        noise_angles = np.linspace(noise_angle_start, noise_angle_end, self.point_count)
        noise_x = self.noise_radius * np.cos(noise_angles)
        noise_y = self.noise_radius * np.sin(noise_angles)
        noise_value = vsk.noise(noise_x, noise_y, grid_mode=False)

        # draw line
        vsk.polygon(np.linspace(0.5, 4.5, self.point_count), 2.5 * noise_value * 2)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    NoisePlotloopSketch.display()
