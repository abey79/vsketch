from typing import Any, Dict, Mapping

from PySide2.QtCore import Signal
from PySide2.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QSpinBox,
    QTextEdit,
    QWidget,
)

import vsketch


class ChoiceParamWidget(QComboBox):
    value_changed = Signal()

    def __init__(self, param: vsketch.Param, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._param = param
        if param.choices is not None:
            for choice in param.choices:
                self.addItem(str(choice), choice)
        self.setCurrentText(str(param.value))
        self.currentTextChanged.connect(self.update_param)

    def update_param(self) -> None:
        self._param.set_value_with_validation(self.currentData())
        # noinspection PyUnresolvedReferences
        self.value_changed.emit()  # type: ignore

    def set_value(self, value: Any) -> None:
        self._param.set_value_with_validation(value)
        self.setCurrentText(str(self._param.value))


class IntParamWidget(QSpinBox):
    value_changed = Signal()

    def __init__(self, param: vsketch.Param, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._param = param
        self.setValue(int(param.value))
        if param.bounds:
            self.setRange(int(param.bounds[0]), int(param.bounds[1]))

        self.valueChanged.connect(self.update_param)

    def update_param(self) -> None:
        self._param.set_value_with_validation(self.value())
        # noinspection PyUnresolvedReferences
        self.value_changed.emit()  # type: ignore

    def set_value(self, value: Any) -> None:
        self._param.set_value_with_validation(value)
        self.setValue(int(self._param.value))


class FloatParamWidget(QDoubleSpinBox):
    value_changed = Signal()

    def __init__(self, param: vsketch.Param, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._param = param
        self.setValue(float(param.value))
        if param.bounds:
            self.setRange(float(param.bounds[0]), float(param.bounds[1]))

        self.valueChanged.connect(self.update_param)

    def update_param(self):
        self._param.set_value_with_validation(self.value())
        # noinspection PyUnresolvedReferences
        self.value_changed.emit()

    def set_value(self, value: Any) -> None:
        self._param.set_value_with_validation(value)
        self.setValue(float(self._param.value))


class TextParamWidget(QTextEdit):
    value_changed = Signal()

    def __init__(self, param: vsketch.Param, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._param = param

        self.setText(str(param.value))
        self.textChanged.connect(self.update_param)

    def update_param(self):
        self._param.set_value_with_validation(self.text())
        # noinspection PyUnresolvedReferences
        self.value_changed.emit()

    def set_value(self, value: Any) -> None:
        self._param.set_value_with_validation(value)
        self.setText(str(self._param.value))


def _beautify(name: str) -> str:
    """Concert variable name to a user friendly string."""
    return name.replace("_", " ").title()


class ParamsWidget(QWidget):
    paramUpdated = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._widgets: Dict[str, Any] = {}

        # layout
        self._layout = QFormLayout()
        self.setLayout(self._layout)

    def set_params(self, params: Mapping[str, vsketch.Param]) -> None:
        # clean up
        while self._layout.rowCount() > 0:
            self._layout.removeRow(0)
        self._widgets.clear()

        # create new widgets
        for name, param in params.items():
            if param.choices is not None:
                widget = ChoiceParamWidget(param)
            elif param.type is int:
                widget = IntParamWidget(param)
            elif param.type is float:
                widget = FloatParamWidget(param)
            else:
                widget = TextParamWidget(param)

            # noinspection PyUnresolvedReferences
            widget.value_changed.connect(self.emitParamUpdated)  # type: ignore

            # update the widget
            self._widgets[name] = widget
            self._layout.addRow(_beautify(name), widget)

    def set_param_set(self, param_set: Mapping[str, Any]) -> None:
        for name, value in param_set.items():
            if name in self._widget and hasattr(self._widget[name], "set_value"):
                self._widget.set_value(value)

    def emitParamUpdated(self) -> None:
        # noinspection PyUnresolvedReferences
        self.paramUpdated.emit()  # type: ignore
