from MFramework import (
    Bitwise_Permission_Flags,
    Context,
    Discord_Paths,
    Embed,
    Groups,
    Message,
    register,
)


@register(group=Groups.GLOBAL, private_response=True)
async def Bookmark(ctx: Context, message: Message) -> str:
    """Bookmark a moment in chat to save in your DMs for easy navigation"""
    await ctx.deferred(private=True)
    e = Embed(title="Your bookmark", description=message.content or None)
    e = message.attachments_as_embed(e)
    try:
        await ctx.send_dm(
            content=Discord_Paths.MessageLink.link.format(
                guild_id=ctx.guild_id, channel_id=message.channel_id, message_id=message.id
            ),
            embeds=[e],
        )
        return "Bookmarked in your DM successfully!"
    except:
        return "Couldn't send you a DM message!"


@register(group=Groups.GLOBAL)
async def Quote(ctx: Context, message: Message) -> Embed:
    """Quotes a message"""
    if any(
        Bitwise_Permission_Flags.check(None, int(i.deny), 2048)
        for i in list(filter(lambda x: x.id in ctx.member.roles + [ctx.guild_id], ctx.channel.permission_overwrites))
    ):
        await ctx.deferred(private=True)
        return await ctx.reply("Sorry, you can't use it here")
    await ctx.deferred()
    e = Embed()
    e = message.attachments_as_embed(e, title_attachments=None)
    e.setDescription(message.content)
    e.setTimestamp(message.timestamp)
    e.setAuthor(
        name=f"{message.author.username}#{message.author.discriminator}",
        url=Discord_Paths.MessageLink.link.format(
            guild_id=ctx.guild_id, channel_id=message.channel_id, message_id=message.id
        ),
        icon_url=message.author.get_avatar(),
    )
    e.setFooter(text=f"Quoted by {ctx.user.username}#{ctx.user.discriminator}")
    e.setColor("#3275a8")
    return e
