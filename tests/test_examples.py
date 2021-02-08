import glob
import pathlib

import nbformat
import pytest
from nbconvert.preprocessors import ExecutePreprocessor

EXAMPLES = str(pathlib.Path(__file__).parent.parent.absolute()) + "/examples/_notebooks/"


@pytest.mark.slow
@pytest.mark.parametrize("ipynb", glob.glob(EXAMPLES + "*.ipynb"))
def test_example_detail(tmp_path, ipynb):
    with open(ipynb) as f:
        nb = nbformat.read(f, as_version=4)
    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    ep.preprocess(nb, {"metadata": {"path": tmp_path}})
