import numpy as np
import pytest

import vsketch


def test_random(vsk):
    for _ in range(1000):
        r = vsk.random(10)
        assert 0 <= r <= 10

        r = vsk.random(30, 40)
        assert 30 <= r <= 40


def test_random_seed(vsk):
    vsk.randomSeed(0)
    n1 = vsk.random(10)
    vsk.randomSeed(1)
    n2 = vsk.random(10)
    vsk.randomSeed(0)
    n3 = vsk.random(10)

    assert n1 != n2
    assert n1 == n3


def test_get_random_seed(vsk):
    vsk.randomSeed(0)
    n1 = vsk.random(10)
    assert vsk.random_seed == 0

    vsk.randomSeed(42)
    n2 = vsk.random(10)
    assert vsk.random_seed == 42

    vsk.randomSeed(0)
    n3 = vsk.random(10)
    assert vsk.random_seed == 0

    assert n1 != n2
    assert n1 == n3


def test_randomGaussian_seed(vsk):
    vsk.randomSeed(0)
    n1 = vsk.randomGaussian()
    vsk.randomSeed(1)
    n2 = vsk.randomGaussian()
    vsk.randomSeed(0)
    n3 = vsk.randomGaussian()

    assert n1 != n2
    assert n1 == n3


def test_random_seed_different():
    vsk1 = vsketch.Vsketch()
    vsk2 = vsketch.Vsketch()

    assert vsk1.random(10, 20) != vsk2.random(10, 20)


def test_noise_seed_different():
    vsk1 = vsketch.Vsketch()
    vsk2 = vsketch.Vsketch()

    assert vsk1.noise(0.5) != vsk2.noise(0.5)


def test_noise_seed(vsk):
    vsk.noiseSeed(0)
    n1 = vsk.noise(100)
    vsk.noiseSeed(2)
    n2 = vsk.noise(100)
    vsk.noiseSeed(0)
    n3 = vsk.noise(100)
    vsk.noiseSeed(100000)
    n4 = vsk.noise(100)

    assert n1 != n2
    assert n1 != n4
    assert n2 != n4
    assert n1 == n3


def test_noise_dimensions(vsk):
    assert isinstance(vsk.noise(0.1), float)
    assert isinstance(vsk.noise(0.1, 0.2), float)
    assert isinstance(vsk.noise(0.1, 0.2, 0.3), float)
    assert isinstance(vsk.noise(0.1, grid_mode=False), float)
    assert isinstance(vsk.noise(0.1, 0.2, grid_mode=False), float)
    assert isinstance(vsk.noise(0.1, 0.2, 0.3, grid_mode=False), float)

    assert vsk.noise([0, 1]).shape == (2,)
    assert vsk.noise([0, 1], 0.1).shape == (2,)
    assert vsk.noise([0, 1], 0.1, 0.2).shape == (2,)
    assert vsk.noise([0, 1], range(10, 13)).shape == (2, 3)
    assert vsk.noise([0, 1], range(10, 13), 0.5).shape == (2, 3)
    assert vsk.noise([0, 1], range(10, 13), np.linspace(0, 1, 100)).shape == (2, 3, 100)

    assert vsk.noise(np.linspace(0, 1, 100), grid_mode=False).shape == (100,)
    assert vsk.noise(
        np.linspace(0, 1, 100), np.linspace(10, 20, 100), grid_mode=False
    ).shape == (100,)
    assert vsk.noise(
        np.linspace(0, 1, 100), np.linspace(10, 20, 100), range(100), grid_mode=False
    ).shape == (100,)

    with pytest.raises(ValueError):
        vsk.noise(range(10), range(11), grid_mode=False)
    with pytest.raises(ValueError):
        vsk.noise(range(10), range(10), range(11), grid_mode=False)
