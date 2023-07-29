# *vsketch*

![python](https://img.shields.io/github/languages/top/abey79/vsketch)
![Test](https://img.shields.io/github/actions/workflow/status/abey79/vsketch/python-lint-tests.yml?logo=github)
[![Documentation Status](https://img.shields.io/readthedocs/vsketch?label=Read%20the%20Docs&logo=read-the-docs)](https://vsketch.readthedocs.io/en/latest/?badge=latest)


## What is _vsketch_?

_vsketch_ is a Python generative art toolkit for plotters with the following focuses:

* **Accessibility**: _vsketch_ is easy to learn and feels familiar thanks to its API strongly inspired from [Processing](https://processing.org).
* **Minimized friction**: _vsketch_ automates every part of the creation process
      (project initialisation, friction-less iteration, export to plotter-ready files) through a CLI tool called `vsk`
      and a tight integration with [_vpype_](https://github.com/abey79/vpype/).
* **Plotter-centric**: _vsketch_ is made for plotter users, by plotter users. It's feature set is focused on the
      peculiarities of this medium and doesn't aim to solve other problems.
* **Interoperability**: _vsketch_ plays nice with popular packages such as [Numpy](https://numpy.org) and
      [Shapely](https://shapely.readthedocs.io/en/latest/), which are true enabler for plotter generative art.

_vsketch_ is the sum of two things:

* A CLI tool named `vsk` to automate every part of a sketch project lifecycle::
    * Sketch creation based on a customizable template.
    * Interactive rendering of your sketch with live-reload and custom parameters.
    * Batch export to SVG with random seed and configuration management as well as multiprocessing support.
* An easy-to-learn API similar to [Processing](https://processing.org) to implement your sketches.

*This project is at an early the stage and needs [contributions](https://vsketch.readthedocs.io/en/latest/contributing.html).
You can help by providing feedback and improving the documentation.*


## Installing *vsketch*

The recommended way to install *vsketch* is as a stand-alone installation using pipx:

```bash
$ pipx install vsketch
```

To run the examples, they must be [downloaded](https://github.com/abey79/vsketch/archive/refs/heads/master.zip) separately. After decompressing the archive, they can be run using the following command:

```bash
$ vsk run path/to/vsketch-master/examples/schotter
```

Check the [installation instructions](https://vsketch.readthedocs.io/en/latest/install.html) for more details.


## Getting started

This section is meant as a quick introduction of the workflow supported by _vsketch_. Check the
[documentation](https://vsketch.readthedocs.io/en/latest/) for a more complete overview.

Open a terminal and create a new project:

```bash
$ vsk init my_project
```

This will create a new project structure that includes everything you need to get started:

```bash
$ ls my_project
config
output
sketch_my_project.py
```

The `sketch_my_project.py` file contains a skeleton for your sketch. The `config` and `output` sub-directories are used
by `vsk` to store configurations and output SVGs.

Open `sketch_my_project.py` in your favourite editor and modify it as follows:

```python
import vsketch

class SchotterSketch(vsketch.SketchClass):
    def draw(self, vsk: vsketch.SketchClass) -> None:
        vsk.size("a4", landscape=False)
        vsk.scale("cm")

        for j in range(22):
            with vsk.pushMatrix():
                for i in range(12):
                    with vsk.pushMatrix():
                        vsk.rotate(0.03 * vsk.random(-j, j))
                        vsk.translate(
                            0.01 * vsk.randomGaussian() * j,
                            0.01 * vsk.randomGaussian() * j,
                        )
                        vsk.rect(0, 0, 1, 1)
                    vsk.translate(1, 0)
            vsk.translate(0, 1)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")

if __name__ == "__main__":
    SchotterSketch.display()

```

Your sketch is now ready to be run with the following command:

```bash
$ vsk run my_project
```

You should see this:

<img width="600" alt="image" src="https://user-images.githubusercontent.com/49431240/107370067-cd08ef00-6ae2-11eb-834a-72baf8c112e3.png">

Congratulation, you just reproduced [Georg Nees' famous artwork](http://www.medienkunstnetz.de/works/schotter/)!

Wouldn't be nice if you could interactively interact with the script's parameters? Let's make this happen.

Add the following declaration at the top of the class:

```python
class SchotterSketch(vsketch.SketchClass):
    columns = vsketch.Param(12)
    rows = vsketch.Param(22)
    fuzziness = vsketch.Param(1.0)
    
    # ...
```

Change the `draw()` method as follows:

```python
    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=False)
        vsk.scale("cm")

        for j in range(self.rows):
            with vsk.pushMatrix():
                for i in range(self.columns):
                    with vsk.pushMatrix():
                        vsk.rotate(self.fuzziness * 0.03 * vsk.random(-j, j))
                        vsk.translate(
                            self.fuzziness * 0.01 * vsk.randomGaussian() * j,
                            self.fuzziness * 0.01 * vsk.randomGaussian() * j,
                        )
                        vsk.rect(0, 0, 1, 1)
                    vsk.translate(1, 0)
            vsk.translate(0, 1)
```

Hit `ctrl-S`/`cmd-S` to save and, lo and behold, corresponding buttons just appeared in the viewer without even needing to restart it! Here is how it looks with some more fuzziness:

<img width="600" alt="image" src="https://user-images.githubusercontent.com/49431240/107372262-84066a00-6ae5-11eb-8d0f-fb6d4291cb51.png">

Let's play a bit with the parameters until we find a combination we like, then hit the _Save_ button and enter a "Best config" as name.

<img width="200" alt="image" src="https://user-images.githubusercontent.com/49431240/107372905-39d1b880-6ae6-11eb-8a73-5f8d01cac0a9.png">

We just saved a configuration that we can load at any time.

Finally, being extremely picky, it would be nice to be able to generate ONE HUNDRED versions of this sketch with various random seeds, in hope to find the most perfect version for plotting and framing. `vsk` will do this for you, using all CPU cores available:

```bash
$ vsk save --config "Best config" --seed 0..99 my_project
```

You'll find all the SVG file in the project's `output` subdirectory:

<img width="600" alt="image" src="https://user-images.githubusercontent.com/49431240/107375111-abab0180-6ae8-11eb-8034-d84c9d400ab2.png">

Next steps:
* Use `vsk` integrated help to learn about the all the possibilities (`vsk --help`).
* Learn the vsketch API on the documentation's [overview](https://vsketch.readthedocs.io/en/latest/overview.html) and [reference](https://vsketch.readthedocs.io/en/latest/reference.html) pages.


## Acknowledgments

Part of this project's documentation is inspired by or copied from the  [Processing project](https://processing.org).


## License

This project is licensed under the MIT license. The documentation is licensed under the
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) license. See the
[documentation](https://vsketch.readthedocs.io/en/latest/license.html) for details.
