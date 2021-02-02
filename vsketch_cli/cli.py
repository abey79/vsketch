import os
import pathlib
import random
from typing import Optional, Tuple

import typer
import vpype as vp
from cookiecutter.main import cookiecutter

from .gui import show
from .sketch_runner import SketchRunner

cli = typer.Typer()


def _find_candidates(path: pathlib.Path, glob: str) -> Optional[pathlib.Path]:
    candidates = list(path.glob(glob))
    if len(candidates) == 1:
        return candidates[0].absolute()
    elif len(candidates) > 1:
        raise ValueError(
            f"target {path.absolute()} is ambiguous, possible scripts:\n"
            + "\n".join(f" - {candidate.name}" for candidate in candidates)
        )
    else:
        return None


def _find_sketch_script(path: Optional[str]) -> pathlib.Path:
    """Implements the logics of finding the sketch script:

    - if path is dir, look for a unique ``sketch_*.py`` file (return if exists, fail if many)
    - if none, look for a unique  ``*.py`` file (return if exists, fail if none or many)
    - if path is file, check if it ends with ``.py`` and fail otherwise

    """
    path = pathlib.Path().cwd() if path is None else pathlib.Path(path)

    if path.is_dir():
        # find  suitable sketch
        candidate_path = _find_candidates(path, "sketch_*.py")
        if candidate_path is None:
            candidate_path = _find_candidates(path, "*.py")

        if candidate_path is None:
            raise ValueError(
                f"target directory {path.absolute()} does not contain a sketch script"
            )
        else:
            return candidate_path
    elif path.suffix == ".py":
        return path.absolute()
    else:
        raise ValueError(f"target {path.absolute()} is not a Python file")


@cli.command()
def init(
    name: str = typer.Argument(..., help="project name"),
    page_size: str = typer.Option("a4", "--page-size", "-p", prompt=True, help="page size"),
    landscape: bool = typer.Option(
        False, "--landscape", "-l", prompt=True, help="use landscape orientation"
    ),
):
    slug = name.replace(" ", "_")
    cookiecutter(
        "https://github.com/abey79/cookiecutter-vsketch-sketch.git",
        no_input=True,
        extra_context={
            "sketch_name": name,
            "sketch_slug": slug,
            "page_size": page_size,
            "landscape": str(landscape),
        },
    )


def _target_not_found_error(err: ValueError):
    typer.echo(
        typer.style("Sketch could not be found: ", fg=typer.colors.RED, bold=True) + str(err),
        err=True,
    )


def _parse_seed(seed: str) -> Tuple[int, int]:
    seed_parts = seed.split("..")
    if len(seed_parts) == 1:
        return int(seed_parts[0]), int(seed_parts[0])
    elif len(seed_parts) == 2:
        return int(seed_parts[0]), int(seed_parts[1])
    else:
        raise ValueError(f"error parsing seed {seed}")


@cli.command()
def run(
    target: Optional[str] = typer.Argument(default=None, help="Sketch directory or file."),
    editor: Optional[str] = typer.Option(
        None, "-e", "--editor", help="Editor command to use."
    ),
):
    """Show and monitor a sketch.

    TARGET may either point at a Python file or at a directory. If omitted, the current
    directory is assumed. When TARGET points at a directory, this command looks for a single
    Python file whose name starts wit `sketch_`. If none are found, it will look for a single
    Python file with arbitrary name. If no or multiple candidates are found, the command will
    fail.
    """
    try:
        path = _find_sketch_script(target)
    except ValueError as err:
        _target_not_found_error(err)
        return

    typer.echo(
        typer.style("Running sketch: ", fg=typer.colors.GREEN, bold=True) + str(path), err=True
    )

    if editor is not None:
        os.system(f"{editor} {path}")

    show(str(path), second_screen=True)


@cli.command()
def save(
    target: Optional[str] = typer.Argument(default=None, help="sketch directory or file"),
    name: Optional[str] = typer.Option(
        None, "-n", "--name", help="output name (without extension)"
    ),
    seed: Optional[str] = typer.Option(None, "-s", "--seed", help="Seed to "),
):
    try:
        path = _find_sketch_script(target)
    except ValueError as err:
        _target_not_found_error(err)
        return

    if name is None:
        name = path.name.lstrip("sketch_").rstrip(".py")

    seed_in_name = seed is not None

    if seed is None:
        seed_start = seed_end = random.randint(0, 2 ** 31 - 1)
    else:
        try:
            seed_start, seed_end = _parse_seed(seed)
        except ValueError as err:
            typer.echo(
                typer.style(f"Could not parse seed {seed}: ", fg=typer.colors.RED, bold=True)
                + str(err),
                err=True,
            )
            return

    # TODO: parallelize
    for seed in range(seed_start, seed_end + 1):
        output_name = name
        if seed_in_name:
            output_name += "_s" + str(seed)
        output_name += ".svg"
        output_path = path.parent / output_name

        typer.echo(
            typer.style("Saving sketch: ", fg=typer.colors.GREEN, bold=True)
            + str(path)
            + f" (seed: {seed}, destination: {output_name})",
            err=True,
        )
        sketch_runner = SketchRunner(path)
        doc = sketch_runner.run(finalize=True, seed=seed)
        with open(output_path, "w") as fp:
            vp.write_svg(fp, doc, source_string=f"vsketch save -s {seed} {path}")
