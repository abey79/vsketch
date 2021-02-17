import math
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

    def perlin(
        self,
        x: Union[float, Sequence[float]],
        y: Union[float, Sequence[float]],
        z: Union[float, Sequence[float]],
    ) -> np.ndarray:
        """Compute perlin noise for a range of values.

        Each of the x, y, and z argument may be 1D sequence of float. Perlin noise will be
        computed for each combination of each of the input argument and returns them in a
        Numpy array of shape (len(x), len(y), len(z)). If any of the input are scalar, they are
        interpreted as a length-1 array.
        """
        grid = np.abs(np.array(np.meshgrid(x, y, z, indexing="ij", copy=False), dtype=float))
        grid_i = np.floor(grid).astype(int)
        grid_f = grid - grid_i

        r = np.zeros(shape=grid.shape[1:])
        ampl = 0.5

        for _ in range(self.octaves):
            of = (
                grid_i[0, ...]
                + (grid_i[1, ...] << PERLIN_YWRAPB)
                + (grid_i[2, ...] << PERLIN_ZWRAPB)
            )

            r_f = 0.5 * (1.0 - np.cos(grid_f * math.pi))

            n1 = self._perlin[of & PERLIN_SIZE]
            n1 += r_f[0, ...] * (self._perlin[(of + 1) & PERLIN_SIZE] - n1)
            n2 = self._perlin[(of + PERLIN_YWRAP) & PERLIN_SIZE]
            n2 += r_f[0, ...] * (self._perlin[(of + PERLIN_YWRAP + 1) & PERLIN_SIZE] - n2)
            n1 += r_f[1, ...] * (n2 - n1)

            of += PERLIN_ZWRAP
            n2 = self._perlin[of & PERLIN_SIZE]
            n2 += r_f[0, ...] * (self._perlin[(of + 1) & PERLIN_SIZE] - n2)
            n3 = self._perlin[(of + PERLIN_YWRAP) & PERLIN_SIZE]
            n3 += r_f[0, ...] * (self._perlin[(of + PERLIN_YWRAP + 1) & PERLIN_SIZE] - n3)
            n2 += r_f[1, ...] * (n3 - n2)

            n1 += r_f[2, ...] * (n2 - n1)

            r += n1 * ampl
            ampl *= self.amp_falloff

            grid_i <<= 1
            grid_f *= 2

            idx = grid_f >= 1.0
            grid_i[idx] += 1
            grid_f[idx] -= 1.0

        return r


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


if __name__ == "__main__":
    main()

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
