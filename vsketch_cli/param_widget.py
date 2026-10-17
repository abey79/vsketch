import math
from typing import Any, Dict, Mapping

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QTextEdit,
)

import vsketch

_MAX_INT = (2**31) - 1

# ``QDoubleSpinBox`` renders values with a fixed number of decimal places and,
# crucially, snaps its *range bounds* to that precision. A declared bound that
# is finer than the current precision is therefore silently altered by Qt:
# ``min_value=0.001`` at two decimals becomes an effective minimum of ``0.00``
# (letting the user type ``0``), while ``min_value=0.05`` at one decimal becomes
# ``0.1`` (tightening past what the sketch declared).
#
# To counter this we raise the number of decimals until every declared bound
# survives a round-trip through the fixed-notation text format that Qt uses
# internally, up to a hard ceiling. The ceiling is 18 decimals: it is well
# beyond any bound a sketch realistically declares, and was verified against
# the actual Qt behaviour (e.g. ``1e-16`` and ``1e-18`` round-trip exactly at
# this cap). Doubles whose spacing is finer than 1e-18 -- e.g. ``1e-19`` or
# ``nextafter(1e-18)`` -- need more precision than the cap can display and
# fall through to the documented beyond-cap policy below.
#
# Bounds needing *more* than the cap (subnormal-magnitude values such as
# ``1e-19``) cannot be displayed faithfully. Rather than imply that the declared
# bound still holds, the widget falls back to the cap and lets Qt clamp the
# bound to the nearest representable value; the enforced minimum/maximum is then
# exactly ``QDoubleSpinBox.minimum()``/``maximum()``, which callers and tests
# should read as the real boundary. This is documented and exercised in the
# test suite.
_MAX_DISPLAY_DECIMALS = 18


def _decimals_to_represent(x: float, start: int) -> int:
    """Smallest number of decimals >= ``start`` at which ``x`` round-trips
    through fixed-notation formatting (the precision model Qt applies when
    snapping spinbox range bounds), capped at ``_MAX_DISPLAY_DECIMALS``.

    If ``x`` cannot be represented within the cap, the cap is returned; the
    caller should treat the resulting spinbox ``minimum()``/``maximum()`` as the
    effective bound rather than assuming ``x`` itself was preserved.
    """
    d = max(1, start)
    while d <= _MAX_DISPLAY_DECIMALS:
        if float(f"{x:.{d}f}") == x:
            return d
        d += 1
    return _MAX_DISPLAY_DECIMALS


class ChoiceParamWidget(QComboBox):
    value_changed = Signal()

    def __init__(self, param: vsketch.Param, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._param = param
        if param.choices is not None:
            for choice in param.choices:
                self.addItem(str(choice), choice)
        self.setCurrentText(str(param.value))
        self.currentTextChanged.connect(self.update_param)  # type: ignore

    def update_param(self) -> None:
        self._param.set_value_with_validation(self.currentData())
        # noinspection PyUnresolvedReferences
        self.value_changed.emit()  # type: ignore

    def update_from_param(self) -> None:
        self.setCurrentText(str(self._param.value))


class IntParamWidget(QSpinBox):
    value_changed = Signal()

    def __init__(self, param: vsketch.Param, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._param = param

        if param.step is not None:
            self.setSingleStep(int(param.step))
        self.setRange(
            int(param.min) if param.min is not None else -_MAX_INT,
            int(param.max) if param.max is not None else _MAX_INT,
        )

        self.setValue(int(param.value))
        self.valueChanged.connect(self.update_param)  # type: ignore

    def update_param(self) -> None:
        self._param.set_value_with_validation(self.value())
        # noinspection PyUnresolvedReferences
        self.value_changed.emit()  # type: ignore

    def update_from_param(self) -> None:
        self.setValue(int(self._param.value))


class FloatParamWidget(QDoubleSpinBox):
    value_changed = Signal()

    def __init__(self, param: vsketch.Param, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._param = param
        val = float(param.value)
        if param.decimals is not None:
            decimals = param.decimals
        elif val == 0.0:
            decimals = 1
        else:
            decimals = max(1, 1 - math.floor(math.log10(abs(val))))
        # Raise the precision until every declared bound survives Qt's snapping
        # to the display precision, so the UI enforces what the sketch declares
        # (see the note above _MAX_DISPLAY_DECIMALS for the beyond-cap case).
        # ``singleStep`` is not snapped by Qt and needs no such treatment.
        for extra in (param.min, param.max):
            if extra is not None:
                decimals = max(decimals, _decimals_to_represent(float(extra), decimals))
        self.setDecimals(decimals)
        if param.step is not None:
            self.setSingleStep(param.step)
        else:
            self.setStepType(QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
            self.setSingleStep(val / 10)
        self.setRange(
            float(param.min) if param.min is not None else -1e100,
            float(param.max) if param.max is not None else 1e100,
        )

        self.setValue(val)
        self.valueChanged.connect(self.update_param)  # type: ignore

    def update_param(self):
        self._param.set_value_with_validation(self.value())
        # noinspection PyUnresolvedReferences
        self.value_changed.emit()

    def update_from_param(self) -> None:
        self.setValue(float(self._param.value))


class TextParamWidget(QTextEdit):
    value_changed = Signal()

    def __init__(self, param: vsketch.Param, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._param = param

        self.setText(str(param.value))
        self.textChanged.connect(self.update_param)  # type: ignore

    def update_param(self):
        self._param.set_value_with_validation(self.toPlainText())  # type: ignore
        # noinspection PyUnresolvedReferences
        self.value_changed.emit()

    def update_from_param(self) -> None:
        self.setText(str(self._param.value))


class BoolParamWidget(QCheckBox):
    value_changed = Signal()

    def __init__(self, param: vsketch.Param, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._param = param

        self.setChecked(bool(param.value))
        self.stateChanged.connect(self.update_param)  # type: ignore

    def update_param(self):
        self._param.set_value_with_validation(self.isChecked())
        # noinspection PyUnresolvedReferences
        self.value_changed.emit()

    def update_from_param(self) -> None:
        self.setChecked(bool(self._param.value))


def _beautify(name: str) -> str:
    """Concert variable name to a user friendly string."""
    return name.replace("_", " ").title()


class ParamsWidget(QGroupBox):
    paramUpdated = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__("Parameters", *args, **kwargs)

        self._widgets: Dict[str, Any] = {}

        # layout
        self._layout = QFormLayout()
        self.setLayout(self._layout)

    def set_params(self, params: Mapping[str, vsketch.Param]) -> None:
        # clean up
        while self._layout.rowCount() > 0:
            self._layout.removeRow(0)
        self._widgets.clear()

        # hide if empty
        self.setVisible(len(params) > 0)

        # create new widgets
        for name, param in params.items():
            if param.choices is not None:
                widget: Any = ChoiceParamWidget(param)
            elif param.type is int:
                widget = IntParamWidget(param)
            elif param.type is float:
                widget = FloatParamWidget(param)
            elif param.type is bool:
                widget = BoolParamWidget(param)
            else:
                widget = TextParamWidget(param)

            # noinspection PyUnresolvedReferences
            widget.value_changed.connect(self.emitParamUpdated)  # type: ignore

            # update the widget
            self._widgets[name] = widget
            label = _beautify(name)
            if param.unit != "":
                label += f" ({param.unit})"
            label += ":"
            self._layout.addRow(label, widget)

    def update_from_param(self):
        for widget in self._widgets.values():
            widget.blockSignals(True)
            widget.update_from_param()
            widget.blockSignals(False)

    # def set_param_set(self, param_set: Mapping[str, Any]) -> None:
    #     for name, value in param_set.items():
    #         if name in self._widgets and hasattr(self._widgets[name], "set_value"):
    #             self._widgets[name].set_value(value)

    def emitParamUpdated(self) -> None:
        # noinspection PyUnresolvedReferences
        self.paramUpdated.emit()  # type: ignore
