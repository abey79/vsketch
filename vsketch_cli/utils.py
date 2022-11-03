import inspect
import json
import os
import pathlib
import sys
import traceback
from runpy import run_path
from typing import Dict, Optional, Type

import click

import vsketch


def print_error(title_str: str, detail_str: str = "") -> None:
    click.echo(click.style(title_str, fg="red", bold=True) + str(detail_str), err=True)


def print_info(title_str: str, detail_str: str = "") -> None:
    click.echo(click.style(title_str, fg="green", bold=True) + str(detail_str), err=True)


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


def load_sketch_class(path: pathlib.Path) -> Optional[Type[vsketch.SketchClass]]:
    cwd_path = path
    if not cwd_path.is_dir():
        cwd_path = cwd_path.parent

    # noinspection PyBroadException
    try:
        with vsketch.working_directory(cwd_path):
            if str(cwd_path) not in sys.path:
                sys.path.insert(0, str(cwd_path))
            sketch_scripts = run_path(str(path))  # type: ignore
    except Exception:
        traceback.print_exc()
        print_error("Could not load script due to previous error.")
        return None

    for cls in sketch_scripts.values():
        if inspect.isclass(cls) and issubclass(cls, vsketch.SketchClass):
            cls.__vsketch_cwd__ = cwd_path  # type: ignore
            return cls
    return None


def get_config_path(path: pathlib.Path) -> pathlib.Path:
    """returns the config directory path from a sketch path"""
    config_path = path.parent / "config"
    if not config_path.exists():
        config_path.mkdir()
    return config_path


def load_config(path: pathlib.Path) -> Dict[str, vsketch.ParamType]:
    with open(path, "r") as fp:
        param_set = json.load(fp)
    return param_set
