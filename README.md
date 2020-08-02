# vsketch

vsketch is plotter generative art toolkit based based on [vpype](https://github.com/abey79/vpype/) and suited
for use within Jupyter notebooks. Its API is loosely based on that of [Processing](https://processing.org).

*This project is at the stage of the very early concept/prototype.*

## Installation

```bash
git clone https://github.com/abey79/vsketch
cd vsketch
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
jupyter notebook  # [optional] to start the jupyter environment
```

## Example

```python
import vsketch

vsk = vsketch.Vsketch()

# by default, geometries go to layer 1
vsk.rect(10, 10, 5, 8)
vsk.rect(12, 8, 4, 5)

# destination layer can be changed
vsk.stroke(2)
vsk.circle(14, 8, 3)

# arbitrary vpype pipeline can be postpended 
vsk.pipeline("linemerge reloop linesort")

# plot the resulting graphics
vsk.plot()

# write the SVG
vsk.write("test.svg", "a4", center=True)
```


## Contributing

Pull-request are most welcome contributions. Actually, this project survival might very well depend on them :)


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
