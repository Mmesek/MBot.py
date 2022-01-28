from MFramework import register, Context, Groups, Embed, Snowflake

@register(group=Groups.ADMIN, interaction=False)
async def edit_message(ctx: Context, messageID, *newMessage,  channel, **kwargs):
    '''Edits bot's message'''
    await ctx.bot.edit_message(channel[0], messageID, ' '.join(newMessage))


@register(group=Groups.ADMIN, interaction=False)
async def edit_emoji(ctx: Context, emojis, roles, *args,  **kwargs):
    '''Allows only specific roles access to emoji's'''
    for emoji in emojis:
        if "<:" in emoji:
            part2 = emoji.replace("\\<:", "").replace(">", "").replace(":", " ").split(" ", 2)
            await ctx.bot.modify_guild_emoji(ctx.guild_id, part2[1], part2[0], roles)


@register(group=Groups.ADMIN, interaction=False)
async def aemoji(ctx: Context, emoji_name) -> str:
    '''Sends animated emoji'''
    emojis = await ctx.bot.list_guild_emoji(ctx.guild_id)
    message = ""
    for emoji in emojis:
        if emoji.name == emoji_name:
            if emoji.animated:
                message += f"<a:{emoji.name}:{emoji.id}> "
            else:
                message += f"<:{emoji.name}:{emoji.id}> "
    await ctx.delete()
    return message


@register(group=Groups.ADMIN, interaction=False)
async def list_emoji(ctx: Context, *args,  all=False, regular=False) -> Embed:
    '''Lists all available emoji's in guild'''
    emojis = await ctx.bot.list_guild_emojis(ctx.guild_id)
    _animated = ""
    _regular = ""
    for emoji in emojis:
        if emoji.animated and not regular:
            _animated += f"\n<a:{emoji.name}:{emoji.id}> - a:{emoji.name}:{emoji.id}"
        elif not emoji.animated and (all or regular):
            _regular += f"\n<:{emoji.name}:{emoji.id}> - {emoji.name}:{emoji.id}"
    e = Embed().setTitle("Emoji List")
    if not regular and _animated != "":
        e.addFields("Animated", _animated, False)
    if (all or regular) and _regular != "":
        if regular and (len(_regular) / 1024 <= 2):
            inline = True
        else:
            inline = False
        e.addFields("Regular", _regular, inline)
    return e


@register(group=Groups.ADMIN, interaction=False)
async def delete(ctx: Context, channel, *message):
    '''Delete's message'''
    await ctx.bot.delete_message(channel, *message)

@register(group=Groups.ADMIN, interaction=False)
async def getmessages(ctx: Context, user) -> Embed:
    '''Retrives messages from DM'''
    dm = await ctx.bot.create_dm(user)
    messages = await ctx.bot.get_messages(dm.id)
    message = ""
    for each in messages:
        message += f"\n`[{each.timestamp[:19]}]` - `{each.author.username}`: {each.content}"
    e = Embed().setFooter("", f"DM ID: {dm.id}").setDescription(message[:2000])
    return e

@register(group=Groups.ADMIN, interaction=False)
async def prunecount(ctx: Context, days=7) -> str:
    '''Shows prune count'''
    count = await ctx.bot.get_guild_prune_count(ctx.guild_id, days)
    return str(count)

@register(group=Groups.MODERATOR, interaction=False)
async def role_icon(ctx: Context, role: Snowflake, emoji: str):
    '''
    Allows setting icons for roles
    Params
    ------
    role:
        role to modify
    emoji:
        Unicode Emoji, Discord Emoji or link to picture
    '''
    from MFramework.utils.utils import parseMention
    if emoji and "http" in emoji or ":" in emoji:
        if ':' in emoji and not emoji.startswith("http"):
            emoji_name, id = parseMention(emoji).split(":")
            from mdiscord import CDN_URL, CDN_Endpoints
            emoji = CDN_URL+CDN_Endpoints.Custom_Emoji.value.format(emoji_id=id)
        import requests
        icon = requests.get(emoji)
        if icon.ok:
            from binascii import b2a_base64
            emoji = {"icon":f"data:image/png;base64,{b2a_base64(icon.content).decode()}"}
    else:
        emoji = {"icon": "","unicode_emoji": emoji}
    await ctx.bot.modify_guild_role(guild_id=ctx.guild_id, role_id=role, **emoji)
    return "Icon changed"

@register(group=Groups.ADMIN, interaction=False)
async def nick(ctx: Context, nick: str):
    '''
    Changes bot nickname
    Params
    ------
    nick:
        New nickname
    '''
    await ctx.bot.modify_current_user_nick(ctx.guild_id, nick, reason=f"Request made by {ctx.user.username}")
