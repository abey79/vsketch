from typing import Any, Optional, Sequence, Tuple, Union

import vpype as vp

ParamType = Union[int, float, bool, str]


class Param:
    """This class encapsulate a sketch parameter.

    A sketch parameter can be interacted with in the ``vsk`` viewer.
    """

    def __init__(
        self,
        value: ParamType,
        min_value: Optional[ParamType] = None,
        max_value: Optional[ParamType] = None,
        *,
        choices: Optional[Sequence[ParamType]] = None,
        step: Union[None, float, int] = None,
        unit: str = "",
        decimals: Optional[int] = None,
    ):
        """Create a sketch parameter.

        This class implements a sketch parameter. Ts automatically recognized by ``vsk`` which
        generates the corresponding UI in the sketch interactive viewer. :class:`Param`
        instances must be declared as class member in the :class:`Vsketch` subclass and can
        then be used using the calling convention::

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
        self.value: ParamType = value
        self.type = type(value)
        self.min = self.type(min_value) if min_value is not None else None  # type: ignore
        self.max = self.type(max_value) if max_value is not None else None  # type: ignore
        self.step = step
        self.decimals = decimals
        self.unit = unit
        self.factor: Optional[float] = None if unit == "" else vp.convert_length(unit)

        self.choices: Optional[Tuple[ParamType, ...]] = None
        if choices is not None:
            self.choices = tuple(self.type(choice) for choice in choices)  # type: ignore

    def set_value(self, value: ParamType) -> None:
        """Assign a value without validation."""
        self.value = value

    def set_value_with_validation(self, v: Any) -> None:
        """Assign a value to the parameter provided that the value can be validated.

        The value must be of a compatible type and comply with the parameter's choices and
        bounds if defined.
        """
        try:
            value = self.type(v)  # type: ignore
        except ValueError:
            return

        if self.choices and value not in self.choices:
            return

        if self.min:
            value = max(self.min, value)

        if self.max:
            value = min(self.max, value)

        self.value = value

    def __call__(self) -> ParamType:
        if self.factor is None:
            return self.value
        else:
            return self.type(self.factor * self.value)  # type: ignore
