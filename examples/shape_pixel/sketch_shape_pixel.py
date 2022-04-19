import itertools

import vsketch


class ShapePixelSketch(vsketch.SketchClass):
    pixel_count = vsketch.Param(20, 1)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a5", landscape=False)

        shp = vsk.createShape()

        diameter = 0.8 * min(vsk.width, vsk.height)
        pixel_size = diameter / self.pixel_count
        epsilon = pixel_size / 10000  # ensure numerical errors dont get in the way of unions

        for i, j in itertools.product(range(self.pixel_count), range(self.pixel_count)):
            if vsk.random(1) < 0.2:
                x = (vsk.width - diameter) / 2 + i * pixel_size
                y = (vsk.height - diameter) / 2 + j * pixel_size
                shp.rect(x, y, pixel_size + epsilon, pixel_size + epsilon)

        shp.circle(vsk.width / 2, vsk.height / 2, diameter, op="intersection")

        vsk.fill(2)
        vsk.shape(shp)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    ShapePixelSketch.display()
