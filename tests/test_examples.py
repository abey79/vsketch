import pathlib

import nbformat
import pytest
from click.testing import CliRunner
from nbconvert.preprocessors import ExecutePreprocessor
from vsketch_cli.cli import cli

EXAMPLES = pathlib.Path(__file__).parent.parent.absolute() / "examples"
NOTEBOOKS = EXAMPLES / "_notebooks"

runner = CliRunner()


@pytest.mark.slow
@pytest.mark.parametrize("ipynb", NOTEBOOKS.glob("*.ipynb"))
def test_example_notebooks(tmp_path, ipynb):
    with open(ipynb) as f:
        nb = nbformat.read(f, as_version=4)
    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    ep.preprocess(nb, {"metadata": {"path": tmp_path}})


@pytest.mark.parametrize("path", EXAMPLES.glob("[!._]*[!.md]"))
def test_examples(tmp_path, path):
    # Note: split is needed to avoid `invoke`'s preprocessor to eat Windows' path backslashes
    res = runner.invoke(
        cli, f"save --name test_output --destination {tmp_path} {str(path)}".split()
    )
    assert res.exit_code == 0
    assert (pathlib.Path(tmp_path) / "test_output.svg").exists()
