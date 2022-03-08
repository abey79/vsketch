import vsketch


class PointTransformSketch(vsketch.SketchClass):
    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=False)
        vsk.scale("1mm")

        with vsk.pushMatrix():
            for _ in range(40):
                vsk.rotate(2, degrees=True)
                vsk.scale(0.95)
                vsk.point(-75, 75)
                vsk.point(0, 75)
                vsk.point(75, 75)
                vsk.point(75, 0)
                vsk.point(75, -75)
                vsk.point(0, -75)
                vsk.point(-75, -75)
                vsk.point(-75, 0)

        with vsk.pushMatrix():
            vsk.rotate(80, degrees=True)
            vsk.scale(0.95**40)
            vsk.square(0, 0, 150, mode="center")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    PointTransformSketch.display()
