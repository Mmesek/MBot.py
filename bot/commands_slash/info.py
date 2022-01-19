from MFramework import register, Groups, Context, Embed, Snowflake, RoleID, ChannelID, Role, Bitwise_Permission_Flags, Guild_Member, Premium_Types, User_Flags

@register()
async def info(ctx: Context):
    '''Shows info'''
    pass

@register(group=Groups.GLOBAL, main=info)
async def user(ctx: Context, member: Guild_Member = None) -> Embed:
    '''Shows user info
    Params
    ------
    member:
        Member to show info about'''
    await ctx.deferred()
    if not member or not ctx.permission_group.can_use(Groups.HELPER):
        member = ctx.member
    from mlib.colors import get_main_color
    embed = (
        Embed()
            .setAuthor(name=f"{member.user.username}#{member.user.discriminator}", icon_url=member.user.get_avatar())
            .setThumbnail(member.user.get_avatar())
            .setColor(get_main_color(member.user.get_avatar()))
            .setFooter(text=f"ID: {member.user.id}")
    )
    
    dates = []
    dates.append(("On Discord since", member.user.id.styled_date()))
    if member:
        import time
        dates.append(("Joined Server at", f"<t:{int(time.mktime(member.joined_at.timetuple()))}>"))
        try:
            dates.append(("Booster since", f"<t:{int(time.mktime(member.premium_since.timetuple()))}>"))
        except:
            pass
    embed.addField("Dates", '\n'.join(format_values(dates)))
    
    names = [
        ("Nick", member.nick),
        ("Username", member.user.username)
    ]
    if member.nick:
        embed.addField("Names", "\n".join(format_values(names, lambda x: x[1])), False)

    flags = [
        ("Verified", member.user.verified),
        ("System", member.user.system),
        ("Bot", member.user.bot),
        ("Pending", member.pending),
        ("Multi Factor Authentication", member.user.mfa_enabled)
    ]
    if any(i[1] for i in flags):
        embed.addField("User Flags", '\n'.join([f[0] for f in flags if f[1]]), True)

    badges = User_Flags.current_permissions(User_Flags, member.user.public_flags)
    if badges != ["NONE"]:
        embed.addField("Badges", ", ".join(i.title().replace("_", " ") for i in badges if i != "NONE"), True)

    if member.user.locale:
        embed.addField("Language", member.user.locale, True)

    vc_state = [
        ("Muted", member.mute),
        ("Deafed", member.deaf)
    ]
    if any(i[1] for i in vc_state):
        embed.addField("Voice", ", ".join([i[0] for i in vc_state if i[1]]), True)

    if member.user.premium_type:
        embed.addField("Nitro Type", Premium_Types.get(member.user.premium_type).name.title(), True)

    roles = [f"<@&{i}>" for i in member.roles]
    if len(roles):
        embed.addField(f"Roles [{len(roles)}]", ", ".join(roles))

    try:
        permissions = Bitwise_Permission_Flags.current_permissions(Bitwise_Permission_Flags, int(member.permissions))
    except:
        permissions = []

    if permissions:
        embed.addField("Permissions", ", ".join(i.title().replace("_", " ") for i in permissions))

    embed.addField("\u200b", "\u200b")

    s = ctx.db.sql.session()
    from ..database import User
    u = User.by_id(s, id=member.user.id)
    if u:
        from datetime import datetime
        infractions = list(filter(lambda x: x.server_id == ctx.guild_id, u.infractions))
        if infractions:
            _ = [
                ("Total", len(infractions)),
                ("Active", len([i.expires_at for i in infractions if i.expires_at >= datetime.utcnow()]))
            ]
            embed.addField("Infractions", "\n".join(format_values(_, lambda x: x[1])), True)
        mod_actions = list(filter(lambda x: x.server_id == ctx.guild_id, u.mod_actions))
        if mod_actions:
            embed.addField("Moderation Actions", str(len(mod_actions)), True)
        _stats = []
        for stat in filter(lambda x: x.server_id == ctx.guild_id, u.statistics):
            _stats.append((stat.name.name, stat.value))
        if _stats:
            embed.addField("Statistics", "\n".join(format_values(_stats)), False)

    return embed

from typing import Callable, List, Tuple
def format_values(iterable: List[Tuple[str, str]], check: Callable = None):
    if check:
        iterable = list(filter(check, iterable))
    longest_string = max([len(i[0]) for i in iterable])
    r = []
    for name, value in iterable:
        r.append(f"`{name.replace('_', ' '):>{longest_string}}`: {value}")
    return r

@register(group=Groups.MODERATOR, main=info)
async def server(ctx: Context) -> Embed:
    '''Shows server info'''
    await ctx.deferred()
    guild = await ctx.bot.get_guild(ctx.guild_id, True)
    channel_names = {"Widget":guild.widget_channel_id, "Rules":guild.rules_channel_id, "Public Updates":guild.public_updates_channel_id, "AFK":guild.afk_channel_id, "System":guild.system_channel_id}
    channels = [f"{key} Channel <#{value}>" for key, value in channel_names.items() if value]
    fields = {
        "Channels": f'Total Channels: {len(guild.channels)}\n'+'\n'.join(channels),
        "Emojis": f'Total Emojis: {len(guild.emojis)}',
        "Roles": f'Total Roles: {len(guild.roles)}',
        "Presences": f"Total Presences: {len(guild.presences)}",
        "Voice": f"{len(guild.voice_states)}\nAFK Timeout: {guild.afk_timeout}s",
        "Limits": f"Members: {guild.max_members}\nPresences: {guild.max_presences}\nVideo Users: {guild.max_video_channel_users}",
        "Boosters": f"Tier: {guild.premium_tier}\nBoosters: {guild.premium_subscription_count}",
        "Approximate Counts": f"Members: {guild.approximate_member_count}\nPresences: {guild.approximate_presence_count}", #TODO
        "Settings": "", #TODO
        "Region": f"Voice: {guild.region}\nLanguage: {guild.preferred_locale}",
        #"Widget": f"{guild.widget_enabled}", #TODO
        "Permissions": "", #TODO
        "Features": "", #TODO
        "General": f"{guild.member_count}" #TODO
    }
    embed = (
        Embed()
            .setTitle(guild.name)
            .setFooter(f"Server ID: {guild.id}")
            .setThumbnail(guild.get_icon(), width=500, height=500)
            .setImage(guild.get_splash())
            .setDescription(guild.description if guild.description else None)
            .setTimestamp(guild.id.as_date)
            .setAuthor(ctx.cache.members[guild.owner_id].user.username)
    )
    for field in fields:
        if fields[field] != "":
            embed.addField(field, fields[field], True)

    bans = await ctx.bot.get_guild_bans(ctx.guild_id)
    if bans != []:
        embed.addField(f"Amount of Bans", str(len(bans)), True)

    return embed

@register(group=Groups.MODERATOR, main=info)
async def role(ctx: Context, role_id: RoleID = 0) -> Embed:
    '''Shows role info'''
    await ctx.deferred()
    if role_id == 0:
        role_id = ctx.guild_id #Usually @everyone role has same id as guild
    roles = await ctx.bot.get_guild_roles(ctx.guild_id)
    role = list(filter(lambda x: x.id == role_id, roles))[0]

    color = str(hex(role.color)).replace("0x", "#")
    import time
    embed = (
        Embed()
            .setTitle(role.name)
            .setFooter(f"Role ID: {role.id}")
            .setTimestamp(role.id.as_date)
            .addField("Position", str(role.position), True)
            .addField("Displayed separately", str(role.hoist), True)
            .addField("Color", color, True)
            .addField("Mentionable", str(role.mentionable), True)
            .addField("Integration", str(role.managed), True)
            .addField("Permissions", str(role.permissions), True)
            .addField(
                "Created",
                str(
                    time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        role.id.as_date.timetuple(),
                    )
                ),
                True,
            )
            .setThumbnail("attachment://color.png")
    )
    embed.setColor(role.color)
    f = None
    if role.color:
        from mlib.colors import buffered_image
        from PIL import Image
        f = buffered_image(Image.new("RGB", (100, 100), color))
    await ctx.reply(embeds=[embed], file=f, filename="color.png")

@register(group=Groups.MODERATOR, main=info)
async def channel(ctx: Context, channel_id: ChannelID = 0) -> Embed:
    '''Shows channel info'''
    await ctx.deferred()
    if channel_id == 0:
        channel_id = ctx.channel_id
    channel = await ctx.bot.get_channel(channel_id)

    embed = Embed().setTitle("Channel Info").setThumbnail("").setDescription("")

    return embed

@register(group=Groups.ADMIN, main=info)
async def members(ctx: Context, role: Role, force_update: bool=False, show_id: bool=False) -> Embed:
    '''
    Lists users with provided role
    Params
    ------
    role:
        Role to fetch
    force_update:
        Whether new users should be pulled before counting (Delays response by around 30 seconds)
    '''
    await ctx.deferred(private=False)
    if force_update:
        await ctx.bot.request_guild_members(ctx.guild_id)
        import asyncio
        await asyncio.sleep(30)
    total = []
    for member_id, member in ctx.cache.members.items():
        if role.id in member.roles:
            total.append(member_id)
    from MFramework import Embed
    if show_id:
        desc = ",".join([str(i) for i in total])
    else:
        desc = ''.join([f'<@{i}>' for i in total])
    embed = Embed().setDescription(desc).setFooter(f'Total users/members: {len(total)}/{len(ctx.cache.members)}')
    embed.setColor(role.color).setTitle(f'List of members with role {role.name}')
    return embed

@register(group=Groups.GLOBAL, main=info)
async def created(ctx: Context, snowflake: Snowflake) -> Embed:
    '''
    Shows when the snowflake was created
    Params
    ------
    snowflake:
        Snowflake to check
    '''
    await ctx.deferred()
    names = []
    _member, _channel, _role = None, None, None
    try:
        _member = await ctx.bot.get_guild_member(ctx.guild_id, snowflake)
    except:
        _role = [i for i in ctx.cache.roles if i == snowflake]
        if _role:
            names.append(("Role", f"<@&{snowflake}>"))
        _channel = [i for i in ctx.cache.channels if i == snowflake]
        if _channel:
            names.append(("Channel", f"<#{snowflake}>"))
    if not _role and not _channel:
        names.append(("User", f"<@{snowflake}>"))
    names.append(("On Discord since", snowflake.styled_date()))
    if _member:
        import time
        names.append(("Joined Server at", f"<t:{int(time.mktime(_member.joined_at.timetuple()))}>"))
        try:
            names.append(("Booster since", f"<t:{int(time.mktime(_member.premium_since.timetuple()))}>"))
        except:
            pass
    embed = Embed()
    embed.addField(f"{snowflake}",'\n'.join(format_values(names)))
    return embed
