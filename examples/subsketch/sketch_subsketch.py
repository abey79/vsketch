import vsketch


class SubSketchSketch(vsketch.Vsketch):
    def draw(self) -> None:
        self.size("a4", landscape=True)
        self.scale("cm")

        # create a stick figure
        sub = vsketch.Vsketch()
        sub.detail(0.01)
        sub.rect(0, 0, 1, 2)
        sub.circle(0.5, -0.5, 1)
        sub.line(0, 0, -0.5, 1)
        sub.line(1, 0, 1.5, 1)
        sub.line(0, 2, -0.3, 4)
        sub.line(1, 2, 1.3, 4)

        for i in range(8):
            with self.pushMatrix():
                self.scale(0.95 ** i)
                self.rotate(8 * i, degrees=True)
                self.sketch(sub)

            self.translate(3, 0)

    def finalize(self) -> None:
        self.vpype("linemerge linesimplify reloop linesort")
