import pathlib
from runpy import run_path
from typing import Optional, Union

import vpype as vp

import vsketch


def execute_sketch(
    path: Union[str, pathlib.Path], finalize: bool, seed: Optional[int] = None
) -> vp.Document:
    sketch = run_path(str(path))
    vsk = vsketch.Vsketch()
    sketch["setup"](vsk)
    if seed is not None:
        vsk.randomSeed(seed)
        vsk.noiseSeed(seed)
    sketch["draw"](vsk)
    if finalize:
        sketch["finalize"](vsk)
    return vsk.document
