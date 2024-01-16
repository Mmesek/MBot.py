import asyncio
import enum

import sqlalchemy as sa
from MFramework import Context, Embed, Emoji, Groups, register
from mlib.database import Base, Timestamp


class Contest_Entries(Base):
    id = sa.Column(sa.BigInteger, primary_key=True)
    msg = sa.Column(sa.BigInteger)
    cc = sa.Column(sa.String)


class Contest_Entries2(Base):
    id = sa.Column(sa.BigInteger, primary_key=True)
    msg = sa.Column(sa.BigInteger)


class Contest_Entries3(Timestamp, Base):
    id = sa.Column(sa.BigInteger, primary_key=True)
    msg = sa.Column(sa.BigInteger)


from MFramework.commands.components import (
    Button,
    Button_Styles,
    Modal,
    Row,
    Text_Input_Styles,
    TextInput,
)
from MFramework.commands.decorators import EventBetween


@register(group=Groups.GLOBAL, guild=289739584546275339, private_response=True)
@EventBetween(after_month=7, after_day=3, before_month=7, before_day=13, before_hour=15)
async def horror(
    ctx: Context,
    entry: TextInput[50, 200] = "Your Entry",
) -> Modal:
    """
    Enter a contest!
    Params
    ------
    entry:
        2 sentences
    """
    embed = Embed().set_footer(ctx.user.username, ctx.user.get_avatar()).set_color("#990000").set_description(entry)

    session = ctx.db.sql.session()
    if _entry := session.query(Contest_Entries3).filter(Contest_Entries3.id == ctx.user_id).first():
        try:
            await ctx.bot.edit_message(1125772270258901044, _entry.msg, embeds=[embed])
            return "Entry Edited!"
        except:
            pass

    msg = await ctx.bot.create_message(1125772270258901044, embeds=[embed])
    session.merge(Contest_Entries3(id=ctx.user_id, msg=msg.id))
    session.commit()

    await msg.react("💀")
    return "Entry Confirmed!"


class EnterContest(Button):
    auto_deferred: bool = False

    @classmethod
    async def execute(cls, ctx: Context, data: str):
        return horror


class Button_Types(enum.Enum):
    Primary = Button_Styles.PRIMARY.name
    Secondary = Button_Styles.SECONDARY.name
    Success = Button_Styles.SUCCESS.name
    Danger = Button_Styles.DANGER.name


@register(group=Groups.MODERATOR, private_response=True, bot=572532846678376459)
async def entry_button(ctx: Context, label: str, style: Button_Types, emoji: str = None, text: str = None):
    """
    Create button that acts as contest entry
    Params
    ------
    label:
        Name of the button
    style:
        Style of button to use
    emoji:
        Emoji to put into the button
    text:
        Optional message before button
    """
    if emoji:
        emoji = emoji.strip("<>").split(":")
        if len(emoji) == 1:
            emoji.append(None)
        emoji = Emoji(id=emoji[-1], name=emoji[-2], animated="a" == emoji[0])
    await ctx.send(
        text,
        components=Row(EnterContest(label=label, emoji=emoji, style=Button_Styles.get(style.value))),
        channel_id=ctx.channel_id,
    )
    return "Message sent!"


@register(group=Groups.GLOBAL, guild=289739584546275339, auto_defer=False, private_response=True)
@EventBetween(after_month=3, after_day=28, before_month=5, before_day=5, before_hour=17)
async def msi(ctx: Context) -> str:
    """
    Participate in MSI contest
    """
    r = Msi(
        Row(
            TextInput(
                "URL",
                style=Text_Input_Styles.Short,
                min_length=1,
                max_length=200,
                required=True,
                placeholder="URL to a picture",
            )
        ),
        Row(
            TextInput(
                "URL 2",
                style=Text_Input_Styles.Short,
                min_length=1,
                max_length=200,
                required=False,
                placeholder="Optional URL to a second picture",
            )
        ),
        Row(
            TextInput(
                "URL 3",
                style=Text_Input_Styles.Short,
                min_length=1,
                max_length=200,
                required=False,
                placeholder="Optional URL to a third picture",
            )
        ),
        title="MSI Contest",
    )
    return r


class Msi(Modal):
    @classmethod
    async def execute(cls, ctx: Context, data: str, inputs: dict[str, str]):
        attachment = inputs.get("URL")
        attachment2 = inputs.get("URL 2")
        attachment3 = inputs.get("URL 3")

        if attachment and (
            not (attachment.endswith(".png") or attachment.endswith(".jpg") or attachment.endswith(".jpeg"))
            or not attachment.startswith("http")
        ):
            return "Your URL (1) should point directly to an image, not an album! Seems like your URL doesn't start with http or doesn't end with .png, .jpg or .jpeg"
        if attachment2 and (
            not (attachment2.endswith(".png") or attachment2.endswith(".jpg") or attachment2.endswith(".jpeg"))
            or not attachment2.startswith("http")
        ):
            return "Your URL (2) should point directly to an image, not an album! Seems like your URL doesn't start with http or doesn't end with .png, .jpg or .jpeg"
        if attachment3 and (
            not (attachment3.endswith(".png") or attachment3.endswith(".jpg") or attachment3.endswith(".jpeg"))
            or not attachment3.startswith("http")
        ):
            return "Your URL (3) should point directly to an image, not an album! Seems like your URL doesn't start with http or doesn't end with .png, .jpg or .jpeg"
        embeds = [
            Embed().setImage(attachment).setAuthor(str(ctx.user), icon_url=ctx.user.get_avatar()).setColor("#060606")
        ]
        if attachment2:
            embeds.append(Embed().setImage(attachment2).setColor("#ed1c24"))
        if attachment3:
            embeds.append(Embed().setImage(attachment3).setColor("#ed1c24"))
        session = ctx.db.sql.session()
        entry = Contest_Entries.filter(session, id=ctx.user_id).first()
        if entry:
            try:
                await ctx.bot.edit_message(957937620724371476, entry.msg, embeds=embeds)
                return "Entry Edited!"
            except:
                pass
        msg = await ctx.bot.create_message(957937620724371476, embeds=embeds)
        session.add(Contest_Entries(id=ctx.user_id, msg=msg.id))
        session.commit()
        return "Entry Confirmed!"


# @register(group=Groups.GLOBAL, guild=289739584546275339, private_response=True)
async def msi(ctx: Context, country: str, text: str = None, attachment: str = None, attachment2: str = None) -> str:
    """
    Participate in MSI contest
    Params
    ------
    country:
        Country where you live
    text:
        Contest Entry (Up to 500 words) Leave empty, you can fill it in next message
    attachment:
        DIRECT URL to a picture. Must end with either .png or .gif
    attachment2:
        DIRECT URL to a picture 2. Must end with either .png or .gif
    """
    import asyncio

    import pycountry

    try:
        _country = pycountry.countries.search_fuzzy(country)
    except:
        return "There was an error searching for provided country, make sure it's as close as possible to actual name and use the command again."
    if _country[0].name.lower() != country.lower():
        await ctx.reply(f"Most similiar Country: {_country[0].name}")
        await asyncio.sleep(5)
    session = ctx.db.sql.session()
    # if Contest_Entries.filter(session, id=ctx.user_id).all():
    #    return "You've already sent your entry!"
    if text and len(text.split(" ")) > 500:
        return "Sadly your entry is too long \=("
    if not text:
        await ctx.reply("Send your entry here (Up to 500 words)")
        try:
            msg = await ctx.bot.wait_for(
                "message_create",
                check=lambda x: x.channel_id == ctx.channel_id
                and x.content
                and len(x.content.split(" ")) <= 500
                and x.author.id == ctx.user_id,
                timeout=600,
            )
        except:
            return "Sadly you didn't respond in time! Use the command again!"
        await msg.delete()
        text = msg.content
    if attachment and (
        not (attachment.endswith(".png") or attachment.endswith(".jpg") or attachment.endswith(".jpeg"))
        or not attachment.startswith("http")
    ):
        return "Your URL should point directly to an image, not an album!"
    if attachment2 and (
        not (attachment2.endswith(".png") or attachment2.endswith(".jpg") or attachment2.endswith(".jpeg"))
        or not attachment2.startswith("http")
    ):
        return "Your URL should point directly to an image, not an album!"
    embeds = [
        Embed()
        .setDescription(text)
        .setImage(attachment)
        .setAuthor(str(ctx.user), icon_url=ctx.user.get_avatar())
        .setColor("#060606")
    ]
    if attachment2:
        embeds.append(Embed().setImage(attachment2).setColor("#ed1c24"))
    entry = Contest_Entries.filter(session, id=ctx.user_id).first()
    if entry:
        try:
            await ctx.bot.edit_message(934134541487050762, entry.msg, embeds=embeds)
            return "Entry Edited!"
        except:
            pass
    msg = await ctx.bot.create_message(934134541487050762, embeds=embeds)
    session.add(Contest_Entries(id=ctx.user_id, msg=msg.id, cc=_country[0].name))
    session.commit()
    return "Entry Confirmed!"


@register(group=Groups.SYSTEM, interaction=False)
async def msi_entries(ctx: Context, *, language):
    """
    Description to use with help command
    Params
    ------
    :
        description
    """
    msgs = [await ctx.bot.get_channel_message(934134541487050762, 940276323442655262)]
    for i in range(16):
        msgs.extend(await ctx.bot.get_channel_messages(934134541487050762, limit=100, before=msgs[-1].id))
        await asyncio.sleep(0.03)
    msgs.reverse()
    text = ""
    session = ctx.bot.db.sql.session()
    for msg in msgs:
        if msg.author.id != 572532846678376459:
            text += f"{msg.author} | {msg.author.id}" + "\n"
            text += msg.content + "\n"
            for attachment in msg.attachments:
                text += attachment.url + "\n"
        for embed in msg.embeds:
            if embed.author:
                ce = Contest_Entries.filter(session, msg=msg.id).first()
                if ce:
                    text += f"{embed.author.name} | {ce.id} [{ce.cc}]" + "\n"
            if embed.description:
                text += embed.description + "\n"
            if embed.image:
                text += embed.image.url + "\n"
        text += "\n---\n"
    with open("entries.txt", "w", newline="", encoding="utf-8") as file:
        file.write(text)


@register(group=Groups.SYSTEM, interaction=False)
async def msi_activity(ctx: Context, *, language):
    """
    Description to use with help command
    Params
    ------
    :
        description
    """
    msgs = [await ctx.bot.get_channel_message(934134541487050762, 940276323442655262)]
    for i in range(16):
        msgs.extend(await ctx.bot.get_channel_messages(934134541487050762, limit=100, before=msgs[-1].id))
        await asyncio.sleep(0.03)
    msgs.reverse()
    users = []
    session = ctx.bot.db.sql.session()
    for msg in msgs:
        if msg.author.id != 572532846678376459:
            users.append(msg.author.id)
        for embed in msg.embeds:
            if embed.author:
                ce = Contest_Entries.filter(session, msg=msg.id).first()
                if ce:
                    users.append(ce.id)
    from ..systems.xp import User_Experience

    new_xp = (
        session.query(User_Experience.user_id, User_Experience.value)
        .filter(User_Experience.server_id == ctx.guild_id, User_Experience.user_id.in_(users))
        .all()
    )

    old_exp = session.query(Statistic.user_id, Statistic.value).filter(Statistic.name == types.Statistic.Chat).all()
    rows = []
    for user in users:
        row = {"user_id": user, "old_exp": 0, "new_xp": 0}
        old = next(filter(lambda x: user == x[0], old_exp), None)
        new = next(filter(lambda x: user == x[0], new_xp), None)
        if old:
            row["old_exp"] = old[1]
        if new:
            row["new_xp"] = new[1]
        rows.append(row)
    import csv

    with open("entries.txt", "w", newline="", encoding="utf-8") as file:
        cw = csv.DictWriter(file, ["user_id", "old_exp", "new_xp"])
        cw.writeheader()
        cw.writerows(rows)


@register(group=Groups.SYSTEM, interaction=False)
async def clean_entries(ctx: Context):
    from MFramework import Channel

    channel = Channel(ctx.bot, 1125772270258901044)
    msgs = await channel.get_messages(limit=200)
    ids = [int(msg.id) for msg in msgs]
    session = ctx.db.sql.session()
    entries = session.query(Contest_Entries3.msg).filter(Contest_Entries3.msg.in_(ids)).all()
    entries = [int(i[0]) for i in entries]
    for _id in set(ids).difference(set(entries)):
        await ctx.bot.delete_message(1125772270258901044, _id)
        await asyncio.sleep(0.1)
