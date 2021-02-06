from typing import Any, Optional, Sequence, Tuple, TypeVar, Union

ParamType = Union[int, float, bool, str]


class Param:
    def __init__(
        self,
        value: ParamType,
        min_value: Optional[ParamType] = None,
        max_value: Optional[ParamType] = None,
        *,
        choices: Optional[Sequence[ParamType]] = None,
        step: Union[None, float, int] = None,
        decimals: Optional[int] = None,
    ):
        self.value: ParamType = value
        self.type = type(value)
        self.min = self.type(min_value) if min_value is not None else None  # type: ignore
        self.max = self.type(max_value) if max_value is not None else None  # type: ignore
        self.step = step
        self.decimals = decimals

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
        return self.value
