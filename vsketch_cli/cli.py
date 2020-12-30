from typing import Optional

import typer

from .run import run_directory

cli = typer.Typer()


@cli.command()
def init(name: str = typer.Argument(..., help="project name")):
    typer.echo(f"Init project {name}")


@cli.command()
def run(name: Optional[str] = typer.Argument(default=None, help="project name")):
    if name is None:
        typer.echo("Running current")
    else:
        run_directory(name)
