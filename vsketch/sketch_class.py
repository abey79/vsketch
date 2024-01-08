from __future__ import annotations

import os
import pathlib
import random
from typing import Any, Generic, Iterable, Optional, TypeVar, Union, overload

import numpy as np
import vpype as vp

from .utils import working_directory
from .vsketch import Vsketch

ParamType = Union[int, float, bool, str]


class SketchClass:
    """Base class for sketch managed with the ``vsk`` CLI tool.

    Subclass must override :meth:`draw` and :meth:`finalize`.
    """

    def __init__(self):
        self._vsk = Vsketch()
        self._finalized = False
        self._params = self.get_params()

    @property
    def vsk(self) -> Vsketch:
        """:class:`Vsketch` instance"""
        return self._vsk

    def execute_draw(self) -> None:
        self.draw(self._vsk)

        # apply pen widths to the document's metadata
        for lid, layer in self._vsk.document.layers.items():
            pen_width = self._vsk.getPenWidth(lid)
            if pen_width is not None:
                layer.set_property(vp.METADATA_FIELD_PEN_WIDTH, pen_width)

    def ensure_finalized(self) -> None:
        if self._finalized:
            return

        self.finalize(self._vsk)

        # vsk is not reused, so we can just hack into it's document instead of using a deep
        # copy like vsk.display() and vsk.save()
        if self.vsk.centered and self.vsk.document.page_size is not None:
            bounds = self.vsk.document.bounds()
            if bounds is not None:
                width, height = self.vsk.document.page_size
                self.vsk.document.translate(
                    (width - (bounds[2] - bounds[0])) / 2.0 - bounds[0],
                    (height - (bounds[3] - bounds[1])) / 2.0 - bounds[1],
                )

        self._finalized = True

    @classmethod
    def execute(
        cls,
        seed: int | None = None,
        finalize: bool = False,
    ) -> Optional[SketchClass]:
        cwd = getattr(cls, "__vsketch_cwd__", pathlib.Path(os.getcwd()))
        with working_directory(cwd):
            sketch = cls()
            if sketch is None:
                return None

            if seed is not None:
                sketch.vsk.randomSeed(seed)
                sketch.vsk.noiseSeed(seed)
                random.seed(seed)
                np.random.seed(seed)
            sketch.execute_draw()
            if finalize:
                sketch.ensure_finalized()

        # vsk is not reused, so we can just hack into it's document instead of using a deep
        # copy like vsk.display() and vsk.save()
        vsk = sketch.vsk
        if vsk.centered and vsk.document.page_size is not None:
            bounds = vsk.document.bounds()
            if bounds is not None:
                width, height = vsk.document.page_size
                vsk.document.translate(
                    (width - (bounds[2] - bounds[0])) / 2.0 - bounds[0],
                    (height - (bounds[3] - bounds[1])) / 2.0 - bounds[1],
                )

        return sketch

    @classmethod
    def display(cls, *args: Any, **kwargs: Any) -> None:
        """Execute the sketch class and display the results using :meth:`Vsketch.display`.

        All parameters are forwarded to :meth:`Vsketch.display`.
        """
        sketch = cls.execute()
        if sketch is not None:
            sketch.vsk.display(*args, **kwargs)

    def draw(self, vsk: Vsketch) -> None:
        """Draws the sketch.

        This function must be implemented by subclasses.
        """
        raise NotImplementedError()

    def finalize(self, vsk: Vsketch) -> None:
        """Finalize the sketch before export.

        This function must be implemented by subclasses.
        """
        raise NotImplementedError()

    @classmethod
    def get_params(cls) -> dict[str, Param]:
        res = {}
        for name in cls.__dict__:
            param = getattr(cls, name)
            if isinstance(param, Param):
                res[name] = param
        return res

    @classmethod
    def set_param_set(cls, param_set: dict[str, Any]) -> None:
        for name, value in param_set.items():
            if name in cls.__dict__ and isinstance(cls.__dict__[name], Param):
                cls.__dict__[name].set_value_with_validation(value)

    @property
    def param_set(self) -> dict[str, Any]:
        return {name: param.value for name, param in self._params.items()}


_T = TypeVar("_T")


class Param(Generic[_T]):
    """Generic parameter for :class:`SketchClass`.

    This class implements a generic parameter for :class:`SketchClass` instances. Parameters
    can be interacted with in the ``vsk`` viewer and support functionalities such as saved
    configuration and parameter space exploration with ``vsk save``.
    """

    def __init__(
        self,
        value: _T,
        min_value: _T | None = None,
        max_value: _T | None = None,
        *,
        choices: Iterable[_T] | None = None,
        step: None | float | int = None,
        unit: str = "",
        decimals: int | None = None,
    ):
        """Create a sketch parameter.

        This class implements a sketch parameter. Ts automatically recognized by ``vsk`` which
        generates the corresponding UI in the sketch interactive viewer. :class:`Param`
        instances must be declared as class member in the :class:`Vsketch` subclass and can
        then be used with the calling convention::

            import vsketch
            class MySketch(vsketch.Vsketch):
                page_size = vsketch.Param("a4", choices=["a3", "a4", "a5"])

                def draw(self):
                    self.size(self.page_size())
                    # ...

        :class:`Param` can encapsulate the following types: :class:`int`, :class:`float`,
        :class:`str`, and :class:`bool`.

        For numeral types, a minimum and maximum value may be specified, as well as the step
        size to use in the UI::

            low_bound_param = vsketch.Param(10, 0, step=5)  # may not be lower than 0
            bounded_param = vsketch.Param(0.5, 0., 1.)  # must be within 0.0 and 1.0

        For these types, a unit may also be specified::

            margin = vsketch.Param(10., unit="mm")

        In this case, the unit will be displayed in the UI and the value converted to pixel
        when accessed by the sketch.

        :class:`float` parameters may further define the number of decimals to display in the
        UI::

            precise_param = vsketch.Param(0.01, decimals=5)

        Numeral types and string parameters may have a set of possibly choices::

            mode = vsketch.Param("simple", choices=["simple", "complex", "versatile"])
        """
        self.value: _T = value
        self.type = type(value)
        self.min = self.type(min_value) if min_value is not None else None  # type: ignore
        self.max = self.type(max_value) if max_value is not None else None  # type: ignore
        self.step = step
        self.decimals = decimals
        self.unit = unit
        self.factor: float | None = None if unit == "" else vp.convert_length(unit)

        self.choices: tuple[_T, ...] | None = None
        if choices is not None:
            self.choices = tuple(self.type(choice) for choice in choices)  # type: ignore

    def set_value(self, value: _T) -> None:
        """Assign a value without validation."""
        self.value = value

    def set_value_with_validation(self, v: Any) -> bool:
        """Assign a value to the parameter provided that the value can be validated.

        The value must be of a compatible type and comply with the parameter's choices and
        bounds if defined.

        Returns:
            returns True if the value was successfully updated
        """
        try:
            # bool("False") == True, so we need to check for str first
            if self.type is bool and isinstance(v, str):
                v = v.lower() in ("true", "1", "yes", "y")

            value = self.type(v)  # type: ignore
        except ValueError:
            return False

        if self.choices and value not in self.choices:
            return False

        if self.min is not None:
            value = max(self.min, value)  # type: ignore

        if self.max is not None:
            value = min(self.max, value)  # type: ignore

        self.value = value
        return True

    @overload
    def __get__(self, instance: None, owner: None) -> Param:
        ...

    @overload
    def __get__(self, instance: object, owner: type[object]) -> _T:
        ...

    def __get__(
        self, instance: object | None, owner: type[object] | None = None
    ) -> Union[_T, Param]:
        if instance is None:
            return self

        if self.factor is None:
            return self.value
        else:
            return self.type(self.factor * self.value)  # type: ignore
