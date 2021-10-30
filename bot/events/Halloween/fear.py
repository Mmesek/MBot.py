#TODO:
# New:
# Fear system? Trade to buy monsters, send on others, gain more fear
# Increase power level of player based on bites/cures?
# Boss raids?
from enum import Enum
from datetime import datetime
import sqlalchemy as sa
from mlib.database import Base, Timestamp

from MFramework import register, Context, User, Groups, Embed
from MFramework.commands.cooldowns import cooldown
from MFramework.database.alchemy.mixins import ServerID

from .general import HalloweenCooldown, halloween, FearLog
from ...database import items, types, models
from ...database.mixins import UserID

class Monsters(Enum):
    Imp = 10
    Poltergeist = 50
    Skeleton = 200
    Mummy = 800
    Shoggoth = 3200

class FearLog(ServerID, UserID, Timestamp, Base):
    timestamp: datetime = sa.Column(sa.TIMESTAMP(timezone=True), primary_key=True, server_default=sa.func.now())
    target_id: User = sa.Column(sa.ForeignKey("User.id", ondelete='Cascade', onupdate='Cascade'), primary_key=False, nullable=False)
    user_power: int = sa.Column(sa.Integer)
    target_power: int = sa.Column(sa.Integer)
    reward: int = sa.Column(sa.Integer)

@register(group=Groups.GLOBAL, main=halloween)
async def fear(ctx: Context):
    '''
    Base command related to fear system
    '''
    pass

@register(group=Groups.GLOBAL, main=fear)
async def carve(ctx: Context, quantity: int=1) -> str:
    '''
    Carve owned pumpkins into Jack-o-Laterns!
    Params
    ------
    quantity:
        Quantity of pumpkins you want to carve
    '''
    s = ctx.db.sql.session()
    u = models.User.fetch_or_add(s, id=ctx.user_id)
    item = items.Item.fetch_or_add(s, name="Pumpkin")
    pumpkins = next(filter(lambda x: x.item_id == item.id and x.quantity >= quantity, u.items), None)
    if not pumpkins:
        return "You don't have enough pumpkins!"
    pumpkin_inv = items.Inventory(item, quantity)
    result_item = items.Item.fetch_or_add(s, name="Jack-o-Latern", type=types.Item.Miscellaneous)
    result_inv = items.Inventory(result_item, quantity)
    t = u.claim_items(ctx.guild_id, [result_inv])
    u.remove_item(pumpkin_inv, transaction=t)
    s.commit()
    return f"Successfully Carved {quantity} Jack-o-Laterns!"

@register(group=Groups.GLOBAL, main=fear)
async def summon(ctx: Context, monster: Monsters=None, quantity: int=1):
    '''
    Summon an entity to fight for you in your army
    Params
    ------
    monster:
        Monster you want to summon. Leave empty to check prices
    quantity:
        Amount of entities you want to summon at once
    '''
    s = ctx.db.sql.session()
    u = models.User.fetch_or_add(s, id=ctx.user_id)
    fear_item = items.Item.fetch_or_add(s, name="Fear")
    owned_fear = next(filter(lambda x: x.item_id == fear_item.id, u.items), None)
    if not monster:
        monsters = []
        for monster in Monsters:
            monsters.append(f"{monster.name} - {monster.value}")
        e = Embed()
        e.setDescription("\n".join(monsters))
        if owned_fear:
            e.addField("Current Fear", f"{owned_fear.quantity}", True)
        carved_pumpkins = next(filter(lambda x: x.item.name == 'Jack-o-Latern', u.items), None)
        if carved_pumpkins:
            e.addField("Currently Carved Pumpkins", f"{carved_pumpkins.quantity}", True)
        summoned_entites = [i for i in u.items if i.item.name in Monsters]
        entities = []
        for entity in summoned_entites:
            entities.append(f"{entity.item.name} - {entity.quantity}")
        if entities:
            e.addField("Current Army", "\n".join(entities), True)

    if owned_fear.quantity < monster.value*quantity:
        return "You don't have enough fear to summon that entity!"
    fear_prc = items.Inventory(fear_item, monster.value*quantity)
    item = items.Item.fetch_or_add(s, name=monster.name, type=types.Item.Entity)
    result_inv = items.Inventory(item, quantity)
    t = u.claim_items(ctx.guild_id, [result_inv])
    u.remove_item(fear_prc, transaction=t)
    s.commit()
    amount = f" x {quantity}" if quantity else ""
    return f"Successfully summoned {monster.name}{amount}"

@register(group=Groups.GLOBAL, main=fear)
@cooldown(hours=1, logic=HalloweenCooldown)
async def scare(ctx: Context, target: User):
    '''
    Scare user using your army!
    Params
    ------
    user:
        User you want to scare
    '''
    if target.id == ctx.user_id:
        return "You can't send your army on your own self!"
    s = ctx.db.sql.session()

    fear_item = items.Item.fetch_or_add(s, name="Fear")
    
    u = models.User.fetch_or_add(s, id=ctx.user_id)
    user_fear = next(filter(lambda x: x.item_id == fear_item.id, u.items), 0)
    user_monsters = [i for i in u.items if i.item.name in Monsters]
    user_power = sum([Monsters(i.item.name).value*i.quantity for i in user_monsters])
    
    t = models.User.fetch_or_add(s, id=target.id)
    target_fear = next(filter(lambda x: x.item_id == fear_item.id, t.items), 0)
    target_monsters = [i for i in t.items if i.item.name in Monsters]
    target_power = sum([Monsters(i.item.name).value*i.quantity for i in target_monsters])
    carved_pumpkins = next(filter(lambda x: x.item.name == 'Jack-o-Latern', t.items))
    target_power += carved_pumpkins

    def calculate_fear(_fear):
        #power_difference = user_power - target_power
        #points = 50 * (power_difference // 100)
        #if points > _fear:
        from random import SystemRandom as random
        d = random().randint(2,10)
        if 50 < _fear // d:
            return _fear // d
        return 50#points
    
    def award_points(winner, loser, _fear):
        reward_points = calculate_fear(_fear)
        reward = items.Inventory(fear_item, reward_points)

        transaction = winner.claim_items(ctx.guild_id, [reward])
        if _fear > reward_points:
            loser.remove_item(reward, transaction=t)

        return transaction, reward.quantity

    if user_power > target_power:
        transaction, reward = award_points(u, t, target_fear)
        result = f"<@{ctx.user_id}>'s Army, Sucessfully scared <@{target.id}> and gained {reward} of Fear!"
    elif user_power == target_power:
        return "Draw! Both Armies tried to scare each other but failed!"
    else:
        transaction, reward = award_points(t, u, user_fear)
        result = f"<@{ctx.user_id}> got scared by <@{target.id}>'s army and lost {reward} of Fear!"
    
    s.add(transaction)
    s.add(FearLog(server_id=ctx.guild_id, target_id=target.id, user_power=user_power, target_power=target_power, user_id=ctx.user_id, reward=reward))
    s.commit()
    return result
