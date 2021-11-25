from random import SystemRandom as random

from MFramework import Context, Groups, register, Event, User, Embed
from MFramework.commands.cooldowns import cooldown
from ...database import items, models, types

from MFramework.commands._utils import Error
class SnowballError(Error):
    pass

@register(group=Groups.GLOBAL)
@Event(month=12)
async def snowball(ctx: Context) -> Embed:
    '''Snowball throwing event commands'''
    e = Embed()
    e.setTitle("Winter Snowballs Minigame")
    e.addField(
        name="Attributions",
        value="OG version was made by Chrisoman#8561 (Or at least I've got flowchart about it from him)"
    )

@register(group=Groups.GLOBAL, main=snowball)
@Event(month=12)
@cooldown(minutes=3)
async def throw(ctx: Context, target: User):
    '''
    Throw a snowball at someone!
    Params
    ------
    target:
        user to throw to
    '''
    s = ctx.db.sql.session()
    user = models.User.fetch_or_add(s, id=ctx.user_id)
    snowballs = next(filter(lambda x: x.item.name == "Snowball", user.items), None)
    if not snowballs:
        raise SnowballError("Sorry, you don't have any snowballs! Gather some firstly!")

    msgs = await ctx.bot.get_channel_messages(ctx.channel_id, limit=5)
    user_msg = next(filter(lambda x: x.author.id == target.id, msgs), None)
    if user_msg:
        item = items.Inventory(items.Item.by_name(s, "Snowball"))
        transaction = user.transfer(ctx.guild_id, target.id, [item]) 
        #FIXME: Right now it only transfers snowball,
        # adding a method that "turns" item in transit (Sent A, Received B)
        # would be a possible solution for this [There was something similiar for gifting 2020]
        s.add(transaction)

        return f"<@{ctx.user_id}>, You have hit <@{target.id}>!"
    return SnowballError("Sorry, Provided user is out of range")

@register(group=Groups.GLOBAL, main=snowball)
@Event(month=12)
@cooldown(hours=1)
async def gather(ctx: Context):
    '''Gather snowballs to throw at someone later!'''
    s = ctx.db.sql.session()
    user = models.User.fetch_or_add(s, id=ctx.user_id)

    amount = random().randint(2,5)
    item = items.Item.fetch_or_add(s, name="Snowball", type=types.Item.Resource)
    snowball_inventory = items.Inventory(item, amount)

    transaction = user.claim_items(ctx.guild_id, [snowball_inventory])
    s.add(transaction)

    return f"<@{ctx.user_id}>, Successfully gathered {amount} snowballs!"
