from typing import List

from MFramework import register, Groups, Context, UserID, Snowflake, onDispatch, Bot, Message, Channel_Types
from MFramework.utils.log import Message as MessageLog
from MFramework.commands.components import Select, Select_Option

@register(group=Groups.MODERATOR)
async def dm(ctx: Context, user: UserID, message: str, *, language):
    '''
    DMs user with specified message
    Params
    ------
    user:
        User to which Message should be send
    message:
        Message to send
    '''
    try:
        dm = await ctx.bot.create_dm(user)
        msg = await ctx.bot.create_message(dm.id, message)
        msg.author = ctx.user
        log = ctx.cache.logging["direct_message"]
        if not log:
            return
        e = log._create_embed(msg)
        e.setColor("#0fc130")
        threads = {v: k for k, v in ctx.cache.dm_threads.items()}
        thread_id = threads.get(user, None)
        await log._log(content=f"This message has been sent to <@!{int(user)}>", embeds=[e], username=f"{ctx.user.username}#{ctx.user.discriminator}", avatar=ctx.user.get_avatar(), thread_id=thread_id)
        if ctx.is_interaction:
            await ctx.reply(f"Message sent.\nChannelID: {dm.id}\nMessageID: {msg.id}", private=True)
    except Exception as ex:
        await ctx.reply("Couldn't Deliver message to specified user.", private=True)


@onDispatch(event="message_create")
async def dm_thread(ctx: Bot, msg: Message):
    from MFramework.commands._utils import detect_group
    channel = ctx.cache[msg.guild_id].threads.get(msg.channel_id, msg.channel_id)
    if channel != 686371597895991327:
        return
    _g = detect_group(ctx, msg.author.id, msg.guild_id, msg.member.roles)
    if _g > Groups.MODERATOR:
        return
    user_id = ctx.cache[msg.guild_id].dm_threads.get(msg.channel_id, None)
    if user_id:
        dm = await ctx.create_dm(user_id)
        try:
            await ctx.create_message(dm.id, msg.content or None, embeds=msg.attachments_as_embed())
            return await msg.react(ctx.emoji["success"])
        except:
            return await msg.react(ctx.emoji["failure"])


class Direct_Message(MessageLog):
    def __init__(self, bot: Bot, guild_id: Snowflake, type: str, id: Snowflake, token: str) -> None:
        self.channel_id = None
        super().__init__(bot, guild_id, type, id, token)

    async def get_wh_channel(self):
        webhook = await self.bot.get_webhook_with_token(self.webhook_id, self.webhook_token)
        self.channel_id = webhook.channel_id

    def _create_embed(self, msg: Message):
        embed = self.set_metadata(msg)
        avatar = msg.author.get_avatar()
        embed.author.icon_url = None
        embed.footer.icon_url = avatar
        embed.footer.text = msg.author.id
        embed = msg.attachments_as_embed(embed)
        return embed

    async def log(self, msg: Message) -> Message:
        embed = self._create_embed(msg)
        avatar = embed.footer.icon_url
        embed.setColor(self.bot.cache[self.guild_id].color)
        canned = self.bot.cache[self.guild_id].canned

        from mlib.localization import tr
        if (len(set(msg.content.lower().split(' '))) < 2) and len(msg.attachments) == 0:
            return await msg.reply(tr("commands.dm.singleWordError", self.bot.cache[self.guild_id].language, emoji_success=self.bot.emoji['success']))

        if msg.channel_id in self.bot.cache[0]:
            s = list(self.bot.cache[0][msg.channel_id].keys())
            if (self.bot.cache[0][msg.channel_id][s[-1]].content == msg.content and
                self.bot.cache[0][msg.channel_id][s[-1]].attachments == msg.attachments
                ):
                return await msg.reply(tr("commands.dm.sameMessageError", self.bot.cache[self.guild_id].language))

        import re
        reg = re.search(canned['patterns'], msg.content)
        content = ''
        if reg and reg.lastgroup is not None:
            await msg.reply(canned['responses'][reg.lastgroup])
            content = tr("commands.dm.cannedResponseSent", self.bot.cache[self.guild_id].language, name=reg.lastgroup)
        threads = {v: k for k, v in self.bot.cache[self.guild_id].dm_threads.items()}
        thread_id = threads.get(msg.author.id, None)
        embeds = []
        if thread_id is None:
            if not self.channel_id:
                await self.get_wh_channel()
            thread = await self.bot.start_thread_without_message(channel_id=self.channel_id, name=f"{msg.author.username} - {msg.author.id}", type= Channel_Types.GUILD_PUBLIC_THREAD, reason="Received DM from new user")
            try:
                from copy import copy
                _msg = copy(msg)
                _msg.guild_id = self.guild_id
                _msg.channel_id = thread.id
                _msg.id = None
                _msg.member = self.bot.cache[self.guild_id].members.get(msg.author.id)
                ctx = Context(self.bot.cache, self.bot, _msg)
                from .info import user
                await user(ctx)
            except:
                pass
            thread_id = thread.id
            self.bot.cache[self.guild_id].dm_threads[thread_id] = msg.author.id
            past_messages = await self.bot.get_channel_messages(msg.channel_id, before=msg.id, limit=15)
            if past_messages:
                _past_messages = []
                for _msg in past_messages:
                    if not _msg.content and len(_msg.attachments):
                        _msg.content = f"[Attachments: {len(_msg.attachments)}]"
                    elif not _msg.content and len(_msg.stickers):
                        _msg.content = f"[Stickers: {len(_msg.stickers)}]"
                    _past_messages.append((f"<t:{int(_msg.timestamp.timestamp())}:R>", _msg.author.username, _msg.content))
                from MFramework import Embed
                _past_messages = "\n".join("[{}] [**`{}`**]: {}".format(i[0], i[1], i[2]) for i in reversed(_past_messages))
                embeds.append(Embed(title=f"Previous messages (#{len(past_messages)})").setDescription(_past_messages).setColor("#646363"))
            #for moderator in filter(lambda x: self.channel_id in x["moderated_channels"], self.bot.cache[self.guild_id].moderators):
            #    await self.bot.add_thread_member(thread_id, moderator, "Added User to DM thread")
        embeds.append(embed)
        msg_links = re.findall(rf"https:\/\/discord\.com\/channels\/{self.guild_id}\/(\d+)\/(\d+)", msg.content)
        if msg_links:
            for channel_id, message_id in msg_links[:5]:
                linked_msg = await self.bot.get_channel_message(channel_id, message_id)
                linked = self._create_embed(linked_msg)
                linked.setColor("#068dd1")
                linked.addField("Channel", f"<#{channel_id}>")
                linked.setTitle("Referenced Message")
                embeds.append(linked)
        try:
            from MFramework.commands.components import Option, Row
            dm_components = [
                Row(
                    CannedResponses(
                        *[Option(label=k, value=v, description=v) for k, v in canned["responses"].items()][:25],
                        custom_id=msg.channel_id,
                        placeholder="Send Canned Response"
                    )
                )
            ]
            await self._log(content=content+f' <@!{msg.author.id}>', embeds=embeds, username=f"{msg.author.username}#{msg.author.discriminator}", avatar=avatar, thread_id=thread_id, components=dm_components)
            await msg.react(self.bot.emoji['success'])
        except:
            await msg.react(self.bot.emoji["failure"])
    async def _log(self, content: str = "", embeds = None, components = None, *, username: str = None, avatar: str = None, thread_id = None, wait: bool = None):
        return await self.bot.create_message(thread_id, content=content, embeds=embeds, components=components)

class CannedResponses(Select):
    private_response = False
    @classmethod
    async def execute(cls, ctx: Context, data: str, values: List[str], not_selected: List[Select_Option]):
        ctx.data.message._Client = ctx.bot
        ctx.data.message.components = []
        await ctx.data.message.edit()
        msg = await ctx.bot.create_message(data, values[0])
        log = ctx.cache.logging["direct_message"]
        if not log:
            return
        msg.author = ctx.user
        e = log._create_embed(msg)
        e.setColor("#ff8f00")
        await ctx.reply(embeds=[e])
