import vsketch


class DetailSketch(vsketch.SketchClass):
    detail_value = vsketch.Param(1, 1, 50, unit="mm")

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a5", landscape=True)
        vsk.scale("1.5cm")

        vsk.detail(self.detail_value)

        vsk.circle(0, 0, 1)
        vsk.circle(0, 0, 2)
        with vsk.pushMatrix():
            vsk.scale(4)
            # the scale is taken into account to compute details
            vsk.circle(0, 0, 1)

        vsk.translate(4, 0)

        for i in range(-4, 5):
            with vsk.pushMatrix():
                vsk.translate(0, i * 0.4)
                vsk.bezier(0, 0, 1, -2, 2, 2, 3, 0)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    DetailSketch.display()
