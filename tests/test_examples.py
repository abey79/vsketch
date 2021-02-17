import glob
import pathlib

import nbformat
import pytest
from nbconvert.preprocessors import ExecutePreprocessor
from typer.testing import CliRunner
from vsketch_cli.cli import cli

EXAMPLES = str(pathlib.Path(__file__).parent.parent.absolute()) + "/examples/"
NOTEBOOKS = EXAMPLES + "_notebooks/"

runner = CliRunner()


@pytest.mark.slow
@pytest.mark.parametrize("ipynb", glob.glob(NOTEBOOKS + "*.ipynb"))
def test_example_notebooks(tmp_path, ipynb):
    with open(ipynb) as f:
        nb = nbformat.read(f, as_version=4)
    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    ep.preprocess(nb, {"metadata": {"path": tmp_path}})


@pytest.mark.parametrize("path", glob.glob(EXAMPLES + "[!_]*[!.md]"))
def test_examples(tmp_path, path):
    res = runner.invoke(cli, f"save --name test_output --destination {tmp_path} {path}")
    assert res.exit_code == 0
    assert (pathlib.Path(tmp_path) / "test_output.svg").exists()
