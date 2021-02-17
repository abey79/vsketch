import numbers

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
    assert isinstance(vsk.noise(1.5), numbers.Number)

    assert vsk.noise([0, 1]).shape == (2,)
    assert vsk.noise([0, 1], 3).shape == (2,)
    assert vsk.noise([0, 1], [2, 3, 4]).shape == (2, 3)
    assert vsk.noise([0, 1], [2, 3, 4], 4).shape == (2, 3)
    assert vsk.noise([0, 1], [2, 3, 4], [5, 6, 7, 8]).shape == (2, 3, 4)
    assert vsk.noise([0, 1], 4, [5, 6, 7, 8]).shape == (2, 4)
    assert vsk.noise(4, 4, [5, 6, 7, 8]).shape == (4,)
    assert vsk.noise(4, [0, 1], [5, 6, 7, 8]).shape == (2, 4)
