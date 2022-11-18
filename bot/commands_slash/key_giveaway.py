import enum

import aiohttp
import sqlalchemy as sa
from MFramework import (
    Attachment,
    Bot,
    Context,
    Emoji,
    Groups,
    Message_Reaction_Add,
    Role,
    onDispatch,
    register,
)
from MFramework.commands.components import Button, Button_Styles, Row
from mlib.database import Base


class Dockets(Base):
    code = sa.Column(sa.String, primary_key=True)
    snippet = sa.Column(sa.String)
    user_id = sa.Column(sa.BigInteger, nullable=True, default=None)


# @onDispatch(event="message_reaction_add")
async def message_reaction_add(bot: Bot, data: Message_Reaction_Add):
    if data.guild_id != 289739584546275339:
        return
    r = await get(bot, data.user_id)
    try:
        dm = await bot.create_dm(data.user_id)
        await bot.create_message(dm.id, r)
    except Exception as ex:
        pass


@register(group=Groups.HELPER, bot=289739584546275339)
async def docket():
    pass


@register(group=Groups.ADMIN, main=docket, private_response=True, bot=289739584546275339)
async def get(ctx: Context, user_id: int):
    session = ctx.db.sql.session()
    entry: Dockets = (
        session.query(Dockets)
        .filter(sa.or_(Dockets.user_id == None, Dockets.user_id == user_id))
        .order_by(Dockets.user_id.asc(), sa.func.random())
        .first()
    )

    if not entry:
        return "Seems like there are no more available dockets =("
    if entry and entry.user_id == user_id:
        return f"You have already claimed your docket! {entry.code}"

    entry.user_id = user_id
    session.commit()

    if entry.snippet:
        return entry.snippet.format(code=entry.docket)
    return entry.code


@register(group=Groups.HELPER, main=docket, private_response=True, bot=289739584546275339)
async def add(ctx: Context, codes: Attachment, role: Role) -> str:
    """
    Add new codes to database
    Params
    ------
    codes:
        csv file with codes and snippets to add
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(codes.url) as response:
            file = await response.read()
    import csv
    from io import StringIO

    file = StringIO(file.decode())
    c = csv.reader(file)
    headers = next(c)
    session = ctx.db.sql.session()
    try:
        _ = [i.lower() for i in headers]
        index = _.index("code")
        snippet = _.index("snippet")
    except ValueError:
        index = 0
        snippet = 1
    i = 0
    for row in c:
        i += 1
        session.merge(Dockets(code=row[index].strip().upper(), snippet=row[snippet].strip().lower()))
    session.commit()
    return f"Added {i} row(s) successfully!"


@register(group=Groups.MODERATOR, main=docket, private_response=True, bot=289739584546275339)
async def retrieve(ctx: Context, docket: str) -> str:
    """
    Check who redeemed that docket
    Params
    ------
    docket:
        Docket to check
    """
    session = ctx.db.sql.session()
    entry = Dockets.filter(session, code=docket).first()
    if not entry:
        return "Couldn't find docket"
    elif entry.user_id:
        return f"<@{entry.user_id}>"
    return "Docket found, not claimed"


class GetDocket(Button):
    private_response = True
    auto_deferred: bool = True

    @classmethod
    async def execute(cls, ctx: Context, data: str):
        return await get(ctx, ctx.user_id)


class Button_Types(enum.Enum):
    Primary = Button_Styles.PRIMARY.name
    Secondary = Button_Styles.SECONDARY.name
    Success = Button_Styles.SUCCESS.name
    Danger = Button_Styles.DANGER.name


@register(group=Groups.ADMIN, main=docket, private_response=True, bot=963549809447432292)
async def button(ctx: Context, label: str, style: Button_Types, emoji: str = None, text: str = None):
    """
    Create button that acts like /docket get
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
        components=Row(GetDocket(label=label, emoji=emoji, style=Button_Styles.get(style.value))),
        channel_id=ctx.channel_id,
    )
    return "Message sent!"
