from math import tau

import vsketch


class RandomSeedSketch(vsketch.SketchClass):
    rows = 12
    cols = 12
    padding = 30

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("6x6cm", landscape=False, center=False)

        cell_width = (vsk.width - 2 * self.padding) / self.cols
        cell_height = (vsk.height - 2 * self.padding) / self.rows

        aw = cell_width * 0.8
        ah = cell_height * 0.8

        vsk.text(f"random seed: {vsk.random_seed}", 2, vsk.height - 5, size="2mm")

        for x in range(self.cols):
            for y in range(self.rows):
                cx = self.padding + cell_width * x
                cy = self.padding + cell_height * y
                vsk.translate(cx, cy)

                start = vsk.random(tau)
                stop = vsk.random(tau)
                vsk.arc(0, 0, aw, ah, start, stop, mode="corner")

                vsk.resetMatrix()

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    RandomSeedSketch.display()
