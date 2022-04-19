import vsketch


class ShapeBasicSketch(vsketch.SketchClass):
    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("18x18cm")
        vsk.scale("cm")

        shp = vsk.createShape()

        shp.square(0, 0, 2, mode="radius")
        shp.circle(0, 0, 1.6, mode="radius", op="difference")

        shp.line(-1, -1, -2.5, -2.5)
        shp.line(1, 1, 2.5, 2.5)
        shp.line(1, -1, 2.5, -2.5)
        shp.line(-1, 1, -2.5, 2.5)

        shp.point(0, 0)

        shp.point(-3, -3)
        shp.point(3, 3)
        shp.point(-3, 3)
        shp.point(3, -3)

        shp.point(0, -1.8)
        shp.point(0, 1.8)
        shp.point(-1.8, 0)
        shp.point(1.8, 0)

        # draw the shape without fill (line/point masking is disabled by default)
        vsk.shape(shp)

        # draw the shape with fill (line/point masking is enabled by default)
        with vsk.pushMatrix():
            vsk.translate(8, 0)
            vsk.fill(2)
            vsk.shape(shp)

        # draw the shape with fill and line/point masking explicitly disabled
        with vsk.pushMatrix():
            vsk.translate(0, 8)
            vsk.shape(shp, mask_lines=False, mask_points=False)

        # draw the shape with fill and a thicker pen
        with vsk.pushMatrix():
            vsk.translate(8, 8)
            vsk.stroke(3)
            vsk.fill(3)
            vsk.penWidth("2mm", 3)
            vsk.shape(shp)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        pass


if __name__ == "__main__":
    ShapeBasicSketch.display()
