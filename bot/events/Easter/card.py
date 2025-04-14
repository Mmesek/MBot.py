from textwrap import wrap

from MFramework import Attachment, Context, Event, register
from mlib.colors import buffered_image
from PIL import Image, ImageDraw, ImageFont

import json
import random

with open("data/easter_postcard.json", "r") as file:
    TEXTS = json.load(file)


@register()
@Event(month=4)
async def happyeaster(ctx: Context):
    """Search for new matches"""
    img = Image.open("data/images/easter_postcard.jpg")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(
        "data/fonts/BarlowCondensed-Regular.ttf", size=65)
    text = random.choice(TEXTS)["message"]

    nick = ctx.member.nick or ctx.user.global_name or ctx.user.username
    captions = wrap(text.format(username=nick.title()), 50)
    height, pad = 60, 70
    for line in captions:
        width = draw.textlength(line, font)
        draw.text(
            ((img.size.width - width) / 2, height),
            line,
            fill=(0, 0, 0),
            font=font,
            align="center",
        )
        height += pad
        # NOTE: Not ideal as it doesn't take dynamic font's height
        # https://pillow.readthedocs.io/en/stable/deprecations.html#font-size-and-offset-methods

    img_str = buffered_image(img)
    attachment = Attachment(file=img_str, filename=f"{nick}_easter_card.jpg")

    await ctx.reply(
        f"{nick.title()} wishes you all a happy easter!", embeds=[], attachments=[attachment], components=[]
    )
