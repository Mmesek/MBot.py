from MFramework import register, Groups, Context, ChannelID, Snowflake


@register(group=Groups.MODERATOR, private_response=True)
async def say(ctx: Context, message: str, channel: ChannelID=None, *, language):
    '''
    Sends message as a bot
    Params
    ------
    message:
        Message to send
    channel:
        Channel to which message should be send
    '''
    msg = await ctx.bot.create_message(channel, message)
    await ctx.reply(f"Message sent.\nChannelID: {msg.channel_id}\nMessageID: {msg.id}", private=True)

@register(group=Groups.MODERATOR, private_response=True)
async def react(ctx: Context, reaction: str, message_id: Snowflake, channel: ChannelID=None, *, language):
    '''
    Reacts to a message as a bot
    Params
    ------
    reaction:
        Reaction(s) which should be used to react.
    message_id:
        Message to which bot should react
    channel:
        Use it if Message is in a different channel
    '''
    for each in reaction.split(','):
        await ctx.bot.create_reaction(channel, message_id, each.replace("<:", "").replace(">", "").strip())
    await ctx.reply("Reacted", private=True)
