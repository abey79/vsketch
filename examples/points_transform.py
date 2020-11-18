from vsketch import Vsketch

vsk = Vsketch()
vsk.size("a4")
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
    vsk.scale(0.95 ** 40)
    vsk.square(0, 0, 150, mode="center")

vsk.display(mode="matplotlib")
