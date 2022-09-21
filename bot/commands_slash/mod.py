from mdiscord.exceptions import BadRequest
from MFramework import (
    ChannelID,
    Context,
    Embed,
    Groups,
    Message_Reference,
    Snowflake,
    register,
)
from MFramework.commands.components import Modal, Row, TextInput


@register(group=Groups.MODERATOR, private_response=True)
async def say(
    ctx: Context,
    message: str,
    channel: ChannelID = None,
    edit: Snowflake = None,
    reply: str = None,
    skip_message: bool = False,
    title: str = None,
    description: str = None,
    footer: str = None,
    footer_icon: str = None,
    author: str = None,
    author_icon: str = None,
    author_url: str = None,
    url: str = None,
    image: str = None,
    thumbnail: str = None,
    color: str = None,
    left_name: str = None,
    left_text: str = None,
    middle_name: str = None,
    middle_text: str = None,
    right_name: str = None,
    right_text: str = None,
):
    """
    Sends message as a bot
    Params
    ------
    message:
        Message to send
    channel:
        Channel to which message should be send
    edit:
        ID of bot's message to edit
    reply:
        ID or link to message to which is should reply to
    skip_message:
        Whether Message should not be sent (Set if you want to only send embed)
    title:
        Title of an Embed
    description:
        Description of an Embed
    footer:
        Footer text of an Embed
    footer_icon:
        URL to an icon used as footer icon (Bottom left)
    image:
        URL to an image used as main image ("Main" picture)
    thumbnail:
        URL to an image used as thumbnail (Top right)
    author:
        Text above Title
    author_url:
        URL available after clicking author's text (Requires Author)
    author_icon:
        URL to an image used as author icon (Small Top Left)
    url:
        URL available after clicking title's text. (Requires Title)
    color:
        Color of an embed. Value in hexadecimal notation. For example: #00aaff
    left_name:
        Name of Field on the left
    left_text:
        Text of Field on the left
    middle_name:
        Name of Field on the middle
    middle_text:
        Text of Field on the middle
    right_name:
        Name of Field on the right
    right_text:
        Text of Field on the right
    """
    if reply:
        if "/" in reply:
            message_id = reply.split("/")[-1]
        else:
            message_id = reply
        reply = Message_Reference(message_id=message_id, channel_id=channel, guild_id=ctx.guild_id)
    e = Embed()
    if title:
        e.setTitle(title or "")
    if description:
        e.setDescription(description or "")
    if color:
        e.setColor(color)
    if footer or footer_icon:
        e.setFooter(text=footer or "", icon_url=footer_icon)
    if image:
        e.setImage(url=image)
    if thumbnail:
        e.setThumbnail(url=thumbnail)
    if author or author_icon or (author_url and author):
        e.setAuthor(name=author or "", url=author_url, icon_url=author_icon)
    if url and title:
        e.setUrl(url=url)
    if any([left_name, left_text, middle_name, middle_text, right_name, right_text]):
        e.addField(name=left_name or "\u200b", value=left_text or "\u200b", inline=True)
        if middle_name or middle_text:
            e.addField(name=middle_name or "\u200b", value=middle_text or "\u200b", inline=True)
        if right_name or right_text:
            e.addField(name=right_name or "\u200b", value=right_text or "\u200b", inline=True)
    try:
        if edit and ctx.permission_group.can_use(Groups.ADMIN):
            msg = await ctx.bot.get_channel_message(channel, edit)
            if message and not skip_message:
                msg.content = message
            if e and e.total_characters - 8:
                if len(msg.embeds) > 0:
                    msg.embeds.append(e)
                else:
                    msg.embeds = [e]
            if reply:
                msg.message_reference = reply
            await msg.edit()
        else:
            msg = await ctx.bot.create_message(
                channel_id=channel,
                content=message if not skip_message else "",
                embeds=[e] if e.total_characters - 8 else None,
                message_reference=reply,
            )
        return f"Message sent.\nChannelID: {msg.channel_id}\nMessageID: {msg.id}"
    except BadRequest as ex:
        return ex.msg or f"Exception: {ex}"
    except Exception as ex:
        return f"Exception occured: {ex}"


class Long_Message(Modal):
    private_response = True

    @classmethod
    async def execute(cls, ctx: Context, data: str, inputs: dict[str, str]):
        return await say(ctx, inputs["message"], ctx.channel_id, None if data == "None" else data)


@register(group=Groups.MODERATOR, private_response=True, auto_defer=False)
async def say_long(ctx: Context, message_id: Snowflake = None):
    """Shows Modal to send a multilined message as a bot"""
    if message_id:
        msg = await ctx.bot.get_channel_message(ctx.channel_id, message_id)
        content = msg.content
    else:
        content = None

    return Long_Message(
        Row(
            TextInput(
                label="Your Message",
                custom_id="message",
                min_length=1,
                required=True,
                value=content,
                placeholder="Message to send",
            )
        ),
        title="Multiline Message",
        custom_id=message_id,
    )


@register(group=Groups.MODERATOR, private_response=True)
async def react(ctx: Context, reaction: str, message_id: Snowflake, channel: ChannelID = None, *, language):
    """
    Reacts to a message as a bot
    Params
    ------
    reaction:
        Reaction(s) which should be used to react.
    message_id:
        Message to which bot should react
    channel:
        Use it if Message is in a different channel
    """
    for each in reaction.split(","):
        await ctx.bot.create_reaction(channel, message_id, each.replace("<:", "").replace(">", "").strip())
    await ctx.reply("Reacted", private=True)
