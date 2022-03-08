import numpy as np
import pytest

import vsketch


@pytest.mark.parametrize("mode", vsketch.EASING_FUNCTIONS.keys())
def test_easing_func_range(mode: str) -> None:
    for i in np.linspace(0, 1.0, num=51):
        for a in range(10):
            assert 0 <= vsketch.EASING_FUNCTIONS[mode](i, a)
