from setuptools import setup

with open("README.rst") as f:
    readme = f.read()

with open("LICENSE") as f:
    license_file = f.read()

setup(
    name="vsketch",
    version="0.1.0",
    description="Plotter generative art environment",
    long_description=readme,
    long_description_content_type="text/x-rst",
    author="Antoine Beyeler",
    url="https://github.com/abey79/vsketch",
    license=license_file,
    packages=["vsketch"],
    install_requires=[
        "numpy",
        "matplotlib",
        "vpype @ git+https://github.com/abey79/vpype",
        "shapely[vectorized]",
    ],
    extras_require={
        "colab": ["requests"],
        "jupyterlab": [
            "jupyterlab",
            "jupyter_nbextensions_configurator",
            "jupyterlab_code_formatter",
            "ipympl",
            "black",
            "isort",
        ],
    },
)
