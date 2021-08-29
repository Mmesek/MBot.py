from MFramework import register, Context, Groups, Embed

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
async def aemoji(ctx: Context, emoji_name, *args,  **kwargs):
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
    await ctx.reply(message)


@register(group=Groups.ADMIN, interaction=False)
async def list_emoji(ctx: Context, *args,  all=False, regular=False, **kwargs):
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
    await ctx.reply(embeds=[e])


@register(group=Groups.ADMIN, interaction=False)
async def delete(ctx: Context, channel, *message,  **kwargs):
    '''Delete's message'''
    await ctx.bot.delete_message(channel, *message)

@register(group=Groups.ADMIN, interaction=False)
async def getmessages(ctx: Context, user, *args,  **kwargs):
    '''Retrives messages from DM'''
    dm = await ctx.bot.create_dm(user)
    messages = await ctx.bot.get_messages(dm.id)
    message = ""
    for each in messages:
        message += f"\n`[{each.timestamp[:19]}]` - `{each.author.username}`: {each.content}"
    e = Embed().setFooter("", f"DM ID: {dm.id}").setDescription(message[:2000])
    await ctx.reply(embeds=[e])

@register(group=Groups.ADMIN, interaction=False)
async def prunecount(ctx: Context, days=7, *args,  language, **kwargs):
    '''Shows prune count'''
    count = await ctx.bot.get_guild_prune_count(ctx.guild_id, days)
    await ctx.reply(count)