from typing import Any, Optional, Sequence, Tuple, TypeVar

T = TypeVar("T")


class Param:
    def __init__(
        self,
        value: T,
        choices: Optional[Sequence[T]] = None,
        bounds: Optional[Tuple[T, T]] = None,
    ):
        self.value: T = value
        self.type = type(value)

        self.choices: Optional[Tuple[T, ...]] = None
        if choices is not None:
            self.choices = tuple(self.type(choice) for choice in choices)  # type: ignore

        self.bounds: Optional[Tuple[T, T]] = None
        if bounds is not None:
            self.bounds = self.type(bounds[0]), self.type(bounds[1])  # type: ignore

    def set_value(self, value: T) -> None:
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

        if self.bounds:
            value = min(self.bounds[1], max(self.bounds[0], value))  # type: ignore

        self.value = value

    def __call__(self) -> T:
        return self.value
