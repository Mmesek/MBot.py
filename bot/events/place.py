import numpy as np
import matplotlib.pyplot as plt
import json
import os
from io import BytesIO

from MFramework.commands.cooldowns import CacheCooldown, cooldown
from MFramework import Attachment, Groups, register

# Canvas Size
CANVAS_WIDTH = 300
CANVAS_HEIGHT = 300
BORDER_SIZE = 5
# Default zoom when using the show command, will show a 50x50 pixel image
DEFAULT_ZOOM_SIZE = 50
#Path to canvas.json file
canvas_file = "data/canvas.json"



# color codes, list is expandable
COLOR_CODES = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "magenta": (255, 0, 255),
    "cyan": (0, 255, 255),
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "gray": (128, 128, 128),
    "maroon": (128, 0, 0),
    "olive": (128, 128, 0),
    "navy": (0, 0, 128),
    "purple": (128, 0, 128),
    "teal": (0, 128, 128),
    "lime": (0, 128, 0),
    "aqua": (0, 255, 255),
    "silver": (192, 192, 192),
    "fuchsia": (255, 0, 255),
    "orange": (255, 165, 0),
    "pink": (255, 192, 203),
    "gold": (255, 215, 0),
    "brown": (165, 42, 42),
    "indigo": (75, 0, 130),
    "violet": (238, 130, 238),
    "turquoise": (64, 224, 208),
    "coral": (255, 127, 80),
    "khaki": (240, 230, 140),
    "plum": (221, 160, 221),
    "salmon": (250, 128, 114),
    "orchid": (218, 112, 214),
    "tan": (210, 180, 140),
}

canvas = np.zeros((CANVAS_HEIGHT, CANVAS_WIDTH, 3), dtype=np.uint8)


def display_canvas(canvas):
    plt.figure(figsize=(CANVAS_WIDTH / 100, CANVAS_HEIGHT / 100), dpi=100)
    plt.imshow(canvas)
    plt.axis("off")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    buffered = BytesIO()
    plt.savefig(buffered, bbox_inches='tight', pad_inches=0)
    return buffered.getvalue()


def save_canvas():
    with open(canvas_file, "w") as f:
        json.dump(canvas.tolist(), f)


def load_canvas():
    global canvas
    try:
        if os.path.isfile(canvas_file):
            with open(canvas_file, "r") as f:
                canvas = np.array(json.load(f))
                canvas = np.asarray(canvas, dtype=np.uint8)
        else:
            print("Canvas file not found. Creating a new canvas.")
    except Exception as e:
        print(f"An error occurred while loading the canvas: {e}")


load_canvas()


@register(group=Groups.GLOBAL)
async def show(x: int = None, y: int = None, size: int = DEFAULT_ZOOM_SIZE):
    """ "
    Show the canvas or a zoomed-in portion of the canvas.
    Params
    ------
     x:
        The x coordinate of the center of the zoomed-in area (optional).
     y:
        The y coordinate of the center of the zoomed-in area (optional).
     size:
        The size of the zoomed-in area (optional). Defaults to 50.

    Example
    -------
        /show
        /show 10 20
        /show 10 20 5
    """
    if x is None or y is None:
        image = canvas
    else:
        x1 = max(0, x - size // 2)
        x2 = min(CANVAS_WIDTH, x + size // 2)
        y1 = max(0, y - size // 2)
        y2 = min(CANVAS_HEIGHT, y + size // 2)
        image = canvas[y1:y2, x1:x2]

    var = display_canvas(image)
    return Attachment(file=var, filename="data/canvas.png")


@register(group=Groups.GLOBAL)
@cooldown(minutes=1, logic=CacheCooldown)
async def place(x: int, y: int, color_code: str):
    """
    Place a pixel on the canvas at the specified coordinates with the specified color.
    Params
    ------
    x:
        The x coordinate of the pixel.
    y:
        The y coordinate of the pixel.
    color_code:
        The color code representing the desired color.
     Example
     -------
        /place 10 20 red
    """
    if 0 <= x < CANVAS_WIDTH and 0 <= y < CANVAS_HEIGHT:
        color_code = color_code.lower()
        if color_code in COLOR_CODES:
            r, g, b = COLOR_CODES[color_code]
            canvas[y, x] = (r, g, b)
            save_canvas()
            return f"Pixel placed at ({x}, {y}) with color {color_code}"
        else:
            return "Invalid color code! Use the `colorcodes` command to see the available color codes."
    else:
        return "Invalid coordinates!"


@register(group=Groups.GLOBAL, private_response=True)
async def colorcodes():
    """
    Show the list of all available colors
    """
    color_code_list = "\n".join(COLOR_CODES.keys())
    return f"Available color codes:\n```\n{color_code_list}```"