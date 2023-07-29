import dataclasses
import itertools
import os
import pathlib
import random
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union, cast

import click
import vpype as vp
from cookiecutter.main import cookiecutter
from multiprocess.pool import Pool

import vsketch

from .gui import show
from .utils import (
    canonical_name,
    get_config_path,
    load_config,
    load_sketch_class,
    print_error,
    print_info,
)


@click.group()
@click.version_option(vsketch.__version__)
def cli():
    pass


# this is somehow needed to make PyCharm happy with runner.invoke(cli, ...)
if TYPE_CHECKING:  # pragma: no cover
    cli = cast(click.Group, cli)


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


def _find_sketch_script(path: Optional[pathlib.Path]) -> pathlib.Path:
    """Implements the logics of finding the sketch script:

    - if path is dir, look for a unique ``sketch_*.py`` file (return if exists, fail if many)
    - if none, look for a file named exactly ``sketch.py`` (return if exists)
    - if none, look for a unique  ``*.py`` file (return if exists, fail if none or many)
    - if path is file, check if it ends with ``.py`` and fail otherwise

    """
    path = pathlib.Path().cwd() if path is None else path

    if path.is_dir():
        # find  suitable sketch
        candidate_globs = ["sketch_*.py", "sketch.py", "*.py"]
        for glob_pattern in candidate_globs:
            candidate_path = _find_candidates(path, glob_pattern)
            if candidate_path is not None:
                break

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


INIT_HELP = f"""Create a new sketch project.

This command creates a new directory named TARGET and containing the structure for a new
sketch project. TARGET may also be a path to the directory to be created.

If not provided, the page size and orientation is requested with an
interactive prompt. The page size may be one of:

    {', '.join(vp.PAGE_SIZES.keys())}

Alternatively, a custom size can be specified in the form of WIDTHxHEIGHT. WIDTH and
HEIGHT may include units. If only one has an unit, the other is assumed to have the
same unit. If none have units, both are assumed to be pixels by default. Here are some
examples:

\b
    --page-size 11x14in     # 11in by 14in
    --page-size 1024x768    # 1024px by 768px
    --page-size 13.5inx4cm  # 13.5in by 4cm

Portrait orientation is enforced, unless --landscape is used, in which case landscape
orientation is enforced.

By default, the new project is based on the official template located here:

    https://github.com/abey79/cookiecutter-vsketch-sketch

You can provide an alternative template address with the --template option.

Most options can use environment variables to set their default values. For example, the
default template can be set with the VSK_TEMPLATE variable and the default page size with the
VSK_PAGE_SIZE variable.
"""


@cli.command(help=INIT_HELP)
@click.argument("target")
@click.option(
    "--page-size",
    "-p",
    default="a4",
    prompt=True,
    metavar="PAGESIZE",
    envvar="VSK_PAGE_SIZE",
    show_default=True,
    help="Page size.",
)
@click.option(
    "--landscape",
    "-l",
    prompt=True,
    is_flag=True,
    envvar="VSK_LANDSCAPE",
    help="Use landscape orientation.",
)
@click.option(
    "--template",
    default="https://github.com/abey79/cookiecutter-vsketch-sketch.git",
    envvar="VSK_TEMPLATE",
    metavar="TEMPLATE",
    help="Project template.",
)
def init(target: str, page_size: str, landscape: bool, template: str) -> None:
    """Initialize a new sketch.

    TARGET is the name or path of the new sketch directory."""

    dir_path = pathlib.Path(target)

    with vsketch.working_directory(dir_path.parent):
        cookiecutter(
            template,
            no_input=True,
            extra_context={
                "sketch_name": dir_path.name,
                "page_size": page_size,
                "landscape": str(landscape),
            },
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
@click.argument(
    "target",
    type=click.Path(exists=True, path_type=pathlib.Path),
    required=False,
)
@click.option(
    "--editor",
    "-e",
    metavar="EDITOR",
    envvar="VSK_EDITOR",
    help="Use EDITOR to open the sketch source.",
)
@click.option(
    "--fullscreen",
    is_flag=True,
    envvar="VSK_FULLSCREEN",
    help="Display the viewer fullscreen on the second screen if available.",
)
@click.option(
    "--output-dir",
    envvar="VSK_OUTPUT_DIR",
    type=click.Path(path_type=pathlib.Path, file_okay=False, dir_okay=True),
    help="Directory to save liked plots. If not provided, defaults to a directory called 'output' next to the sketch source file.",
)
def run(
    target: Optional[pathlib.Path],
    editor: Optional[str],
    fullscreen: bool,
    output_dir: Optional[pathlib.Path],
) -> None:
    """Execute, display and monitor changes on a sketch.

    This command loads a sketch and opens an interactive viewer display the result. The viewer
    will refresh the display each time the sketch file is saved. If the sketch defines any
    parameters, they will be displayed by the viewer and may be interactively changed.

    TARGET may either point at a Python file or at a directory. If omitted, the current directory
    is assumed. When TARGET points at a directory, this command looks for a single Python file
    whose name starts with `sketch_`. If none are found, it will attempt to use a Python file named
    `sketch.py`. If no such file exists, it will look for a single Python file with arbitrary name.
    If no or multiple candidates are found, the command will fail.

    If the --editor option is provided or the VSK_EDITOR environment variable is set, the
    sketch file will be opened with the corresponding editor.

    If the --fullscreen option is provided or the VSK_FULLSCREEN environment variable is set,
    and a second screen is available, the viewer is opened in fullscreen on the second monitor.
    """
    try:
        path = _find_sketch_script(target)
    except ValueError as err:
        print_error("Sketch could not be found: ", str(err))
        raise click.Abort()

    print_info("Running sketch: ", str(path))

    if editor is not None and editor != "":
        os.system(f"{editor} {path}")

    show(path, output_dir, second_screen=fullscreen)


@dataclasses.dataclass()
class _ParamSpec:
    """Helper class to handle the various way to specify parameter.

    This would probably be better implemented as a click type.
    """

    name: str
    value_string: dataclasses.InitVar[str]
    values: List[Union[int, float, str]] = dataclasses.field(init=False)

    def __post_init__(self, value_string: str) -> None:
        if "," in value_string:
            if ".." in value_string:
                raise click.BadParameter(
                    f"parameter value '{value_string}' invalid, "
                    "ranges cannot be combined with list"
                )

            self.values = list(value_string.split(","))
        elif ".." in value_string:
            fields = value_string.split("..")
            if len(fields) not in {2, 3}:
                raise click.BadParameter(
                    f"parameter value '{value_string}' invalid, "
                    "ranges must have 2 or 3 components"
                )

            try:
                start = float(fields[0])
                end = float(fields[1])
                if len(fields) == 3:
                    stride = float(fields[2])
                else:
                    stride = 1
            except ValueError:
                raise click.BadParameter(
                    f"parameter value '{value_string}' invalid, ranges must be numbers"
                )

            if end < start:
                raise click.BadParameter(
                    f"parameter value '{value_string}' invalid, "
                    "END cannot be lower than START"
                )

            self.values = []
            while start <= end:
                self.values.append(start)
                start += stride
        else:
            self.values = [value_string]


@cli.command()
@click.argument(
    "target",
    type=click.Path(exists=True, path_type=pathlib.Path),
    required=False,
)
@click.option("--name", "-n", metavar="NAME", help="Output name (without extension).")
@click.option(
    "--config",
    "-c",
    metavar="CONFIG",
    help=(
        "Path to the config file to use (may be a path to JSON file or the name of the "
        "configuration)."
    ),
)
@click.option("--seed", "-s", metavar="[SEED|FIRST..LAST]", help="Seed or seed range to use.")
@click.option(
    "--param",
    "-p",
    "params",
    type=(str, str),
    multiple=True,
    metavar="PARAM [VALUE[,VALUE2,...]|FIRST..LAST|FIRST..LAST..INC]",
    help="Set a specific parameter.",
)
@click.option("--destination", "-d", metavar="DEST", help="Destination path.")
@click.option(
    "--multiprocessing",
    "-m",
    is_flag=True,
    envvar="VSK_MULTIPROCESSING",
    help="Enable multiprocessing.",
)
def save(
    target: Optional[pathlib.Path],
    name: Optional[str],
    config: Optional[str],
    seed: Optional[str],
    params: List[Tuple[str, str]],
    destination: Optional[str],
    multiprocessing: bool,
) -> None:
    """Save the sketch to an SVG file.

    TARGET may either point at a Python file or at a directory and is interpreted in the same
    way as the `vsk run` command (see `vsk run --help`).

    By default, the output is named after the sketch and the provided options. An alternative
    name may be provided with the --name option.

    If the sketch has parameters, their default values are used. Alternatively, a pre-existing
    configuration can be used instead with the --config option.

    The value of an individual parameter can be overridden using the --param option. The value
    for this option may take multiple forms:

        --param PARAM VALUE

            The parameter is set to VALUE.

        --param PARAM VAL1,VAL2,VAL3,...

            One output file will be generated for each of the provided value.

        --param PARAM START..END

            One output file will be generated for each values in the provided range (i.e.
    START, START+1, START+2,...,END).

        --param PARAM START..END..STRIDE

            One output file will be generated for each value in the range starting with START,
    then incremented by STRIDE, until it reaches END. The value END is included if, and only
    if, the difference between END and START is an integer multiple of STRIDE.

    If multiple instances of the --param option are used, a file will be generated for all
    possible combinations of values.

    By default, a random seed is used for vsketch's random number generator. If --config is
    used, the seed saved in the configuration is used instead. A seed may also be provided with
    the --seed option, in which case it will override the configuration's seed.

    The --seed option also accepts seed range in the form of FIRST..LAST, e.g. 0..100. In this
    case, one output file per seed is generated.

    If the number of files to generate is greater than 4, all available cores are used for the
    process. This behaviour can be disabled with --no-multiprocessing or the
    VSK_MULTIPROCESSING variable.

    By default, all SVG are saved in the sketch's "output" subdirectory. This can be
    overridden using the --destination option.
    """

    current_directory = pathlib.Path.cwd()

    try:
        path = _find_sketch_script(target)
    except ValueError as err:
        print_error("Sketch could not be found: ", str(err))
        raise click.Abort()

    # load configuration
    param_set: Dict[str, vsketch.ParamType] = {}
    config_postfix = ""
    cmd_line_config_ext = ""
    if config is not None:
        config_path = pathlib.Path(config)
        if not config_path.exists():
            config_path = get_config_path(path) / (config + ".json")

        if config_path.exists():
            param_set = load_config(config_path)
            config_postfix = "_" + config_path.stem
            cmd_line_config_ext = f"-c {config_path} "
        else:
            print_error("Config file not found: ", str(config_path))

    # prepare params
    param_specs = [_ParamSpec(name, value) for name, value in params]

    # compute name
    if name is None:
        name = canonical_name(path) + config_postfix
    seed_in_name = seed is not None

    # prepare seed
    if seed is None:
        if param_set is not None and "__seed__" in param_set:
            seed_start = seed_end = int(param_set["__seed__"])
        else:
            seed_start = seed_end = random.randint(0, 2**31 - 1)
    else:
        try:
            seed_start, seed_end = _parse_seed(seed)
        except ValueError as err:
            print_error(f"Could not parse seed {seed}: ", str(err))
            raise click.Abort()

    # prepare output path
    if destination is not None:
        output_path = pathlib.Path(destination)
        if not output_path.exists():
            print_error("Provided output path does not exist: ", str(output_path.absolute()))
            raise click.Abort()
        if not output_path.is_dir():
            print_error(
                "Provided output path is not a directory: ", str(output_path.absolute())
            )
            raise click.Abort()
    else:
        output_path = path.parent / "output"
        if not output_path.exists():
            output_path.mkdir()
        elif not output_path.is_dir():
            print_error("Could not create output directory: ", str(output_path))
            raise click.Abort()

    # noinspection PyShadowingNames
    def _write_output(seed_and_params: Tuple) -> None:
        seed, *param_values = seed_and_params

        # this needs to be there because the sketch class cannot be pickled apparently
        sketch_class = load_sketch_class(path)
        if sketch_class is None:
            print_error("Could not load script: ", str(path))
            raise click.Abort()

        sketch_class.set_param_set(param_set)

        # apply parameters
        sketch_params = sketch_class.get_params()
        param_name_ext = ""
        cmd_line_param_ext = ""
        for spec, value in zip(param_specs, param_values):
            if spec.name not in sketch_params:
                raise click.BadParameter(f"parameter '{spec.name}' not found in sketch")
            success = sketch_params[spec.name].set_value_with_validation(value)
            if not success:
                raise click.BadParameter(
                    f"value '{value}' incompatible with parameter '{spec.name}'"
                )
            param_name_ext += "_" + spec.name + "_" + str(sketch_params[spec.name].value)
            cmd_line_param_ext += f"-p {spec.name} {str(sketch_params[spec.name].value)} "

        output_name = cast(str, name)
        output_name += param_name_ext
        if seed_in_name:
            output_name += "_s" + str(seed)
        output_name += ".svg"

        output_file = output_path / output_name

        sketch = sketch_class.execute(finalize=True, seed=seed)

        if sketch is None:
            print_error("Could not execute script: ", str(path))
            raise click.Abort()

        doc = sketch.vsk.document
        with open(output_file, "w") as fp:
            try:
                path_to_print = str(output_file.relative_to(current_directory))
            except ValueError:
                path_to_print = str(output_file)
            print_info("Exporting SVG: ", path_to_print)
            source_string = (
                f"vsk save -s {seed} {cmd_line_config_ext}{cmd_line_param_ext}{path}"
            )
            vp.write_svg(
                fp,
                doc,
                source_string=source_string,
                use_svg_metadata=True,
            )

    all_output_iterator = itertools.product(
        range(seed_start, seed_end + 1), *[spec.values for spec in param_specs]
    )

    if not multiprocessing:
        for seed_and_params in all_output_iterator:
            _write_output(seed_and_params)
    else:
        with Pool() as p:
            list(p.imap(_write_output, all_output_iterator))


if __name__ == "__main__":
    save(target="examples/simple_sketch", name=None, seed="0", multiprocessing=True)
