import numpy as np

import vsketch


class TransformsSketch(vsketch.Vsketch):
    def draw(self) -> None:
        self.size("a4", landscape=True)
        self.scale("2cm")

        # build a star
        angles = np.linspace(0, 2 * np.pi, 5, endpoint=False)
        idx = [0, 2, 4, 1, 3, 0]
        x = np.cos(angles[idx] - np.pi / 2)
        y = np.sin(angles[idx] - np.pi / 2)

        with self.pushMatrix():
            for i in range(5):
                with self.pushMatrix():
                    self.scale(0.8 ** i)
                    self.polygon(x, y)

                self.translate(2, 0)

        self.translate(0, 4)

        for i in range(5):
            with self.pushMatrix():
                self.rotate(i * 4, degrees=True)
                self.polygon(x, y)

            self.translate(2, 0)

    def finalize(self) -> None:
        self.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    vsk = TransformsSketch()
    vsk.draw()
    vsk.finalize()
    vsk.display()
