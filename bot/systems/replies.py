from MFramework import Discord_Paths, Message, onDispatch
from MFramework.commands._utils import Groups, detect_group
from MFramework.utils.log import Message as LogMessage
from MFramework.utils.utils import parseMention

from bot import Bot


class Message_Replay_QnA(LogMessage):
    username = None

    async def log(self, msg: Message) -> Message:
        rmsg = msg.referenced_message
        question = self.set_metadata(rmsg).setTitle("Question")
        question.author = None
        question.setColor("#45f913")
        question.setUrl(
            Discord_Paths.MessageLink.link.format(guild_id=msg.guild_id, channel_id=rmsg.channel_id, message_id=rmsg.id)
        )
        self.user_in_footer(question, rmsg)
        if rmsg.attachments != []:
            question.setImage(url=rmsg.attachments[0].url)

        answer = self.set_metadata(msg).setTitle("Answer")
        answer.author = None
        answer.setColor("#ec2025")
        answer.setUrl(
            Discord_Paths.MessageLink.link.format(guild_id=msg.guild_id, channel_id=msg.channel_id, message_id=msg.id)
        )
        self.user_in_footer(answer, msg)
        if msg.attachments != []:
            answer.setImage(url=msg.attachments[0].url)

        await self._log(None, embeds=[question, answer])


@onDispatch(event="message_create")
async def parse_reply(self: Bot, data: Message):
    _g = detect_group(self, data.author.id, data.guild_id, data.member.roles)
    if not data.referenced_message or data.referenced_message.id == 0:
        return
    if not _g.can_use(Groups.MODERATOR):
        return
    channel = self.cache[data.guild_id].threads.get(data.channel_id, data.channel_id)
    if channel == 686371597895991327:
        return await dm_reply(self, data)
    if channel != 802092364008783893:
        return
    await self.cache[data.guild_id].logging["message_replay_qna"](data)


async def dm_reply(ctx: Bot, msg: Message):
    if len(msg.referenced_message.embeds) == 0:
        return
    user = parseMention(msg.referenced_message.embeds[0].footer.text)
    dm = await ctx.create_dm(user)
    try:
        await ctx.create_message(dm.id, msg.content or None, embeds=msg.attachments_as_embed())
    except Exception as ex:
        return await msg.react(ctx.emoji["failure"])
    await msg.react(ctx.emoji["success"])  # _Client is apparently not set
