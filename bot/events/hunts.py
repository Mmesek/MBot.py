from datetime import datetime
from random import SystemRandom

random = SystemRandom()

from mdiscord import onDispatch, Message, Allowed_Mentions
from MFramework import Bot, log, Chance, Event
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
                x.emoji.name == reaction.split(':')[0], timeout=t)
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
        if ":" in reaction:
            reaction = f"<a:{reaction}>"
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

#@EventBetween(after_month=10, after_day=26, before_month=11, before_day=4)
@onDispatch(event="message_create")
@Event(month=10)
@Chance(1.5)
async def treat_hunt(ctx: Bot, data: Message):
    import random
    q = random.SystemRandom().randint(1,5)
    emoji = random.SystemRandom().choice(["🍬", "🧁", "🍭", "🍫", "🍪"])
    await _handle_reaction(ctx, data, emoji, "Halloween Treats", delete_own=False, first_only=False, logger="halloween_hunt", announce_msg=True, quantity=q)

#@EventBetween(after_month=10, after_day=28, before_month=11, before_day=4)
@onDispatch(event="message_create")
@Event(month=10)
@Chance(3)
async def fear_hunt(ctx: Bot, data: Message):
    import random
    q = random.SystemRandom().randint(10, 32)
    rq = random.SystemRandom().randint(1,5)
    emoji = random.SystemRandom().choice(["💀", "🕷", "🕸", "🦇", "🦴", "☠", "🕯", "👻"])
    await _handle_reaction(ctx, data, emoji, "Fear", _type=types.Item.Currency, delete_own=False, first_only=True, logger="halloween_hunt", announce_msg=True, quantity=q, require="Halloween Treats", require_quantity=rq)

@onDispatch(event="message_create")
@Event(month=11, day=5)
@Chance(7)
async def moka_hunt(ctx: Bot, data: Message):
    if data.guild_id == 289739584546275339:
        from random import SystemRandom as random
        if random().randint(1,10) <= 1:
            await _handle_reaction(ctx, data, "mokaFoil:905061222846697503", "Moka Treats", delete_own=False, first_only=True, logger="moka_hunt", announce_msg=True, quantity=10, statistic=types.Statistic.Spawned_GoldMoka)
        else:
            emoji = random().choice(['🐟', '🐔'])
            await _handle_reaction(ctx, data, emoji, "Moka Treats", delete_own=False, first_only=True, logger="moka_hunt", announce_msg=True, statistic=types.Statistic.Spawned_Moka)
