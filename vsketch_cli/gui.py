import math

import vpype as vp
from dearpygui.core import *
from dearpygui.simple import *

BORDER = 5

origin = [0, 0]
scale = [1, 1]

filename = "/Users/hhip/Desktop/TEST_SVG/spirograph-grid-cropped-a3.svg"

lc, width, height = vp.read_svg(filename, 1, return_size=True)
print(width)
print(height)

with window("Tutorial", no_scrollbar=True):
    add_drawing(
        "Drawing_1",
        width=BORDER * 2 + math.ceil(width),
        height=BORDER * 2 + math.ceil(height),
    )

lc.translate(BORDER, BORDER)
for line in lc:
    draw_polyline("Drawing_1", vp.as_vector(line).tolist(), [255, 255, 255])

draw_polyline(
    "Drawing_1",
    [
        [BORDER, BORDER],
        [width + BORDER, BORDER],
        [width + BORDER, height + BORDER],
        [BORDER, height + BORDER],
    ],
    closed=True,
    color=[128, 0, 128],
)

with window("Plot Window"):
    add_plot("Plot", no_legend=True, yaxis_invert=True, anti_aliased=True, crosshairs=True)

for i, line in enumerate(lc):
    add_line_series("Plot", f"##{i}", vp.as_vector(line).tolist(), color=[255, 255, 255])

add_line_series(
    "Plot",
    "BORDER",
    [
        [BORDER, BORDER],
        [width + BORDER, BORDER],
        [width + BORDER, height + BORDER],
        [BORDER, height + BORDER],
        [BORDER, BORDER],
    ],
    color=[128, 0, 128],
)


def drag_callback(sender, data):
    print(sender, get_mouse_pos(local=True))
    if sender == "Tutorial":
        origin[0] += data[1]
        origin[1] -= data[2]
        set_drawing_origin("Drawing_1", *origin)


def mouse_wheel_callback(sender, data):
    print(sender, data)


show_debug()

set_mouse_drag_callback(drag_callback, 10)
# set_mouse_wheel_callback(mouse_wheel_callback)

start_dearpygui()
