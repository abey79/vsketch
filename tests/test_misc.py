import numpy as np


def test_map(vsk):
    assert vsk.map(0.5, 0, 1, 50, 70) == 60
    assert vsk.map(-1, 0, 1, 60, 70) == 50
    assert vsk.map(2, 1, 0, 30, 40) == 20


def test_map_numpy(vsk):
    arr = np.linspace(0, 10, 1000)
    assert np.all(np.isclose(vsk.map(arr, 0, 10, 20, 30), arr + 20))


def test_lerp(vsk):
    assert vsk.lerp(1, 10, 0.5) == 5.5
    assert vsk.lerp(complex(0, 10), complex(20, 20), 0.2) == complex(4.0, 12.0)
    assert np.all(
        np.isclose(
            vsk.lerp(np.array([0, 1, 2]), np.array([10, 11, 12]), 0.8),
            np.array([8.0, 9.0, 10.0]),
        )
    )
