import inspect
import pathlib
from runpy import run_path
from typing import Optional, Type, Union

import vsketch


def load_sketch_class(path: Union[str, pathlib.Path]) -> Optional[Type[vsketch.Vsketch]]:
    sketch_scripts = run_path(str(path))  # type: ignore
    for cls in sketch_scripts.values():
        if inspect.isclass(cls) and issubclass(cls, vsketch.Vsketch):
            return cls
    return None


def execute_sketch(
    sketch_class: Optional[Type[vsketch.Vsketch]] = None,
    seed: Optional[int] = None,
    finalize: bool = False,
) -> Optional[vsketch.Vsketch]:
    if sketch_class is None:
        return None

    vsk = sketch_class()
    if vsk is None:
        return None

    if seed is not None:
        vsk.randomSeed(seed)
        vsk.noiseSeed(seed)
    vsk.draw()
    if finalize:
        vsk.finalize()

    # vsk is not reused, so we can just hack into it's document instead of using a deep copy
    # like vsk.display() and vsk.save()
    if vsk.centered and vsk.document.page_size is not None:
        bounds = vsk.document.bounds()
        if bounds is not None:
            width, height = vsk.document.page_size
            vsk.document.translate(
                (width - (bounds[2] - bounds[0])) / 2.0 - bounds[0],
                (height - (bounds[3] - bounds[1])) / 2.0 - bounds[1],
            )

    return vsk
