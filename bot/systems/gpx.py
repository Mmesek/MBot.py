import time

import gpxpy
import httpx
from MFramework import Bot, Embed, Message, Message_Reference, onDispatch, Attachment, Embed_Image
from .gpx_map import map


@onDispatch(predicate=lambda x: x.attachments and x.guild_id == 463433273620824104)
async def message_create(bot: Bot, data: Message):
    if not any(a.filename.endswith("gpx") for a in data.attachments):
        return
    s = time.time()
    embeds = []
    attachments = []
    files = []
    for attachment in data.attachments:
        if attachment.filename.endswith("gpx"):
            async with httpx.AsyncClient() as client:
                r = await client.get(attachment.url)
            gpx = gpxpy.parse(r.content)
            gpx.smooth(True, True, True)
            gpx.smooth()
            m = gpx.get_moving_data()
            avg_speed = m.moving_distance / m.moving_time

            embeds.append(
                Embed(
                    title=attachment.filename,
                    timestamp=gpx.time,
                    url=attachment.url,
                    image=Embed_Image(f"attachment://{attachment.filename}.png"),
                )
                .add_field("Duratioin", f"{m.moving_time / 60:.2f} m", True)
                .add_field("Distance", f"{m.moving_distance / 1000:.2f}km", True)
                .add_field("Speed m/s (Avg/Best)", f"{avg_speed:.2f}/{m.max_speed:.2f} m/s", True)
                .add_field(
                    "Tempo min/km (Avg/Best)",
                    f"{1000 / (avg_speed * 60):.2f}/{1000 / (m.max_speed * 60):.2f}",
                    True,
                )
            )
            files.append(gpx)
    attachments.append(Attachment(filename=f"{attachment.filename}.png", file=await map(*files)))
    e = time.time()
    await bot.create_message(
        data.channel_id,
        f"Processed in {(e - s):.2}s",
        embeds=embeds,
        attachments=attachments,
        message_reference=Message_Reference(data.id),
    )
