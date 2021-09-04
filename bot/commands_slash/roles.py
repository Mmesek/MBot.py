from MFramework import register, Groups, Context, Snowflake, ChannelID, RoleID

@register(group=Groups.MODERATOR)
async def role(ctx: Context, *args, language, **kwargs):
    '''Manages Roles'''
    pass

@register(group=Groups.MODERATOR, main=role)
async def reaction(ctx: Context, *args, language, **kwargs):
    '''Manages Reaction Roles'''
    pass

@register(group=Groups.MODERATOR, main=reaction, aliases=['rra'])
async def create(ctx: Context, emoji: str, role: RoleID, group: str = None, channel: ChannelID = None, message_id: Snowflake = None, *args, language, **kwargs):
    '''
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
    '''
    from mlib.utils import replaceMultiple
    reaction = f"{emoji}:0" if ":" not in emoji else replaceMultiple(emoji, ['<:', '>'], '')
    if group not in ctx.cache.reaction_roles:
        ctx.cache.reaction_roles[group] = {message_id: {reaction: [role]}}
    else:
        if message_id not in ctx.cache.reaction_roles[group]:
            ctx.cache.reaction_roles[group][message_id] = {reaction: [role]}
        else:
            ctx.cache.reaction_roles[group][message_id][reaction] = [role]
    from MFramework.database.alchemy import models, types
    s = ctx.db.sql.session()
    r = models.Role.fetch_or_add(s, server_id = ctx.guild_id, id=role)
    r.add_setting(types.Setting.ChannelID, channel)
    r.add_setting(types.Setting.MessageID, message_id)
    r.add_setting(types.Setting.Reaction, reaction)
    if group:
        r.add_setting(types.Setting.Group, group)
    s.commit()
    await ctx.bot.create_reaction(channel, message_id, replaceMultiple(emoji, ['<:', '>'], ''))
    await ctx.reply(f"Successfully created reaction {emoji} for role <@&{role}>", private=True)

#@register(group=Groups.MODERATOR, main=reaction, aliases=['rre'])
async def edit(ctx: Context, emoji: str, role: RoleID, group: str = None, channel: ChannelID = None, message_id: Snowflake = None, *args, language, **kwargs):
    '''
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
    '''
    # FIXME!
    await ctx.bot.delete_own_reaction(channel, message_id, emoji)
    await ctx.bot.create_reaction(channel, message_id, emoji)
    return await ctx.reply("Successfully modified reaction role")

@register(group=Groups.MODERATOR, main=reaction, aliases=['rrd'])
async def remove(ctx: Context, emoji: str = None, role: RoleID = None, group: str = None, channel: ChannelID = None, message_id: Snowflake = None, *args, language, **kwargs):
    '''
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
    '''
    from MFramework.database.alchemy import models, types
    s = ctx.db.sql.session()
    if role:
        r = models.Role.filter(s, server_id = ctx.guild_id, id=role).first()
    elif emoji:
        from mlib.utils import replaceMultiple
        r = models.Role.with_setting(types.Setting.Reaction, replaceMultiple(emoji, ['<:', '>'], '')).filter(server_id=ctx.guild_id).first()
    else:
        return ctx.reply("Either Emoji or Role has to be specified", private=True)
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
    await ctx.reply(f"Successfully deleted <@&{role}> from being a {emoji if ':0' in emoji else '<:'+emoji+'>'} reaction role", private=True)

class RoleTypes:
    AND = "AND"
    OR = "OR"
    COMBINED = "COMBINED"

#@register(group=Groups.ADMIN, main=role)
async def level(ctx: Context, role: RoleID, req_exp: int= 0, req_voice: int= 0, type: RoleTypes = RoleTypes.AND, stacked: bool=False, *, language):
    '''Management of level roles

    Params
    ------
    role:
        Role which should be awarded for reaching these values
    req_exp:
        Chat exp required to gain this role
    req_voice:
        Voice exp required to gain this role
    type:
        Whether both, either or in total exp should award this role
    '''
    pass