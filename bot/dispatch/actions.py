from MFramework import *
from ..database import types
async def _handle_reaction(ctx: Bot, data: Message, reaction: str, name: str, 
                    _type: types.Item=types.Item.Event, 
                    delete_own: bool=True, first_only: bool=False, 
                    logger: str=None, statistic: types.Statistic=None, announce_msg: bool = False,
                    quantity: int = 1,
                    require: str = None, require_quantity: int = 1):
    import random, asyncio
    log.debug("Spawning reaction with %s", name)
    await data.typing()
    await asyncio.sleep(random.SystemRandom().randint(0, 10))
    await data.react(reaction)
    t = random.SystemRandom().randint(15, 60)
    if first_only:
        try:
            user = await ctx.wait_for("message_reaction_add", check=lambda x: 
                x.channel_id == data.channel_id and 
                x.message_id == data.id and 
                x.user_id != ctx.user_id and
                x.emoji.name == reaction, timeout=t)
        except asyncio.TimeoutError:
            log.debug("No one reacted. Removing reaction")
            return await data.delete_reaction(reaction)
    else:
        await asyncio.sleep(t)

    if delete_own:
        await data.delete_reaction(reaction)
    
    s = ctx.db.sql.Session()
    
    from ..database import models, Statistic
    if statistic:
        year = models.User.fetch_or_add(s, id=datetime.now().year)
        Statistic.increment(s, server_id=data.guild_id, user_id=datetime.now().year, name=statistic)
    if not first_only:
        users = await data.get_reactions(reaction)
    else:
        users = [user]
    
    from ..database import items
    if require:
        required_item = items.Item.fetch_or_add(s, name=require)

    item = items.Item.fetch_or_add(s, name=name, type=_type)
    claimed_by = []
    not_enough = []
    for _user in users:
        uid = getattr(_user, 'id', None) or getattr(_user, 'user_id')
        u = models.User.fetch_or_add(s, id=uid)
        has = False
        if require:
            required_inv = items.Inventory(required_item, quantity=require_quantity)
            has = next(filter(lambda x: x.item_id == required_item.id and x.quantity >= required_inv.quantity, u.items), None)
        else:
            has = True
        if not has:
            not_enough.append(u.id)
            if require and next(filter(lambda x: x.item_id == item.id and x.quantity >= quantity, u.items), False):
                u.remove_item(required_inv)
            continue
        i = items.Inventory(item, quantity)
        t = u.claim_items(data.guild_id, [i])
        if require:
            u.remove_item(required_inv, transaction=t)
        s.add(t)
        claimed_by.append(u.id)
    if not claimed_by and not_enough:
        users = ", ".join([f"<@{i}>" for i in not_enough])
        result = f"{users} didn't have enough candies ({require_quantity}) and ran away scared"
        if quantity:
            result += f" losing {quantity} fear"
        result += "!"
        await data.reply(result)
        return
    await ctx.cache[data.guild_id].logging[logger](data, users)
    s.commit()
    if announce_msg and claimed_by:
        # TODO If it's not first-only, there should be some additional logic to get list
        users = ", ".join([f"<@{i}>" for i in claimed_by])
        result= f"{users} got {reaction} {item.name}"
        if quantity > 1:
            result += f" x {quantity}"
        if require:
            result += f" for {required_item.emoji} {required_item.name}"
            if require_quantity > 1:
                result += f" x {require_quantity}" 
        result += "!"
        #if require and not_enough:
        #    result+=" Rest didn't have enough and ran away scared!"
        await data.reply(result, allowed_mentions=Allowed_Mentions())

from MFramework.commands.decorators import Event, Chance, EventBetween
@onDispatch(event="message_create")
@Event(month=4)
@Chance(2.5)
async def egg_hunt(ctx: Bot, data: Message):
    await _handle_reaction(ctx, data, "🥚", "Easter Egg", logger="egg_hunt", statistic=types.Statistic.Spawned_Eggs)

@onDispatch(event="message_create")
@Event(month=12)
@Chance(3)
async def present_hunt(ctx: Bot, data: Message):
    await _handle_reaction(ctx, data, "🎁", "Present", delete_own=False, first_only=True, logger="present_hunt", statistic=types.Statistic.Spawned_Presents)

@onDispatch(event="message_create")
@Event(month=12)
@Chance(10)
async def snowball_hunt(ctx: Bot, data: Message):
    await _handle_reaction(ctx, data, "❄", "Snowball", delete_own=False, first_only=True, logger="snowball_hunt", statistic=types.Statistic.Spawned_Snowballs)

@onDispatch(event="message_create")
@Event(month=10)
@Chance(1)
async def halloween_hunt(ctx: Bot, data: Message):
    await _handle_reaction(ctx, data, "🎃", "Pumpkin", delete_own=False, first_only=True, logger="halloween_hunt", statistic=types.Statistic.Spawned_Pumpkins, announce_msg=True)

@onDispatch(event="message_create")
@EventBetween(after_month=10, after_day=26, before_month=11, before_day=4)
@Chance(2)
async def treat_hunt(ctx: Bot, data: Message):
    import random
    q = random.SystemRandom().randint(1,5)
    emoji = random.SystemRandom().choice(["🍬", "🧁", "🍭", "🍫", "🍪"])
    await _handle_reaction(ctx, data, emoji, "Halloween Treats", delete_own=False, first_only=False, logger="halloween_hunt", announce_msg=True, quantity=q)

@onDispatch(event="message_create")
@EventBetween(after_month=10, after_day=28, before_month=11, before_day=4)
@Chance(4)
async def fear_hunt(ctx: Bot, data: Message):
    import random
    q = random.SystemRandom().randint(10, 32)
    rq = random.SystemRandom().randint(1,5)
    emoji = random.SystemRandom().choice(["💀", "🕷", "🕸", "🦇", "🦴", "☠", "🕯", "👻"])
    await _handle_reaction(ctx, data, emoji, "Fear", _type=types.Item.Currency, delete_own=False, first_only=True, logger="halloween_hunt", announce_msg=True, quantity=q, require="Halloween Treats", require_quantity=rq)

@onDispatch(event="message_create")
@Event(month=11, day=5)
@Chance(10)
async def moka_hunt(ctx: Bot, data: Message):
    if data.guild_id == 289739584546275339:
        from random import SystemRandom as random
        if random.randint(1,10) <= 3:
            await _handle_reaction(ctx, data, "mokahide:841299054058405968", "Moka Treats", delete_own=False, first_only=True, logger="moka_hunt", statistic=types.Statistic.Spawned_Moka, announce_msg=True, quantity=10)
        else:
            await _handle_reaction(ctx, data, "", "Moka Treats", delete_own=False, first_only=True, logger="moka_hunt", statistic=types.Statistic.Spawned_MokaTreats, announce_msg=True)

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
            await self.cache[data.guild_id].logging["infraction"](
                guild_id=data.guild_id,
                channel_id=data.channel_id,
                message_id=data.id,
                moderator=self.cache[data.guild_id].bot.user,
                user_id=data.author.id,
                reason="Hijacked Account",
                duration=None,
                type=types.Infraction.Kick
            )
            return True
        try:
            await self.create_message(dm.id, f"Hey, we don't allow sending links by people without colored role. Be more active to gain colored role before attempting to do so again (Violations before being flagged as hijacked account: {len(violations)}/{VIOLATIONS_COUNT})")
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
