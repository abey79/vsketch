import math
from numbers import Number
from typing import Sequence, Union

import numpy as np

PERLIN_YWRAPB = 4
PERLIN_YWRAP = 1 << PERLIN_YWRAPB
PERLIN_ZWRAPB = 8
PERLIN_ZWRAP = 1 << PERLIN_ZWRAPB
PERLIN_SIZE = 4095


class Noise:
    def __init__(self):
        self._perlin = np.random.random(PERLIN_SIZE + 1)
        self.octaves: int = 4
        self.amp_falloff: float = 0.5

    def seed(self, seed: int) -> None:
        rng = np.random.default_rng(seed)
        self._perlin = rng.random(PERLIN_SIZE + 1)

    # @profile
    def perlin(
        self,
        x: Union[Number, Sequence[Number]],
        y: Union[Number, Sequence[Number]],
        z: Union[Number, Sequence[Number]],
    ) -> np.ndarray:
        """Compute perlin noise for a range of values.

        Each of the x, y, and z argument may be 1D sequence of float. Perlin noise will be
        computed for each combination of each of the input argument and returns them in a
        Numpy array of shape (len(x), len(y), len(z)). If any of the input are scalar, they are
        interpreted as a length-1 array.
        """

        if isinstance(x, Number) and isinstance(y, Number) and isinstance(z, Number):
            grid = np.array([x, y, z], dtype=float)
            single = True
        else:
            grid = np.array(np.meshgrid(x, y, z, indexing="ij", copy=False), dtype=float)
            single = False

        np.abs(grid, out=grid)
        grid_i = grid.astype(int)
        grid = grid - grid_i  # faster than in place for small matrices

        r = np.zeros(shape=grid.shape[1:])
        ampl = 0.5

        for _ in range(self.octaves):
            of = (
                grid_i[0, ...]
                + (grid_i[1, ...] << PERLIN_YWRAPB)
                + (grid_i[2, ...] << PERLIN_ZWRAPB)
            )

            r_f = 0.5 * (1.0 - np.cos(grid * math.pi))

            n1 = self._perlin[of % PERLIN_SIZE]
            n1 += r_f[0, ...] * (self._perlin[(of + 1) % PERLIN_SIZE] - n1)
            n2 = self._perlin[(of + PERLIN_YWRAP) % PERLIN_SIZE]
            n2 += r_f[0, ...] * (self._perlin[(of + PERLIN_YWRAP + 1) % PERLIN_SIZE] - n2)
            n1 += r_f[1, ...] * (n2 - n1)

            of += PERLIN_ZWRAP
            n2 = self._perlin[of % PERLIN_SIZE]
            n2 += r_f[0, ...] * (self._perlin[(of + 1) % PERLIN_SIZE] - n2)
            n3 = self._perlin[(of + PERLIN_YWRAP) % PERLIN_SIZE]
            n3 += r_f[0, ...] * (self._perlin[(of + PERLIN_YWRAP + 1) % PERLIN_SIZE] - n3)
            n2 += r_f[1, ...] * (n3 - n2)

            n1 += r_f[2, ...] * (n2 - n1)

            r += n1 * ampl
            ampl *= self.amp_falloff

            grid_i <<= 1
            grid *= 2

            idx = grid >= 1.0
            grid_i[idx] += 1
            grid[idx] -= 1.0

        return r.reshape(1, 1, 1) if single else r


def main():
    import matplotlib.pyplot as plt

    n = Noise()

    xx = np.linspace(0, 10, 100)
    yy = np.arange(30)
    perl = n.perlin(xx, np.linspace(0, 3, 30), 0)
    perl = perl[..., 0]

    for j in yy:
        plt.plot(np.arange(100) * 5.0, yy[j] * 10 + 100 * perl[:, j], "-b")

    plt.axis("square")
    plt.xlim(0, 640)
    plt.ylim(0, 360)

    plt.show()


def main_old():
    import matplotlib.pyplot as plt

    n = Noise()

    for j in range(30):
        x = np.arange(100)
        y = np.empty(100)

        for i in range(100):
            y[i] = n.perlin(i * 0.1, j * 0.1, 0)

        plt.plot(x * 5, j * 10 + 100 * y, "-b")

    plt.axis("square")
    plt.xlim(0, 640)
    plt.ylim(0, 360)

    plt.show()


if __name__ == "__main__":
    main_old()

    # print(Noise().noise_numpy(1, 0, 0))
    # import matplotlib.pyplot as plt
    #
    # n = Noise()
    #
    # basic = False
    # if not basic:
    #     xx = np.linspace(0, 10, 100)
    #     perl = n.noise_numpy(xx, np.linspace(0, 3, 30), 0)
    #     perl = perl[..., 0]
    #
    #     for j in range(30):
    #         plt.plot(xx, perl[:, j], "-b")
    # else:
    #     for j in range(30):
    #         x = np.arange(100)
    #         y = np.empty(100)
    #
    #         for i in range(100):
    #             y[i] = n.noise(i * 0.1, j * 0.1, 0)
    #
    #         plt.plot(x * 5, j * 10 + 100 * y, "-b")
    #
    # plt.axis("square")
    # plt.xlim(0, 640)
    # plt.ylim(0, 360)
    #
    # plt.show()
