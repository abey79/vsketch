import numpy as np

import vsketch


class TransformsSketch(vsketch.SketchClass):
    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=True)
        vsk.scale("2cm")

        # build a star
        angles = np.linspace(0, 2 * np.pi, 5, endpoint=False)
        idx = [0, 2, 4, 1, 3, 0]
        x = np.cos(angles[idx] - np.pi / 2)
        y = np.sin(angles[idx] - np.pi / 2)

        with vsk.pushMatrix():
            for i in range(5):
                with vsk.pushMatrix():
                    vsk.scale(0.8**i)
                    vsk.polygon(x, y)

                vsk.translate(2, 0)

        vsk.translate(0, 4)

        for i in range(5):
            with vsk.pushMatrix():
                vsk.rotate(i * 4, degrees=True)
                vsk.polygon(x, y)

            vsk.translate(2, 0)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    TransformsSketch.display()
