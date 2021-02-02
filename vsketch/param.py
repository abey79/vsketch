from typing import Optional, Sequence, Tuple, TypeVar

T = TypeVar("T")


class Param:
    def __init__(
        self,
        name: str,
        value: T,
        choices: Optional[Sequence[T]] = None,
        bounds: Optional[Tuple[T, T]] = None,
    ):
        self.name: str = name
        self.value: T = value
        self._type = type(value)

        if choices is not None:
            self.choices = tuple(self._type(choice) for choice in choices)
        else:
            self.choices = None

        if bounds is not None:
            self.bounds = self._type(bounds[0]), self._type(bounds[1])
        else:
            self.bounds = None
