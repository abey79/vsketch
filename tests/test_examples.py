import pathlib

import pytest
from click.testing import CliRunner

from vsketch_cli.cli import cli

EXAMPLES = pathlib.Path(__file__).parent.parent.absolute() / "examples"

runner = CliRunner()


@pytest.mark.parametrize("path", EXAMPLES.glob("[!._]*[!.md]"))
def test_examples(tmp_path, path):
    # Note: split is needed to avoid `invoke`'s preprocessor to eat Windows' path backslashes
    res = runner.invoke(
        cli, f"save --name test_output --destination {tmp_path} {str(path)}".split()
    )
    assert res.exit_code == 0
    assert (pathlib.Path(tmp_path) / "test_output.svg").exists()
