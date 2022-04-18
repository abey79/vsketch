"""Text layout examples.

The primary use of this sketch is to show the difference between the "transform"
text mode and the "label" text mode, and to be a testcase for both.
"""

import vsketch


class TextLayoutSketch(vsketch.SketchClass):
    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=True)
        vsk.scale("cm")

        for i in range(4):
            with vsk.pushMatrix():
                vsk.translate(8 * i, 0)

                # Rotation and skewing
                vsk.rotate(30 * i, degrees=True)
                vsk.scale(1.2**i, 0.8**i)

                vsk.point(0, 0)
                vsk.text("transform", 0, 0, size=1.0, mode="transform", align="left")

                vsk.point(0, 2)
                vsk.text("label", 0, 2, mode="label", align="left")

        with vsk.pushMatrix():
            vsk.translate(10, 8)
            # Horizontal Flip
            vsk.scale(-1, 1)

            vsk.text(" transform", 0, -0.5, size=1.0, mode="transform", font="timesr")
            vsk.text(" maybe backwards", 0, 0.5, size=1.0, mode="transform", font="timesr")

            vsk.text(" label", 0, -0.5, mode="label", font="timesr")
            vsk.text(" never backwards", 0, 0.5, mode="label", font="timesr")

        with vsk.pushMatrix():
            vsk.translate(0, 11)

            vsk.text(__doc__, width=14, size=0.9, font="cursive")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        pass


if __name__ == "__main__":
    TextLayoutSketch.display()
