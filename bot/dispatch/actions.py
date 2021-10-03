from MFramework import *
from ..database import types
async def _handle_reaction(ctx: Bot, data: Message, reaction: str, name: str, _type: types.Item=types.Item.Event, 
                    wait: bool=True, delete_own: bool=True, store_in_cache: bool=False, first_only=False, all_reactions: bool=True, 
                    logger: str=None, statistic: types.Statistic=None):
    import random, asyncio
    log.debug("Spawning reaction with %s", name)
    await asyncio.sleep(random.SystemRandom().randint(0, 10))
    await data.react(reaction)
    t = random.SystemRandom().randint(15, 60)
    #if store_in_cache:
    #    ctx.cache[data.guild_id].special_message.store(data, expire=t, type=name, first_only=first_only)
    #if not wait and not statistic:
    #    return
    #await asyncio.sleep(t)
    try:
        user = await ctx.wait_for("message_reaction_add", check=lambda x: 
            x.channel_id == data.channel_id and 
            x.message_id == data.id and 
            x.user_id != ctx.user_id and
            x.emoji.name == reaction, timeout=t)
    except asyncio.TimeoutError:
        log.debug("No one reacted. Removing reaction")
        return await data.delete_reaction(reaction)

    if delete_own:
        await data.delete_reaction(reaction)
    
    #if store_in_cache:
    #    ctx.cache[data.guild_id].special_message.delete(data.id) #Not needed thanks to expire flag
    
    s = ctx.db.sql.Session()
    
    from ..database import models, Statistic
    if statistic:
        Statistic.increment(s, server_id=data.guild_id, user_id=datetime().year, name=statistic)
    if all_reactions:
        users = await data.get_reactions(reaction)
    else:
        users = [user]
    
    from ..database import items
    item = items.Item.fetch_or_add(s, name=name, type=_type)
    i = items.Inventory(item)
    for user in users:
        u = models.User.fetch_or_add(s, id=user.id)
        u.claim_items(data.guild_id, [i])
        #user.add_item(s, data.guild_id, user.id, item=i)
        #Log.claim(data.guild_id, user.id, _type)
    await ctx.cache[data.guild_id].logging[logger](data, users)
    s.commit()

from MFramework.commands.decorators import Event, Chance
@onDispatch(event="message_create")
@Event(month=4)
@Chance(2.5)
async def egg_hunt(ctx: Bot, data: Message):
    await _handle_reaction(ctx, data, "🥚", "Easter Egg", types.Item.Event, logger="egg_hunt", statistic=types.Statistic.Spawned_Eggs)

@onDispatch(event="message_create")
@Event(month=12)
@Chance(3)
async def present_hunt(ctx: Bot, data: Message):
    await _handle_reaction(ctx, data, "🎁", "Present", wait=False, delete_own=False, store_in_cache=True, first_only=True, all_reactions=False, logger="present_hunt", statistic=types.Statistic.Spawned_Presents)

@onDispatch(event="message_create")
@Event(month=10)
@Chance(1)
async def halloween_hunt(ctx: Bot, data: Message):
    await _handle_reaction(ctx, data, "🎃", "Pumpkin", wait=False, delete_own=False, store_in_cache=True, first_only=True, all_reactions=False, logger="halloween_hunt", statistic=types.Statistic.Spawned_Pumpkins)

async def responder(ctx: Bot, msg: Message, emoji: str):
    emoji = ctx.cache[msg.guild_id].custom_emojis.get(emoji.lower().strip(':'))
    if type(emoji) is str:
        await msg.reply(emoji)
    elif type(emoji) is tuple:
        await msg.reply(file=emoji[1], filename=emoji[0])

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

import re
URL_PATTERN = re.compile(r"https?:\/\/.*\..*")
@onDispatch(event="message_create", priority=10)
async def remove_links(self: Bot, data: Message) -> bool:
    if len(data.member.roles) > 0 and any(self.cache[data.guild_id].roles.get(i, Role()).color for i in data.member.roles):
        return False
    if URL_PATTERN.search(data.content):
        log.debug('Deleting Message "%s" because of matching URL filter', data.content)
        await data.delete(reason="URL and user doesn't have colored Roles")
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

@onDispatch(event="message_create")
async def handle_level(self: Bot, data: Message):
    if data.channel_id not in self.cache[data.guild_id].disabled_channels and not any(r in data.member.roles for r in self.cache[data.guild_id].disabled_roles):
        from ..utils import levels
        await levels.exp(self, data)


TIME_PATTERN = re.compile(r"(?P<Hour>\d\d?) ?(:|\.)? ?(?P<Minute>\d\d?)? ?(?P<Daytime>AM|PM)? ?(?P<LateMinute>\d\d?)? ?(?P<Timezone>\w+)")
@onDispatch(event="message_create")
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
