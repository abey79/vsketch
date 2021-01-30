import pathlib
from typing import Optional

import typer

from .gui import show

cli = typer.Typer()


def _find_candidates(path: pathlib.Path, glob: str) -> Optional[str]:
    candidates = list(path.glob(glob))
    if len(candidates) == 1:
        return str(candidates[0].absolute())
    elif len(candidates) > 1:
        raise ValueError(
            f"target {path.absolute()} is ambiguous, possible scripts:\n"
            + "\n".join(f" - {candidate.name}" for candidate in candidates)
        )
    else:
        return None


def _find_sketch_script(path: Optional[str]) -> str:
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
        return str(path.absolute())
    else:
        raise ValueError(f"target {path.absolute()} is not a Python file")


@cli.command()
def init(name: str = typer.Argument(..., help="project name")):
    typer.echo(f"Init project {name}")


@cli.command()
def run(target: Optional[str] = typer.Argument(default=None, help="project name")):
    try:
        path = _find_sketch_script(target)
    except ValueError as err:
        typer.echo(
            typer.style("Sketch could not be found: ", fg=typer.colors.RED, bold=True)
            + str(err)
        )
        return

    show(path)
