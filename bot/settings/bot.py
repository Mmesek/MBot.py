from binascii import b2a_base64

import httpx
from MFramework import Groups, register, Attachment

from bot import Context
from bot.settings import settings


@register(Groups.OWNER, main=settings, private_response=True)
async def bot():
    """Bot related commands"""


async def get_attachment(url: str):
    result = await httpx.get(url)
    if result.ok:
        return f"data:image/{url.split('.')[-1] if '.' in url else 'png'};base64,{b2a_base64(result.content).decode()}"


@register(group=Groups.OWNER, main=bot, private_response=True)
async def presence(
    ctx: Context, avatar: Attachment = None, nick: str = None, bio: str = None, banner: Attachment = None
):
    """
    Change bot's server presence
    Params
    ------
    avatar:
        New avatar picture
    nick:
        New nickname
    bio:
        New bio
    banner:
        New banner picture
    """
    kwargs = {}
    if avatar:
        if r := await get_attachment(avatar.url):
            kwargs["avatar"] = r
    if banner:
        if r := await get_attachment(banner.url):
            kwargs["banner"] = r
    if nick:
        kwargs["nick"] = nick
    if bio:
        kwargs["bio"] = bio

    if kwargs:
        await ctx.bot.modify_current_member(
            ctx.guild_id,
            **kwargs,
            reason=f"Request made by {ctx.user.username}",
        )
        return "Changed"
    return "Error fetching avatar"


@register(group=Groups.OWNER, main=bot, private_response=True)
async def reset(ctx: Context, field: str):
    """
    Reset customised bot presence
    Params
    ------
    field:
        Field to reset
        Choices:
            avatar = avatar
            nick = nick
            bio = bio
            banner = banner
    """
    kwargs = {field: None}
    await ctx.bot.modify_current_member(ctx.guild_id, **kwargs, reason=f"Request made by {ctx.user.username}")
    return f"Reverted `{field}`"


@register(group=Groups.SYSTEM, interaction=False)
async def username(ctx: Context, name: str):
    """
    Change bot's username
    Params
    ------
    name:
        Bot's new Name
    """
    await ctx.bot.modify_current_member(ctx.guild_id, nick=name)
    return "Changed"


@register(group=Groups.ADMIN, interaction=False)
async def nick(ctx: Context, nick: str):
    """
    Changes bot nickname
    Params
    ------
    nick:
        New nickname
    """
    await ctx.bot.modify_current_user_nick(ctx.guild_id, nick, reason=f"Request made by {ctx.user.username}")
    return "New nickname: " + nick
