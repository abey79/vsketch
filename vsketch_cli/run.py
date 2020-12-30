from runpy import run_path

import watchgod

import vsketch


def load_and_save(path: str):
    sketch = run_path(path)
    vsk = vsketch.Vsketch()
    sketch["setup"](vsk)
    sketch["draw"](vsk)
    sketch["finalize"](vsk)
    vsk.display()


def run_directory(path: str):
    """TODO

    Look for sketch.py, or look for any single python file
    """

    watchgod.run_process(path, load_and_save, args=(path,))
