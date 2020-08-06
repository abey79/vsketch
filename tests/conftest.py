import pytest

import vsketch


@pytest.fixture
def vsk():
    return vsketch.Vsketch()
