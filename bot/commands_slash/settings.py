from MFramework import (
    Bitwise_Permission_Flags,
    Channel,
    ChannelID,
    Context,
    Groups,
    Overwrite,
    Snowflake,
    register,
)


@register(group=Groups.ADMIN)
async def settings():
    """Management of server related bot settings"""
    pass


@register(group=Groups.ADMIN, main=settings)
async def language(ctx: Context, new_language: str = None, channel: ChannelID = None, *, language):
    """Management of language bot settings

    Params
    ------
    new_language:
        New language that should be set
    channel:
        Channel of which language should be changed. Leave empty if server-wide
    """
    pass


class Tracking:
    Chat = "Chat"
    Voice = "Voice"
    Presence = "Presence"


@register(group=Groups.ADMIN, main=settings)
async def tracking(ctx: Context, type: Tracking, channel: ChannelID = None, *, language):
    """Management of bot's tracking settings

    Params
    ------
    type:
        Tracking type to switch
    channel:
        Whether this channel should be disabled from tracking
    """
    pass


@register(group=Groups.ADMIN, main=settings)
async def webhooks():
    """Management of webhooks related bot settings"""
    pass


@register(group=Groups.ADMIN, main=webhooks)
async def subscribe(
    ctx: Context,
    source: str,
    channel: ChannelID = None,
    webhook: str = None,
    content: str = None,
    regex: str = None,
    *,
    language,
):
    """Subscribe webhook to specified source

    Params
    ------
    source:
        Source to which this webhook/channel should be subscribed to
    webhook:
        Webhook URL to subscribe to. If empty, creates one
    content:
        Content of message to send alongside
    regex:
        Whether it should only be sent if there is matching pattern
    """
    from MFramework.database.alchemy import models

    _w = models.Webhook()
    if webhook:
        webhooks = await ctx.bot.get_guild_webhooks(ctx.guild_id)
        for wh in filter(lambda x: x.channel_id == channel or ctx.channel_id, webhooks):
            if wh.user.id == ctx.bot.user_id or any(s in wh.name for s in {"RSS", "DM"}):
                _w.id = wh.id
                _w.token = wh.token
                break
    if not webhook and not _w.id:
        if "log" in source.lower():
            name = "Logging"
        elif "dm" not in source.lower():
            name = "RSS"
        else:
            name = "DM Inbox"
        wh = await ctx.bot.create_webhook(channel, name, f"Requested by {ctx.user.username}")
        _w.id = wh.id
        _w.token = wh.token
    _w.channel_id = channel
    _w.server_id = ctx.guild_id
    s = ctx.db.sql.session()
    s.add(_w)
    s.commit()


@register(group=Groups.ADMIN, main=webhooks)
async def unsubscribe(ctx: Context, source: str, webhook: str = None, *, language):
    """Unsubscribe this channel from provided source

    Params
    ------
    source:
        Source to unsubscribe from
    webhook:
        Webhook which should be unsubscribed
    """
    pass


@register(group=Groups.ADMIN, main=settings)
async def roles():
    """Management of role related bot settings"""
    pass


@register(group=Groups.ADMIN, main=settings)
async def channels():
    """Management of channel related bot settings"""
    pass


class ChannelTypes:
    RPG = "RPG"
    Dynamic = "Dynamic"
    Buffer = "Buffer"


@register(group=Groups.ADMIN, main=channels)
async def type(
    ctx: Context,
    type: ChannelTypes,
    channel: ChannelID = None,
    name: str = None,
    parent_or_buffer_id: Snowflake = None,
    bitrate: int = 64000,
    user_limit: int = 0,
    postion: int = 0,
    *,
    language,
):
    """Sets type to specified channel

    Params
    ------
    type:
        type of channel
    """
    pass


@register(group=Groups.ADMIN, main=settings)
async def slowmode(
    ctx: Context, limit: int = 0, duration: int = 0, channel: ChannelID = None, all: bool = False, *, language
):
    """
    Sets a slowmode on a channel
    Params
    ------
    limit:
        Slowmode duration
    duration:
        How long slowmode should last
    channel:
        Channel to slowmode
    all:
        Whether slowmode should be server-wide or not
    """
    channels = {}
    d = int(duration)
    m = await ctx.reply(f"Applying Slowmode in progress...")
    if all:
        for channel in ctx.cache.channels.values():
            if channel.type == 0:
                try:
                    channels[channel.id] = channel.rate_limit_per_user
                    await ctx.bot.modify_channel(
                        channel.id, rate_limit_per_user=limit, reason="Global Slow mode command"
                    )
                except:
                    pass
    else:
        channels[channel] = ctx.cache.channels.get(channel, Channel).rate_limit_per_user
        await ctx.bot.modify_channel(channel, rate_limit_per_user=limit, reason="Slow mode command")
    await m.edit(f"{'Server wide ' if all else ''}Slow mode activiated")
    if d > 0:
        import asyncio

        await asyncio.sleep(d)
        for channel, previous_limit in channels.items():
            try:
                await ctx.bot.modify_channel(channel, rate_limit_per_user=previous_limit, reason="Slow mode expired")
            except Exception as ex:
                pass
        await ctx.reply(f"{'Server wide ' if all else ''}Slow mode finished")


@register(group=Groups.ADMIN, main=settings)
async def lockdown(ctx: Context, duration: int = 0, channel: ChannelID = None, all: bool = False, *, language):
    """
    Sets a lockdown on a channel
    Params
    ------
    duration:
        How long lockdown should last
    channel:
        Channel to lockdown
    all:
        Whether lockdown should be server-wide or not
    """
    channels = {}
    d = int(duration)
    lockdown = Bitwise_Permission_Flags.SEND_MESSAGES.value | Bitwise_Permission_Flags.ADD_REACTIONS.value
    m = await ctx.reply(f"Applying Lockdown in progress...")
    if all:
        for channel in ctx.cache.channels.values():
            channels[channel.id] = channel.permission_overwrites
            channel_overwrites = []
            for overwrite in channel.permission_overwrites:
                channel_overwrites.append(
                    Overwrite(
                        id=overwrite.id, type=overwrite.type, allow=overwrite.allow, deny=overwrite.deny | lockdown
                    )
                )
            await ctx.bot.modify_channel(
                channel.id, permission_overwrites=channel_overwrites, reason="Global Lockdown command"
            )
    else:
        channel = ctx.bot.cache[ctx.guild_id].channels.get(channel, Channel).permission_overwrites
        channels[channel] = channel
        channel_overwrites = []
        for overwrite in channel:
            channel_overwrites.append(
                Overwrite(
                    id=overwrite.id, type=overwrite.type, allow=overwrite.allow, deny=int(overwrite.deny) | lockdown
                )
            )
        await ctx.bot.modify_channel(channel, permission_overwrites=channel_overwrites, reason="Lockdown command")
    await m.edit(f"{'Server wide ' if all else ''}Lockdown activiated")
    if d > 0:
        import asyncio

        await asyncio.sleep(d)
        for channel in channels:
            previous_overwrites = channels[channel]
            await ctx.bot.modify_channel(channel, permission_overwrites=previous_overwrites, reason="Lockdown expired")
        await ctx.reply(f"{'Server wide ' if all else ''}Lockdown finished")
