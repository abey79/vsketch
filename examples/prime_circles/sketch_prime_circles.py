import math

import numpy as np

import vsketch


def get_primes(n):
    numbers = set(range(n, 1, -1))
    primes = []
    while numbers:
        p = numbers.pop()
        primes.append(p)
        numbers.difference_update(set(range(p * 2, n + 1, p)))
    return primes


class PrimeCirclesSketch(vsketch.Vsketch):
    N = vsketch.Param(100, 0)
    random_phase = vsketch.Param(False)

    def draw(self) -> None:
        self.size("10in", "10in")
        self.scale("3mm")

        for i, prime in enumerate(get_primes(self.N())):
            self.circle(0, 0, 2 * (i + 1))

            if self.random_phase():
                phase = np.random.random() * 2 * math.pi
            else:
                phase = -math.pi / 2

            for angle in np.linspace(0, 2 * math.pi, prime, endpoint=False):
                self.line(
                    (i + 1) * math.cos(angle + phase),
                    (i + 1) * math.sin(angle + phase),
                    (i + 2) * math.cos(angle + phase),
                    (i + 2) * math.sin(angle + phase),
                )

        self.circle(0, 0, 2 * (i + 2))

    def finalize(self) -> None:
        self.vpype("linemerge linesimplify reloop linesort")
