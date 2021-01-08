from typing import List

from dearpygui import core, simple

import vsketch


class GUI:
    def __init__(self):
        self.series: List[str] = []

        with simple.window("main", width=600, height=600):
            core.add_plot(
                "Plot",
                no_legend=True,
                yaxis_invert=True,
                anti_aliased=True,
                crosshairs=True,
                equal_aspects=True,
            )

        core.set_primary_window("main", True)

        def redraw(sender, data):
            core.render_dearpygui_frame()

        def post_init(sender, data):
            core.set_resize_callback(redraw)

        core.set_start_callback(post_init)

    # noinspection PyMethodMayBeStatic
    def run(self) -> None:
        core.start_dearpygui()

    def refresh_plot(self, vsk: vsketch.Vsketch) -> None:
        for i, line in enumerate(lc):
            series_id = f"##{i}"
            self.series.append(series_id)
            core.add_line_series(
                "Plot",
                series_id,
                line.real.tolist(),
                line.imag.tolist(),
                color=[255, 255, 255],
            )

        core.add_shade_series(
            "Plot",
            "##shade",
            x=[BORDER, width, width, width + BORDER],
            y1=[height, height, BORDER, BORDER],
            y2=[height + BORDER, height + BORDER, height + BORDER, height + BORDER],
            fill=[128, 0, 128],
        )
        self.series.append("##shade")

        core.add_line_series(
            "Plot",
            "##frame",
            [0, 0, width, width, 0],
            [0, height, height, 0, 0],
            color=[128, 0, 128],
        )

        self.series.append("##frame")
