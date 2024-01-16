from enum import Enum

from MFramework import (
    Bitwise_Permission_Flags,
    Channel,
    ChannelID,
    Context,
    Groups,
    Interaction,
    Overwrite,
    RoleID,
    register,
)
from MFramework.database.alchemy import models, types
from MFramework.utils.log import Log
from mlib.utils import all_subclasses


@register(group=Groups.ADMIN)
async def settings():
    """Management of server related bot settings"""
    pass


# @register(group=Groups.ADMIN, main=settings)
async def language(ctx: Context, new_language: str = None, channel: ChannelID = None):
    """Management of language bot settings

    Params
    ------
    new_language:
        New language that should be set
    channel:
        Channel of which language should be changed. Leave empty if server-wide
    """
    raise NotImplementedError("Not implemented yet!")


class Tracking(Enum):
    Chat = 1 << 0
    Voice = 1 << 1
    Presence = 1 << 2
    Activity = 1 << 3
    Nitro = 1 << 4


@register(group=Groups.ADMIN, main=settings)
async def tracking(ctx: Context, type: Tracking):
    """Management of bot's tracking settings

    Params
    ------
    type:
        Tracking type to switch
    channel:
        Whether this channel should be disabled from tracking
    """
    s = ctx.db.sql.session()
    server: models.Server = s.query(models.Server).filter(models.Server.id == ctx.guild_id).first()

    tracking = server.get_setting(types.Setting.Flags) or 0
    if not tracking & type.value:
        state = "enabled"
        new_tracking = tracking | type.value
    else:
        state = "disabled"
        new_tracking = tracking & ~type.value
    server.add_setting(types.Setting.Flags, new_tracking)
    s.commit()

    ctx.cache.load_settings(server)
    return f"Tracking {state} for {type.name}. Bitflag change: `{tracking}` -> `{new_tracking}`"


@register(group=Groups.ADMIN, main=settings)
async def webhooks():
    """Management of webhooks related bot settings"""
    pass


async def get_logger(interaction: Interaction, current: str):
    return [i.__name__ for i in all_subclasses(Log) if current in i.__name__]


async def configured_loggers(interaction: Interaction, current: str):
    return [i for i in interaction._Client.cache[interaction.guild_id].webhooks.keys() if current in i]


@register(group=Groups.ADMIN, main=webhooks)
async def subscribe(ctx: Context, logger: get_logger, channel: Channel = None):
    """Subscribe channel to specified logger source

    Params
    ------
    logger:
        Source to which this channel should be subscribed to
    channel:
        Channel which should subscribe to this logger. Default is current channel
    """
    if channel.type in {10, 11, 12}:
        thread = channel.id
        channel_id = channel.parent_id
    elif channel.type not in {0, 2, 5}:
        # NOTE: Forum channels require specific behaviour on logger side, therefore they aren't included here
        return "Specify either a Thread or a regular text channel."
    else:
        thread = None
        channel_id = channel.id

    s = ctx.db.sql.session()

    _c = (
        s.query(models.Channel)
        .filter(models.Channel.server_id == ctx.guild_id, models.Channel.id == channel_id)
        .first()
    )
    if not _c:
        s.add(models.Channel(server_id=ctx.guild_id, id=channel_id))

    _w = (
        s.query(models.Webhook)
        .filter(models.Webhook.server_id == ctx.guild_id, models.Webhook.channel_id == channel_id)
        .first()
    )
    if not _w:
        _w = models.Webhook(server_id=ctx.guild_id, channel_id=channel_id)

        webhooks = await ctx.bot.get_channel_webhooks(channel_id or ctx.channel_id)
        for wh in webhooks:
            if wh.user.id == ctx.bot.user_id:
                _w.id = wh.id
                _w.token = wh.token
                break
        if not _w.id:
            wh = await ctx.bot.create_webhook(
                channel_id, f"{ctx.bot.username} Logging", f"Requested by {ctx.user.username}"
            )
            _w.id = wh.id
            _w.token = wh.token

        s.add(_w)

    _w.subscriptions.append(models.Subscription(source=f"logging-{logger.lower()}", thread_id=thread, regex=""))
    s.commit()
    await ctx.cache.get_Webhooks(s)
    await ctx.cache.set_loggers(ctx.bot)
    return f"Channel <#{channel_id}> is now subscribed to {logger}"


@register(group=Groups.ADMIN, main=webhooks)
async def unsubscribe(ctx: Context, logger: configured_loggers, channel: ChannelID = None):
    """Unsubscribe this channel from provided logger

    Params
    ------
    logger:
        Source to unsubscribe from
    channel:
        Channel which should unsubscribe
    """
    s = ctx.db.sql.session()

    _w = (
        s.query(models.Webhook)
        .filter(models.Webhook.server_id == ctx.guild_id, models.Webhook.channel_id == channel)
        .first()
    )
    if not _w:
        return "This channel doesn't have any webhooks associated with it"
    s.delete(
        s.query(models.Subscription)
        .filter(models.Subscription.webhook_id == _w.id, models.Subscription.source == f"logging-{logger}")
        .first()
    )
    s.commit()
    ctx.cache.get_Webhooks(s)
    ctx.cache.set_loggers(ctx.bot)
    return f"Unsubscribed from {logger} on channel <#{channel}>"


@register(group=Groups.ADMIN, main=settings)
async def roles():
    """Management of role related bot settings"""
    pass


@register(group=Groups.OWNER, main=roles, private_response=True)
async def permission(ctx: Context, role: RoleID, permission_level: Groups = None):
    """
    Configure Role permission for bot management
    Params
    ------
    role:
        Role to configure
    permission:
        Permission level this role should have
    """
    if not ctx.permission_group.can_use(permission_level or Groups.GLOBAL):
        return f"You can't set role to permission higher than your own ({ctx.permission_group.name.title()})"

    session = ctx.db.sql.session()

    _role: models.Role = (
        session.query(models.Role).filter(models.Role.server_id == ctx.guild_id, models.Role.id == role).first()
    )
    if not permission_level:
        if _role:
            group = Groups.get(_role.get_setting(types.Setting.Permissions))
        else:
            group = Groups.GLOBAL
        return f"Current Permission level for <@&{role}> is `{group.name.title()}`"
    if not _role:
        _role = models.Role(server_id=ctx.guild_id, id=role)
        session.add(_role)
    session.commit()

    _role.modify_setting(types.Setting.Permissions, permission_level.value)
    ctx.cache.groups[permission_level].add(role)
    return f"Permission Level for <@&{role}> is now `{permission_level.name.title()}`"


@register(group=Groups.ADMIN, main=settings)
async def channels():
    """Management of channel related bot settings"""
    pass


@register(group=Groups.ADMIN, main=channels)
async def rpg(ctx: Context, channel: ChannelID):
    """Toggles dice roll on *italics* in specified channel

    Params
    ------
    channel:
        channel to toggle
    """
    session = ctx.db.sql.session()
    _channel = (
        session.query(models.Channel)
        .filter(models.Channel.server_id == ctx.guild_id, models.Channel.id == channel)
        .first()
    )
    if not _channel:
        _channel = models.Channel(server_id=ctx.guild_id, id=channel)
        session.add(_channel)

    if _channel.get_setting(types.Setting.RPG):
        state = "disabled"
        ctx.cache.rpg_channels.remove(channel)
        _channel.remove_setting(types.Setting.RPG)
    else:
        state = "enabled"
        ctx.cache.rpg_channels.append(channel)
        _channel.add_setting(types.Setting.RPG, True)
    session.commit()
    return f"Dice roll on *italics* is now {state} for <#{channel}>"


@register(group=Groups.ADMIN, main=settings)
async def slowmode(ctx: Context, limit: int = 0, duration: int = 0, channel: ChannelID = None, all: bool = False):
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
        channels[channel] = await ctx.cache.channels.get(channel, Channel).rate_limit_per_user
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
async def lockdown(ctx: Context, duration: int = 0, channel: ChannelID = None, all: bool = False):
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
        for channel in ctx.cache.channels.values():  # FIXME?
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
        channel = await ctx.bot.cache[ctx.guild_id].channels.get(channel, Channel).permission_overwrites
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
