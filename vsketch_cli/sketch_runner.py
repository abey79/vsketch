import asyncio
import inspect
import pathlib
from runpy import run_path
from typing import Callable, Optional, Union

import vpype as vp
import watchgod

import vsketch


class SketchRunner:
    def __init__(
        self,
        path: Union[str, pathlib.Path],
        pre_load_callback: Optional[Callable[["SketchRunner"], None]] = None,
        post_load_callback: Optional[Callable[["SketchRunner"], None]] = None,
    ):
        self._path = str(path)
        self._sketch_type = None
        self._pre_load_cb = pre_load_callback
        self._post_load_cb = post_load_callback
        self._reload()

    def _reload(self) -> None:
        if self._pre_load_cb:
            self._pre_load_cb(self)

        self._sketch_type = None
        sketch_scripts = run_path(self._path)
        for var in sketch_scripts.values():
            if inspect.isclass(var) and issubclass(var, vsketch.Vsketch):
                self._sketch_type = var
                break

        if self._post_load_cb:
            self._post_load_cb(self)

    def run(self, finalize: bool = False, seed: Optional[int] = None) -> vp.Document:
        vsk = self._sketch_type()
        vsk.setup()
        if seed is not None:
            vsk.randomSeed(seed)
            vsk.noiseSeed(seed)
        vsk.draw()
        if finalize:
            vsk.finalize()
        return vsk.document

    async def watch(self):

        try:
            async for changes in watchgod.awatch(self._path):
                print(changes)
                for change in changes:
                    if change[1] == self._path and change[0] == watchgod.Change.modified:
                        self._reload()

        except asyncio.CancelledError:
            print("cancelled")
