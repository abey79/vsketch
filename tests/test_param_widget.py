"""Tests for Qt-level enforcement of float parameter bounds in the interactive
viewer (vsketch_cli.param_widget.FloatParamWidget).

vsketch's model layer (vsketch.Param) already validates/clamps values, but the
GUI widget is a *second, independent* enforcement point. A QDoubleSpinBox snaps
both its range and its value to the current display precision, so if the
precision is too coarse for a declared bound the widget silently enforces the
wrong boundary.

These tests assert exact equality against the *widget's* reported minimum() /
maximum(), deliberately NOT using pytest.approx's default absolute tolerance:
approx (abs=1e-12) would wrongly treat a precision-snapped 0.0 as "close enough"
to a tiny bound such as 1e-16, masking the very bug under test. Exact equality
holds for every representable bound (QDoubleSpinBox round-trips a value that
fits in its `decimals`) and therefore genuinely discriminates the fix.
"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import vsketch
from vsketch_cli.param_widget import (
    _MAX_DISPLAY_DECIMALS,
    FloatParamWidget,
    _decimals_to_represent,
)


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def _widget(value, min_value, max_value, decimals=None):
    param = vsketch.Param(value, min_value, max_value, decimals=decimals)
    return FloatParamWidget(param)


# --------------------------------------------------------------------------- #
# Pure helper: number of decimals needed to represent a bound (no Qt state).  #
# --------------------------------------------------------------------------- #


def test_helper_bound_fits_original_precision():
    assert _decimals_to_represent(0.25, 2) == 2
    assert _decimals_to_represent(-1.5, 1) == 1


def test_helper_raises_for_finer_bound():
    assert _decimals_to_represent(0.001, 2) == 3
    assert _decimals_to_represent(-0.0005, 2) == 4


def test_helper_very_small_values_within_cap():
    # Smaller than the original 15-decimal cap, yet still representable.
    assert _decimals_to_represent(1e-16, 1) == 16
    assert _decimals_to_represent(1e-18, 1) == 18


def test_helper_beyond_cap_returns_cap():
    assert _decimals_to_represent(1e-19, 1) == _MAX_DISPLAY_DECIMALS
    # Prove it genuinely cannot be round-tripped at the cap.
    assert float(f"{1e-19:.{_MAX_DISPLAY_DECIMALS}f}") != 1e-19


# --------------------------------------------------------------------------- #
# Widget: enforced range equals the declared bound once it is representable.  #
# Exact equality is intentional (see module docstring).                       #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ["min_value", "max_value"],
    [
        (-0.0005, 0.0005),  # needs 4 decimals
        (-0.1234567, 0.0),  # needs 7 decimals, negative-only, zero-high
        (0.0, 2e-05),  # needs 5 decimals, positive-only, zero-low
        (-1e-16, 1e-16),  # finer than the OLD 15-decimal cap: real fix test
        (-1e-18, 1e-18),  # at the 18-decimal cap, still representable
    ],
)
def test_bounds_preserved_by_widget(qapp, min_value, max_value):
    widget = _widget(0.0, min_value, max_value)
    assert widget.minimum() == min_value
    assert widget.maximum() == max_value


def test_sub_cap_15_bound_precisely_preserved(qapp):
    # 1e-16 used to round to 0.0 under the old 15-decimal ceiling; exact equality
    # proves it is now genuinely enforced (not silently snapped to zero).
    widget = _widget(0.0, -1e-16, 1e-16)
    assert widget.maximum() == 1e-16 != 0.0
    assert widget.minimum() == -1e-16 != 0.0


@pytest.mark.parametrize("target", [-1.0, 1.0, 0.0])
def test_values_clamp_to_enforced_bound(qapp, target):
    widget = _widget(0.0, -0.0005, 0.0005)
    widget.setValue(target)
    assert widget.value() == min(0.0005, max(-0.0005, target))


def test_low_explicit_decimals_still_preserve_bound(qapp):
    # A bound finer than the declared `decimals` must not be lost; also proves
    # an over-large declared `decimals` is trimmed to what is needed.
    widget = _widget(0.0, -0.001, 0.001, decimals=1)
    assert widget.decimals() == 3
    assert widget.minimum() == -0.001
    assert widget.maximum() == 0.001


def test_bound_fits_original_precision_keeps_decimals(qapp):
    widget = _widget(0.5, 0.25, 0.75)
    assert widget.decimals() == 2
    assert widget.minimum() == 0.25
    assert widget.maximum() == 0.75


# --------------------------------------------------------------------------- #
# Widget: beyond-cap policy. The bound is NOT claimed to be preserved; the    #
# effective boundary is whatever QDoubleSpinBox reports via minimum/maximum.  #
# 1e-19 rounds to (signed) zero at 18 decimals, so the real enforced bound is #
# 0.0 -- which the widget must report truthfully instead of pretending 1e-19  #
# survived. (Note: -0.0 == 0.0 in Python, so exact equality holds.)           #
# --------------------------------------------------------------------------- #


def test_beyond_cap_effective_boundary_is_qts(qapp):
    widget = _widget(0.0, -1e-19, 1e-19)
    assert widget.decimals() == _MAX_DISPLAY_DECIMALS
    assert widget.minimum() == 0.0
    assert widget.maximum() == 0.0
    assert widget.maximum() != 1e-19  # exact compare; Qt snapped it to 0.0
