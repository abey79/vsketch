"""This files tests the example notebooks.

Since notebooks are no longer explicitly supported, this file is  excluded from pytest's
configuration in pyproject.toml."""

import nbformat
import pytest
from nbconvert.preprocessors import ExecutePreprocessor

from .test_examples import EXAMPLES

NOTEBOOKS = EXAMPLES / "_notebooks"


@pytest.mark.slow
@pytest.mark.parametrize("ipynb", NOTEBOOKS.glob("*.ipynb"))
def test_example_notebooks(tmp_path, ipynb):
    with open(ipynb) as f:
        nb = nbformat.read(f, as_version=4)
    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    ep.preprocess(nb, {"metadata": {"path": tmp_path}})
