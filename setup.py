from setuptools import setup


with open("README.md") as f:
    readme = f.read()

with open("LICENSE") as f:
    license = f.read()

setup(
    name="vsketch",
    version="0.1.0",
    description="Plotter generative art environment",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Antoine Beyeler",
    url="https://github.com/abey79/vsketch",
    license=license,
    packages=["vsketch"],
    install_requires=[],
)
