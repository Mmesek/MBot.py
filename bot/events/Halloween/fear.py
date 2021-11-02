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

from .general import HalloweenCooldown, halloween
from ...database import items, types, models
from ...database.mixins import UserID

class Monsters(Enum):
    Imp = 10
    Poltergeist = 50
    Skeleton = 200
    Mummy = 800
    Shoggoth = 3200

monsterPower = {i.name: i.value for i in Monsters}

MONSTER_NAMES = list([j.name for j in Monsters])

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
    monster_ids = {i.id: i.name for i in s.query(items.Item).filter(items.Item.name.in_(MONSTER_NAMES)).all()}
    avg_army_size = s.query(sa.func.avg(items.Inventory.quantity), items.Inventory.item_id).filter(
        items.Inventory.item_id.in_(list(monster_ids.keys()))
    ).group_by(items.Inventory.item_id).all()
    avg_army = {monster_ids.get(i[1], None): i[0] for i in avg_army_size}

    summoned_entites = {i.item.name: i.quantity for i in u.items if i.item.name in MONSTER_NAMES}
    def adjust_price(monster: Monsters) -> int:
        avg = avg_army.get(monster.name, 1)
        value = monster.value
        owned = summoned_entites.get(monster.name, 0)
        if int(avg) < owned:
            multipler = (owned - int(avg))
            if multipler > 1:
                value *= multipler
        return int(value)

    if owned_fear:
        fear_amount = owned_fear.quantity
    else:
        fear_amount = 0
    if not monster:
        monsters = []
        for monster in Monsters:
            value = monster.value # adjust_price(monster)
            monsters.append(f"{monster.name} - {value}")
        e = Embed().setTitle("Summoning Cost in Fear")
        e.setDescription("\n".join(monsters))
        if owned_fear:
            e.addField("Current Fear", f"{owned_fear.quantity}", True)
        carved_pumpkins = next(filter(lambda x: x.item.name == 'Jack-o-Latern', u.items), None)
        if carved_pumpkins:
            e.addField("Carved Pumpkins", f"{carved_pumpkins.quantity}", True)
        entities = []
        for entity, _quantity in summoned_entites.items():
            entities.append(f"{entity} - {_quantity}")
        if entities:
            e.addField("Current Army", "\n".join(entities), True)
        return e
    
    adjusted = monster.value # adjust_price(monster)

    if fear_amount < adjusted*quantity:
        return "You don't have enough fear to summon that entity!"
    fear_prc = items.Inventory(fear_item, adjusted*quantity)
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
    if user_fear:
        user_fear = user_fear.quantity
    user_monsters = [i for i in u.items if i.item.name in list([j.name for j in Monsters])]
    user_power = sum([monsterPower.get(i.item.name)*i.quantity for i in user_monsters])
    if user_power == 0:
        return "You don't have any army to send!"
    
    t = models.User.fetch_or_add(s, id=target.id)
    target_fear = next(filter(lambda x: x.item_id == fear_item.id, t.items), 0)
    if target_fear:
        target_fear = target_fear.quantity
    target_monsters = [i for i in t.items if i.item.name in list([j.name for j in Monsters])]
    target_power = sum([monsterPower.get(i.item.name)*i.quantity for i in target_monsters])
    carved_pumpkins = next(filter(lambda x: x.item.name == 'Jack-o-Latern', t.items), None)
    if carved_pumpkins:
        target_power += carved_pumpkins.quantity

    def calculate_fear(_fear: int, total_fear: int) -> int:
        #power_difference = user_power - target_power
        #points = 50 * (power_difference // 100)
        #if points > _fear:
        from random import SystemRandom as random
        d = random().randint(2,10)
        fear_recv = (_fear or 50) // d
        if total_fear > fear_recv:
            return fear_recv
        return random().randint(1,fear_recv) # Return less than calculated fear if user doesn't have enough fear 
    
    def award_points(winner: models.User, loser: models.User, loser_fear: int, _fear: int):
        reward_points = calculate_fear(_fear, loser_fear)
        reward = items.Inventory(fear_item, reward_points)

        transaction = winner.claim_items(ctx.guild_id, [reward])
        if loser_fear > reward_points:
            loser.remove_item(reward, transaction=transaction)

        return transaction, reward.quantity
    
    def diff(a, b) -> int:
        return int(b // (a / (b or 1)))

    if user_power > target_power:
        if target_fear > 0:
            _fear = diff(user_power, target_power)
        else:
            _fear = target_fear // 2
        transaction, reward = award_points(u, t, target_fear, _fear)
        result = f"<@{ctx.user_id}>'s Army, Sucessfully scared <@{target.id}> and gained {reward} of Fear!"
    elif user_power == target_power:
        return "Draw! Both Armies tried to scare each other but failed!"
    else:
        _fear = diff(target_power, user_power)
        transaction, reward = award_points(t, u, user_fear, _fear)
        result = f"<@{ctx.user_id}> got scared by <@{target.id}>'s army and lost {reward} of Fear!"
    
    s.add(transaction)
    s.add(FearLog(server_id=ctx.guild_id, target_id=target.id, user_power=user_power, target_power=target_power, user_id=ctx.user_id, reward=reward))
    s.commit()
    return result

@register(group=Groups.GLOBAL, main=fear)
@cooldown(minutes=10, logic=HalloweenCooldown)
async def scout(ctx: Context, target: User) -> Embed:
    '''
    Take a pick at someone elses army!
    Params
    ------
    target:
        User you want to scout
    '''
    e = Embed().setTitle(f"{target.username}'s Army")
    s = ctx.db.sql.session()
    u = models.User.fetch_or_add(s, id=target.id)
    summoned_entites = [i for i in u.items if i.item.name in list([j.name for j in Monsters])]
    entities = [f"{entity.item.name} - {entity.quantity}" for entity in summoned_entites]
    if entities:
        e.setDescription("\n".join(entities))
    return e
