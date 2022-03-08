import vsketch


class SubSketchSketch(vsketch.SketchClass):
    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=True)
        vsk.scale("cm")

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
            with vsk.pushMatrix():
                vsk.scale(0.95**i)
                vsk.rotate(8 * i, degrees=True)
                vsk.sketch(sub)

            vsk.translate(3, 0)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    SubSketchSketch.display()
