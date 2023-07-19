import pytest

from vsketch.sketch_class import Param


@pytest.mark.parametrize(
    ["initial_value", "min_value", "max_value", "set_value"],
    [
        [0.0, -5.0, 5.0, 0.0],  # set equal to initial value
        [0.0, -5.0, 5.0, 0.5],  # set within bounds
        [0.0, -5.0, 5.0, -10.0],  # set below min_value
        [0.0, -5.0, 5.0, 10.0],  # set above max_value
        [0.0, 0.0, 5.0, -10.0],  # set below min_value = 0.0
        [0.0, -5.0, 0.0, 10.0],  # set above max_value = 0.0
    ],
)
def test_float_param_bounds(initial_value, min_value, max_value, set_value):
    """
    Tests that sketch_class.Param.set_value_with_validation respects min_value and max_value, and
    clamps values to be within that range.
    """
    float_param = Param(initial_value, min_value=min_value, max_value=max_value)
    float_param.set_value_with_validation(set_value)
    assert float_param.value == min(max_value, max(min_value, set_value))
