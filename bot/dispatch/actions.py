import re

from MFramework import *

async def responder(ctx: Bot, msg: Message, emoji: str):
    emoji = ctx.cache[msg.guild_id].custom_emojis.get(emoji.lower().strip(':'))
    if type(emoji) is str:
        await msg.reply(emoji)
    elif type(emoji) is tuple:
        await msg.reply(file=emoji[1], filename=emoji[0])


EMOJI = re.compile(r":\w+:")
@onDispatch(priority=4)
async def message_create(self: Bot, data: Message):
    if not data.is_empty:
        if any(i.id == self.user_id for i in data.mentions):
            await self.trigger_typing_indicator(data.channel_id)
        from .actions import responder
        for emoji in set(emoji.lower() for emoji in EMOJI.findall(data.content)):
            await responder(self, data, emoji)


from MFramework.utils.log import Message as LogMessage
class Message_Replay_QnA(LogMessage):
    username = None
    async def log(self, msg: Message) -> Message:
        rmsg = msg.referenced_message
        question = self.set_metadata(rmsg).setTitle("Question")
        question.author = None
        question.setColor("#45f913")
        question.setUrl(Discord_Paths.MessageLink.link.format(
            guild_id=rmsg.guild_id, channel_id=rmsg.channel_id, message_id=rmsg.id))
        self.user_in_footer(question, rmsg)
        if rmsg.attachments != []:
            question.setImage(url=rmsg.attachments[0].url)

        answer = self.set_metadata(msg).setTitle("Answer")
        answer.author = None
        answer.setColor("#ec2025")
        answer.setUrl(Discord_Paths.MessageLink.link.format(
            guild_id=msg.guild_id, channel_id=msg.channel_id, message_id=msg.id))
        self.user_in_footer(answer, msg)
        if msg.attachments != []:
            answer.setImage(url=msg.attachments[0].url)

        await self._log(None, embeds=[question, answer])


@onDispatch(event="message_create")
async def parse_reply(self: Bot, data: Message):
    from MFramework.commands._utils import detect_group, Groups
    _g = detect_group(self, data.author.id, data.guild_id, data.member.roles)
    if data.referenced_message == None or data.referenced_message.id == 0:
        return
    if _g >= Groups.MODERATOR:
        return
    channel = self.cache[data.guild_id].threads.get(data.channel_id, data.channel_id)
    if channel == 686371597895991327:
        return await dm_reply(self, data)
    if channel != 802092364008783893:
        return
    await self.cache[data.guild_id].logging["message_replay_qna"](data)

async def dm_reply(ctx: Bot, msg: Message):
    from MFramework.utils.utils import parseMention
    if len(msg.referenced_message.embeds) == 0:
        return
    user = parseMention(msg.referenced_message.embeds[0].footer.text)
    dm = await ctx.create_dm(user)
    try:
        await ctx.create_message(dm.id, msg.content or None, embeds=msg.attachments_as_embed())
    except Exception as ex:
        return await msg.react(ctx.emoji["failure"])
    await msg.react(ctx.emoji['success']) # _Client is apparently not set


@onDispatch(event="message_create", priority=5)
async def deduplicate_messages(self: Bot, data: Message) -> bool:
    c = self.cache[data.guild_id].last_messages
    from MFramework.commands._utils import detect_group
    _g = detect_group(self, data.author.id, data.guild_id, data.member.roles)
    if _g.can_use(Groups.MODERATOR):
        return
    _last_message = c.get(data.channel_id, None)
    if (_last_message and 
        _last_message[0].content == data.content and 
        _last_message[0].author.id == data.author.id and
        _last_message[0].attachments == data.attachments and
        _last_message[0].referenced_message == data.referenced_message
        ):
        if len(_last_message) >= self.cache[data.guild_id].allowed_duplicated_messages:
            log.debug('Deleting Message "%s" because of being duplicate', data.content)
            await data.delete(reason="Duplicate Message")
            return True
    else:
        self.cache[data.guild_id].last_messages[data.channel_id] = []
    self.cache[data.guild_id].last_messages[data.channel_id].append(data)# = data
    return False

@onDispatch(event="message_create", priority=5)
async def deduplicate_across_channels(self: Bot, data: Message) -> bool:
    c = self.cache[data.guild_id].last_messages
    for _msg in c.values():
        if (_msg[0].channel_id != data.channel_id and
            _msg[0].content == data.content and
            _msg[0].author.id == data.author.id and
            _msg[0].attachments == data.attachments and
            _msg[0].referenced_message == data.referenced_message
        ):
            log.debug('Deleting Message "%s" because of being duplicate across channels', data.content)
            await data.delete(reason="Duplicate Message across channels")
            return True
    return False


URL_PATTERN = re.compile(r"https?:\/\/.*\..*")
@onDispatch(event="message_create", priority=4)
async def remove_links(self: Bot, data: Message) -> bool:
    if len(data.member.roles) > 0 and any(self.cache[data.guild_id].roles.get(i, Role()).color for i in data.member.roles):
        return False
    cache = self.cache[data.guild_id]
    if URL_PATTERN.search(data.content):
        violations = cache.msgs_violating_link_filter
        VIOLATIONS_COUNT = 3
        if cache.last_violating_user != data.author.id:
            violations = set()
            cache.last_violating_user = data.author.id
        log.debug('Deleting Message "%s" because of matching URL filter', data.content)
        await data.delete(reason="URL and user doesn't have colored Roles")
        violations.add(data.id)
        dm = await self.create_dm(data.author.id)
        if len(violations) > (VIOLATIONS_COUNT - 1):
            log.debug('Kicking user %s because of amount of msgs violating link filter', data.author.id)
            cache.last_violating_user = None
            try:
                await self.create_message(dm.id, f"You've been kicked from {self.cache[data.guild_id].guild.name} server due to being flagged as hijacked account (You have sent multiple links without having colored role). Feel free to return once you get your account back and/or change password")
            except:
                pass
            await self.remove_guild_member(data.guild_id, data.author.id, "Hijacked account")
            from ..commands_slash.infractions import InfractionTypes
            await self.cache[data.guild_id].logging["infraction"](
                guild_id=data.guild_id,
                channel_id=data.channel_id,
                message_id=data.id,
                moderator=self.cache[data.guild_id].bot.user,
                user_id=data.author.id,
                reason="Hijacked Account",
                duration=None,
                type=InfractionTypes.Kick
            )
            return True
        try:
            embed = Embed().setDescription(data.content).setTitle("Message").setColor("#d10a2b")
            await self.create_message(dm.id, f"Hey, we do not allow sending links by people without colored role. Be more active to gain colored role before attempting to do so again (Violations before being flagged as hijacked account: {len(violations)}/{VIOLATIONS_COUNT})\n\n**[THIS IS AUTOMATED MESSAGE. NO NEED TO RESPOND** *(Please don't reply to this message)* **]**", embeds=[embed])
        except:
            pass
        return True

REPLACE_NOT_APLABETIC = re.compile(r'[^a-zA-Z ]')
@onDispatch(event="message_create", priority=10)
async def blocked_words(self: Bot, data: Message) -> bool:
    BLACKLISTED_WORDS = self.cache[data.guild_id].blacklisted_words #re.compile(r"") #TODO: Source cached from Database!
    if BLACKLISTED_WORDS:
        if BLACKLISTED_WORDS.search(REPLACE_NOT_APLABETIC.sub('', data.content)):
            log.debug('Deleting Message "%s" because of matching blocked words filter', data.content)
            await data.delete(reason="Blocked Words")
            return True

ACTION = re.compile(r"(?:(?=\*)(?<!\*).+?(?!\*\*)(?=\*))")
ILLEGAL_ACTIONS = re.compile(r"(?i)zabij|wyryw|mord")
@onDispatch(event="message_create")
async def roll_dice(self: Bot, data: Message, updated: bool = False):
    channel = self.cache[data.guild_id].threads.get(data.channel_id, data.channel_id)
    if channel not in self.cache[data.guild_id].rpg_channels:
        return
    if updated:
        m = await self.get_channel_message(data.channel_id, data.id)
        if m.reactions:
            return
    DICE_REACTIONS = ['0️⃣','1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣']
    DICE_EMOJIS = {0:'dice_0:761760091648294942',
        1:'dice_1:761760091971780628',2:'dice_2:761760091837825075',3:'dice_3:761760092206792750',
        4:'dice_4:761760092767911967',5:'dice_5:761760093435068446',6:'dice_6:761760093817143345'}
    reg = ACTION.findall(data.content)
    if reg and set(reg) != {'*'}:
        if '*' in reg:
            reg = set(reg)
            reg.remove('*')
            reg = list(reg)
        dices = self.cache[data.guild_id].rpg_dices or DICE_REACTIONS
        from random import SystemRandom as random
        v = random().randint(1, 6) if not ILLEGAL_ACTIONS.findall(reg[0]) else 0
        await self.create_reaction(data.channel_id, data.id, dices[v])


TIME_PATTERN = re.compile(r"(?P<Hour>\d\d?) ?(:|\.)? ?(?P<Minute>\d\d?)? ?(?P<Daytime>AM|PM)? ?(?P<LateMinute>\d\d?)? ?(?P<Timezone>\w+)")
#@onDispatch(event="message_create")
async def check_timezone(self: Bot, data: Message):
    match = TIME_PATTERN.search(data.content)
    if not match:
        return
    timezone = match.group("Timezone")
    import pytz
    if timezone.lower() not in pytz.all_timezones_set:
        timezone = 'utc' # TODO: Get from DB from User setting OR Server's default
    hour = match.group("Hour")
    minute = match.group("Minute") or match.group("LateMinute")
    daytime = match.group("Daytime")


@onDispatch(event="message_create")
async def delete_non_spoilers(self: Bot, data: Message):
    if (
        "spoiler" in self.cache[data.guild_id].channels.get(data.channel_id, Channel()).name
        and "delete" in self.cache[data.guild_id].channels.get(data.channel_id, Channel()).topic
        and (
            not data.content
            and not all(attachment.filename.startswith("SPOILER") for attachment in data.attachments)
            or (data.content and not data.content.startswith("||") and not data.content.endswith("||"))
        )
    ):
        await data.delete(reason="Message is not surrounded with spoilers")


@onDispatch(event="message_delete", priority=1)
async def ghost_ping(self: Bot, data: Message_Delete):
    msg: Message = self.cache[data.guild_id].messages[f"{data.guild_id}.{data.channel_id}.{data.id}"]
    if msg:
        mentions = ", ".join([f"<@{user.id}>" for user in msg.mentions if user.id != msg.author.id])
        if mentions:
            await self.create_message(data.channel_id, f"Looking for a Ping? <:ping:517493248529530890> Detected Ghostping of {mentions} by <@{msg.author.id}>", allowed_mentions=None)
