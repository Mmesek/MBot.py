from io import BytesIO

import aiohttp


async def layer_picture(url: str, layer_filename: str, x_offset: int = -400, y_offset: int = 0) -> bytes:
    from PIL import Image

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            fd = await response.read()

    img = Image.open(BytesIO(fd))
    layer = Image.open("data/" + layer_filename)
    img.paste(
        layer,
        (img.width + x_offset if x_offset < 0 else x_offset, img.height + y_offset if y_offset < 0 else y_offset),
        layer,
    )
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()
