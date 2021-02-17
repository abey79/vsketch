"""Quick draw dataset

Example contributed by Blair Morrison (https://github.com/blrm) and adapted by Antoine Beyeler
"""

import pathlib
import random
import struct
import urllib.request
from itertools import islice

import vpype as vp
from shapely.geometry import MultiLineString

import vsketch

quick_draw_categories = (
    "aircraft carrier",
    "airplane",
    "alarm clock",
    "ambulance",
    "angel",
    "animal migration",
    "ant",
    "anvil",
    "apple",
    "arm",
    "asparagus",
    "axe",
    "backpack",
    "banana",
    "bandage",
    "barn",
    "baseball",
    "baseball bat",
    "basket",
    "basketball",
    "bat",
    "bathtub",
    "beach",
    "bear",
    "beard",
    "bed",
    "bee",
    "belt",
    "bench",
    "bicycle",
    "binoculars",
    "bird",
    "birthday cake",
    "blackberry",
    "blueberry",
    "book",
    "boomerang",
    "bottlecap",
    "bowtie",
    "bracelet",
    "brain",
    "bread",
    "bridge",
    "broccoli",
    "broom",
    "bucket",
    "bulldozer",
    "bus",
    "bush",
    "butterfly",
    "cactus",
    "cake",
    "calculator",
    "calendar",
    "camel",
    "camera",
    "camouflage",
    "campfire",
    "candle",
    "cannon",
    "canoe",
    "car",
    "carrot",
    "castle",
    "cat",
    "ceiling fan",
    "cello",
    "cell phone",
    "chair",
    "chandelier",
    "church",
    "circle",
    "clarinet",
    "clock",
    "cloud",
    "coffee cup",
    "compass",
    "computer",
    "cookie",
    "cooler",
    "couch",
    "cow",
    "crab",
    "crayon",
    "crocodile",
    "crown",
    "cruise ship",
    "cup",
    "diamond",
    "dishwasher",
    "diving board",
    "dog",
    "dolphin",
    "donut",
    "door",
    "dragon",
    "dresser",
    "drill",
    "drums",
    "duck",
    "dumbbell",
    "ear",
    "elbow",
    "elephant",
    "envelope",
    "eraser",
    "eye",
    "eyeglasses",
    "face",
    "fan",
    "feather",
    "fence",
    "finger",
    "fire hydrant",
    "fireplace",
    "firetruck",
    "fish",
    "flamingo",
    "flashlight",
    "flip flops",
    "floor lamp",
    "flower",
    "flying saucer",
    "foot",
    "fork",
    "frog",
    "frying pan",
    "garden",
    "garden hose",
    "giraffe",
    "goatee",
    "golf club",
    "grapes",
    "grass",
    "guitar",
    "hamburger",
    "hammer",
    "hand",
    "harp",
    "hat",
    "headphones",
    "hedgehog",
    "helicopter",
    "helmet",
    "hexagon",
    "hockey puck",
    "hockey stick",
    "horse",
    "hospital",
    "hot air balloon",
    "hot dog",
    "hot tub",
    "hourglass",
    "house",
    "house plant",
    "hurricane",
    "ice cream",
    "jacket",
    "jail",
    "kangaroo",
    "key",
    "keyboard",
    "knee",
    "knife",
    "ladder",
    "lantern",
    "laptop",
    "leaf",
    "leg",
    "light bulb",
    "lighter",
    "lighthouse",
    "lightning",
    "line",
    "lion",
    "lipstick",
    "lobster",
    "lollipop",
    "mailbox",
    "map",
    "marker",
    "matches",
    "megaphone",
    "mermaid",
    "microphone",
    "microwave",
    "monkey",
    "moon",
    "mosquito",
    "motorbike",
    "mountain",
    "mouse",
    "moustache",
    "mouth",
    "mug",
    "mushroom",
    "nail",
    "necklace",
    "nose",
    "ocean",
    "octagon",
    "octopus",
    "onion",
    "oven",
    "owl",
    "paintbrush",
    "paint can",
    "palm tree",
    "panda",
    "pants",
    "paper clip",
    "parachute",
    "parrot",
    "passport",
    "peanut",
    "pear",
    "peas",
    "pencil",
    "penguin",
    "piano",
    "pickup truck",
    "picture frame",
    "pig",
    "pillow",
    "pineapple",
    "pizza",
    "pliers",
    "police car",
    "pond",
    "pool",
    "popsicle",
    "postcard",
    "potato",
    "power outlet",
    "purse",
    "rabbit",
    "raccoon",
    "radio",
    "rain",
    "rainbow",
    "rake",
    "remote control",
    "rhinoceros",
    "rifle",
    "river",
    "roller coaster",
    "rollerskates",
    "sailboat",
    "sandwich",
    "saw",
    "saxophone",
    "school bus",
    "scissors",
    "scorpion",
    "screwdriver",
    "sea turtle",
    "see saw",
    "shark",
    "sheep",
    "shoe",
    "shorts",
    "shovel",
    "sink",
    "skateboard",
    "skull",
    "skyscraper",
    "sleeping bag",
    "smiley face",
    "snail",
    "snake",
    "snorkel",
    "snowflake",
    "snowman",
    "soccer ball",
    "sock",
    "speedboat",
    "spider",
    "spoon",
    "spreadsheet",
    "square",
    "squiggle",
    "squirrel",
    "stairs",
    "star",
    "steak",
    "stereo",
    "stethoscope",
    "stitches",
    "stop sign",
    "stove",
    "strawberry",
    "streetlight",
    "string bean",
    "submarine",
    "suitcase",
    "sun",
    "swan",
    "sweater",
    "swing set",
    "sword",
    "syringe",
    "table",
    "teapot",
    "teddy-bear",
    "telephone",
    "television",
    "tennis racquet",
    "tent",
    "The Eiffel Tower",
    "The Great Wall of China",
    "The Mona Lisa",
    "tiger",
    "toaster",
    "toe",
    "toilet",
    "tooth",
    "toothbrush",
    "toothpaste",
    "tornado",
    "tractor",
    "traffic light",
    "train",
    "tree",
    "triangle",
    "trombone",
    "truck",
    "trumpet",
    "t-shirt",
    "umbrella",
    "underwear",
    "van",
    "vase",
    "violin",
    "washing machine",
    "watermelon",
    "waterslide",
    "whale",
    "wheel",
    "windmill",
    "wine bottle",
    "wine glass",
    "wristwatch",
    "yoga",
    "zebra",
    "zigzag",
)


def unpack_drawing(file_handle):
    (key_id,) = struct.unpack("Q", file_handle.read(8))
    (country_code,) = struct.unpack("2s", file_handle.read(2))
    (recognized,) = struct.unpack("b", file_handle.read(1))
    (timestamp,) = struct.unpack("I", file_handle.read(4))
    (n_strokes,) = struct.unpack("H", file_handle.read(2))
    image = []
    for i in range(n_strokes):
        (n_points,) = struct.unpack("H", file_handle.read(2))
        fmt = str(n_points) + "B"
        x = struct.unpack(fmt, file_handle.read(n_points))
        y = struct.unpack(fmt, file_handle.read(n_points))
        image.append((x, y))

    return {
        "key_id": key_id,
        "country_code": country_code,
        "recognized": recognized,
        "timestamp": timestamp,
        "image": image,
    }


def unpack_drawings(filename):
    with open(filename, "rb") as f:
        while True:
            try:
                yield unpack_drawing(f)
            except struct.error:
                break


def quickdraw_to_linestring(qd_image):
    """Returns a Shapely MultiLineString for the provided quickdraw image.
    This MultiLineString can be passed to vsketch
    """
    linestrings = []
    for i in range(0, len(qd_image["image"])):
        line = zip(qd_image["image"][i][0], qd_image["image"][i][1])
        linestrings.append(tuple(line))
    return MultiLineString(linestrings)


class QuickDrawSketch(vsketch.Vsketch):
    category = vsketch.Param("crab", choices=quick_draw_categories)
    page_size = vsketch.Param("a4", choices=vp.PAGE_SIZES.keys())
    landscape = vsketch.Param(False)
    margins = vsketch.Param(10, 0, unit="mm")
    layer_count = vsketch.Param(2, 1)
    columns = vsketch.Param(9, 1)
    rows = vsketch.Param(13, 1)
    scale_factor = vsketch.Param(3.0)

    def draw(self) -> None:
        self.size(self.page_size, landscape=self.landscape)
        self.penWidth("0.5mm")

        # obtain the datafile
        file_name = self.category + ".bin"
        file_path = pathlib.Path(file_name)
        url = "https://storage.googleapis.com/quickdraw_dataset/full/binary/"
        url += file_name.replace(" ", "%20")
        if not file_path.exists():
            urllib.request.urlretrieve(url, file_name)

        # extract some drawings
        drawing_set = unpack_drawings(file_name)
        drawing_subset = list(islice(drawing_set, 10000))

        # draw stuff

        width = self.width - 2 * self.margins
        height = self.height - 2 * self.margins

        n = self.columns * self.rows
        samples = random.sample(drawing_subset, n)
        for j in range(self.rows):
            with self.pushMatrix():
                for i in range(self.columns):
                    idx = j * self.columns + i
                    with self.pushMatrix():
                        self.scale(self.scale_factor * min(1 / self.columns, 1 / self.rows))
                        drawing = quickdraw_to_linestring(samples[idx])
                        self.stroke((idx % self.layer_count) + 1)
                        self.geometry(drawing)
                    self.translate(width / self.columns, 0)

            self.translate(0, height / self.rows)

    def finalize(self) -> None:
        self.vpype("linemerge linesort")


if __name__ == "__main__":
    vsk = QuickDrawSketch()
    vsk.draw()
    vsk.finalize()
    vsk.display()
