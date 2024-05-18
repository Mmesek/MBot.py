from MFramework import (
    Bot,
    ChannelID,
    Context,
    Groups,
    Message_Reaction_Add,
    Message_Reaction_Remove,
    RoleID,
    Snowflake,
    onDispatch,
    register,
)
from mlib.utils import replace_multiple

from bot.database import models, types
from bot.systems.roles import role


@register(group=Groups.MODERATOR, main=role)
async def reaction():
    """Manages Reaction Roles"""
    pass


@register(group=Groups.MODERATOR, main=reaction, aliases=["rra"], private_response=True)
async def create(
    ctx: Context,
    emoji: str,
    role: RoleID,
    group: str = None,
    channel: ChannelID = None,
    message_id: Snowflake = None,
):
    """
    Adds new reaction role
    Params
    ------
    emoji:
        Emoji to use as a reaction
    role:
        Role that should be given for reacting
    group:
        Whether this RR should belong to a group
    channel:
        Channel in which RR should be created. Empty means current channel
    message_id:
        Message ID under which RR should be created. Empty means last message in channel
    """
    reaction = f"{emoji}:0" if ":" not in emoji else replace_multiple(emoji, ["<:", ">"], "")

    if group not in ctx.cache.reaction_roles:
        ctx.cache.reaction_roles[group] = {message_id: {reaction: [role]}}
    else:
        if message_id not in ctx.cache.reaction_roles[group]:
            ctx.cache.reaction_roles[group][message_id] = {reaction: [role]}
        else:
            ctx.cache.reaction_roles[group][message_id][reaction] = [role]

    s = ctx.db.sql.session()

    r = models.Role.fetch_or_add(s, server_id=ctx.guild_id, id=role)
    r.add_setting(types.Setting.ChannelID, channel)
    r.add_setting(types.Setting.MessageID, message_id)
    r.add_setting(types.Setting.Reaction, reaction)
    if group:
        r.add_setting(types.Setting.Group, group)
    s.commit()

    await ctx.bot.create_reaction(channel, message_id, replace_multiple(emoji, ["<:", ">"], ""))
    return f"Successfully created reaction {emoji} for role <@&{role}>"


# @register(group=Groups.MODERATOR, main=reaction, aliases=['rre'], private_response=True)
async def edit(
    ctx: Context,
    emoji: str,
    role: RoleID,
    group: str = None,
    channel: ChannelID = None,
    message_id: Snowflake = None,
):
    """
    Edits existing reaction role
    Params
    ------
    emoji:
        Emoji to use as a reaction
    role:
        Role that should be given for reacting
    group:
        Whether this RR should belong to a group
    channel:
        Channel in which RR should be edited. Empty means current channel
    message_id:
        Message ID under which RR should be edited. Empty means last message in channel
    """
    # FIXME!
    await ctx.bot.delete_own_reaction(channel, message_id, emoji)
    await ctx.bot.create_reaction(channel, message_id, emoji)
    return "Successfully modified reaction role"


@register(group=Groups.MODERATOR, main=reaction, aliases=["rrd"], private_response=True)
async def remove(
    ctx: Context,
    emoji: str = None,
    role: RoleID = None,
    group: str = None,
    channel: ChannelID = None,
    message_id: Snowflake = None,
):
    """
    Removes existing reaction role
    Params
    ------
    emoji:
        Emoji to remove from being reaction emoji
    role:
        Role to remove from being reaction role
    group:
        Whether this RR should be removed from belonging to a group
    channel:
        Channel from which RR should be removed. Empty means current channel
    message_id:
        Message ID under which RR should be removed. Empty means last message in channel
    """
    s = ctx.db.sql.session()

    if role:
        r = models.Role.filter(s, server_id=ctx.guild_id, id=role).first()
    elif emoji:
        r = (
            models.Role.with_setting(types.Setting.Reaction, replace_multiple(emoji, ["<:", ">"], ""))
            .filter(server_id=ctx.guild_id)
            .first()
        )
    else:
        return "Either Emoji or Role has to be specified"

    if group:
        r.remove_setting(types.Setting.Group)
        s.commit()
        return

    emoji = r.remove_setting(types.Setting.Reaction)
    channel = r.remove_setting(types.Setting.ChannelID)
    message_id = r.remove_setting(types.Setting.MessageID)
    group = r.remove_setting(types.Setting.Group)
    s.commit()

    ctx.cache.reaction_roles.get(group, {}).get(message_id, {}).pop(emoji, None)
    if ctx.cache.reaction_roles.get(group, {}).get(message_id, None) == {}:
        ctx.cache.reaction_roles.get(group, {}).pop(message_id, None)
        if ctx.cache.reaction_roles.get(group, None) == {}:
            ctx.cache.reaction_roles.pop(group)

    await ctx.bot.delete_own_reaction(channel, message_id, emoji)
    return f"Successfully deleted <@&{role}> from being a {emoji if ':0' in emoji else '<:'+emoji+'>'} reaction role"


@onDispatch(predicate=lambda x: x.guild_id and not x.member.user.bot)
async def message_reaction_add(self: Bot, data: Message_Reaction_Add):
    roles = self.cache[data.guild_id].reaction_roles
    r = []

    for group in roles:
        for msg in roles[group]:
            if data.message_id == msg:
                r = roles[group][data.message_id][f"{data.emoji.name}:{data.emoji.id or 0}"]
                if group is None:
                    continue
                elif all(i in data.member.roles for i in r):
                    return
                elif any(
                    i in data.member.roles for i in [j for e in roles[group][data.message_id].values() for j in e]
                ):
                    return await self.delete_user_reaction(
                        data.channel_id,
                        data.message_id,
                        f"{data.emoji.name}:{data.emoji.id}" if data.emoji.id else data.emoji.name,
                        data.user_id,
                    )

    for i in r:
        await self.add_guild_member_role(data.guild_id, data.user_id, i, "Reaction Role")


@onDispatch(predicate=lambda x: x.guild_id)
async def message_reaction_remove(self: Bot, data: Message_Reaction_Remove):
    roles = self.cache[data.guild_id].reaction_roles
    r = []

    for group in roles:
        if data.message_id in roles[group]:
            role = roles[group][data.message_id][f"{data.emoji.name}:{data.emoji.id or 0}"]
            if role == None:
                return
            break

    for i in r:
        await self.remove_guild_member_role(data.guild_id, data.user_id, i, "Reaction Role")
