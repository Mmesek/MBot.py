from enum import Enum

from MFramework import (
    Bitwise_Permission_Flags,
    Channel,
    ChannelID,
    Context,
    Groups,
    Overwrite,
    RoleID,
    register,
)

from bot.database import models, types


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
    m = await ctx.reply("Applying Slowmode in progress...")
    if all:
        for channel in ctx.cache.channels.values():
            if channel.type == 0:
                try:
                    channels[channel.id] = channel.rate_limit_per_user
                    await ctx.bot.modify_channel(
                        channel.id, rate_limit_per_user=limit, reason="Global Slow mode command"
                    )
                except Exception:
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
            except Exception:
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
    m = await ctx.reply("Applying Lockdown in progress...")
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
