import inspect
import os
import pathlib
from runpy import run_path
from typing import Optional, Type, Union

import vsketch


def remove_prefix(s: str, prefix: str) -> str:
    return s[len(prefix) :] if s.startswith(prefix) else s


def remove_postfix(s: str, postfix: str) -> str:
    return s[: -len(postfix)] if s.endswith(postfix) else s


def canonical_name(path: pathlib.Path) -> str:
    return remove_postfix(remove_prefix(path.name, "sketch_"), ".py")


def find_unique_path(
    filename: str, dir_path: pathlib.Path, always_number: bool = False
) -> pathlib.Path:
    """Find a unique (i.e. which not currently exists) path for a file in directory.

    If always_number is False, always append a number to the file name, starting with 1.
    Otherwise prepend only if a file already exists, starting with 2.
    """
    base_name, ext = os.path.splitext(filename)
    name = base_name
    index = 1 if always_number else 2
    while True:
        if always_number:
            name = base_name + "_" + str(index)
        path = dir_path / (name + ext)
        if not path.exists():
            break
        if not always_number:
            name = base_name + "_" + str(index)
        index += 1
    return path


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
