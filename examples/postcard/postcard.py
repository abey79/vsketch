"""Postcard mailing helper sketch

How to use:

1) Create the following files next to the sketch script:
-`addresses.txt`: all the addresses, separated by two new lines
- `header.txt`: header text
- `message.txt`: postcard message, may contain $FirstName$, which will be replaced as you
  expect

2) Run: `vsk run postcard`
"""

from pathlib import Path
from typing import List, Tuple

import vsketch

try:
    ADDRESSES = (Path(__file__).parent / "addresses.txt").read_text().split("\n\n")
except FileNotFoundError:
    ADDRESSES = ["John Doe\n123 Main St\nAnytown, USA"]

try:
    HEADER = (Path(__file__).parent / "header.txt").read_text()
except FileNotFoundError:
    HEADER = "Myself\nMy Place\nMy town, USA"


try:
    MESSAGE = (Path(__file__).parent / "message.txt").read_text()
except FileNotFoundError:
    MESSAGE = """
Dear $FirstName$,

Please enjoy this postcard!

Best,
Me
"""


class PostcardSketch(vsketch.SketchClass):
    addr_id = vsketch.Param(0, 0, len(ADDRESSES) - 1)
    address_only = vsketch.Param(False)

    address_font_size = vsketch.Param(0.7, decimals=1)
    address_line_spacing = vsketch.Param(1.2, decimals=1)
    address_y_offset = vsketch.Param(6.0, decimals=1)

    header_font_size = vsketch.Param(0.4, decimals=1)
    header_line_spacing = vsketch.Param(1.1, decimals=1)

    message_font_size = vsketch.Param(0.5, decimals=1)
    message_line_spacing = vsketch.Param(1.2, decimals=1)
    message_y_offset = vsketch.Param(3.0, decimals=1)

    @staticmethod
    def first_name(address: str) -> str:
        lines = address.splitlines()
        name_line = lines[0].split(" ")
        # deal with abbreviated first name
        if len(name_line) > 2 and len(name_line[1]) > len(name_line[0]):
            return name_line[1]
        else:
            return name_line[0]

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a6", landscape=True, center=False)
        vsk.scale("cm")

        address = ADDRESSES[self.addr_id]

        if not self.address_only:
            vsk.line(8, 0.5, 8, 10)
            vsk.rect(12.5, 0.5, 1.8, 2.2)
            vsk.text("STAMP", 12.5 + 1.8 / 2, 0.5 + 2.2 / 2, size=0.3, align="center")

            vsk.text(
                HEADER,
                0.5,
                0.8,
                width=7.0,
                size=self.header_font_size,
                line_spacing=self.header_line_spacing,
            )

            vsk.text(
                MESSAGE.replace("$FirstName$", self.first_name(address)),
                0.5,
                self.message_y_offset,
                width=7.0,
                size=self.message_font_size,
                line_spacing=self.message_line_spacing,
            )

        vsk.text(
            address,
            8.5,
            self.address_y_offset,
            width=5.8,
            size=self.address_font_size,
            line_spacing=self.address_line_spacing,
        )

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        pass


if __name__ == "__main__":
    PostcardSketch.display()
