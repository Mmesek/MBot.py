#TODO:
# New:
# Fear system? Trade to buy monsters, send on others, gain more fear
# Increase power level of player based on bites/cures?
# Boss raids?
from enum import Enum
from datetime import datetime, timedelta
import sqlalchemy as sa
from mlib.database import Base, Timestamp

from MFramework import register, Context, User, Groups, Embed
from MFramework.commands.cooldowns import cooldown
from MFramework.database.alchemy.mixins import ServerID

from .general import HUNTERS, IMMUNE_TABLE, Halloween, HalloweenCooldown, halloween, inner, Race
from ...database import items, types, models
from ...database.mixins import UserID

class FearCooldown(HalloweenCooldown):
    @property
    def cooldown_var(self) -> timedelta:
        if self.race in HUNTERS:
            return self.cooldown * 0.7
        elif self.race in IMMUNE_TABLE:
            return self.cooldown * 1.3
        return timedelta()

class FEAR_COOLDOWNS(Enum):
    SCARE = timedelta(hours=1)
    SCOUT = timedelta(minutes=10)
    RAID = timedelta(hours=2)

class Monsters(Enum):
    Imp = 10
    Poltergeist = 50
    Skeleton = 200
    Mummy = 800
    Shoggoth = 3200

monsterPower = {i.name: int(i.value*(1+(x/10))) for x, i in enumerate(Monsters)}

MONSTER_NAMES = list([j.name for j in Monsters])

class FearLog(ServerID, UserID, Timestamp, Base):
    timestamp: datetime = sa.Column(sa.TIMESTAMP(timezone=True), primary_key=True, server_default=sa.func.now())
    target_id: User = sa.Column(sa.ForeignKey("User.id", ondelete='Cascade', onupdate='Cascade'), primary_key=False, nullable=False)
    user_power: int = sa.Column(sa.Integer)
    target_power: int = sa.Column(sa.Integer)
    reward: int = sa.Column(sa.Integer)
    success: bool = sa.Column(sa.Boolean)
    user_fear: int = sa.Column(sa.Integer)
    target_fear: int = sa.Column(sa.Integer)


@register(group=Groups.GLOBAL, main=halloween)
def fear(cls=None, *, should_register: bool=True):
    '''
    Base command related to fear system
    '''
    import functools
    i = functools.partial(inner, races=list(Race), main=fear, should_register=should_register)
    if cls:
        return i(cls)
    return i

@fear
async def carve(ctx: Context, quantity: int=1, *, session: sa.orm.Session, **kwargs) -> str:
    '''
    Carve owned pumpkins into Jack-o-Laterns!
    Params
    ------
    quantity:
        Quantity of pumpkins you want to carve
    '''
    u = models.User.fetch_or_add(session, id=ctx.user_id)
    item = items.Item.fetch_or_add(session, name="Pumpkin")
    pumpkins = next(filter(lambda x: x.item_id == item.id and x.quantity >= quantity, u.items), None)
    if not pumpkins:
        return "You don't have enough pumpkins!"
    pumpkin_inv = items.Inventory(item, quantity)
    result_item = items.Item.fetch_or_add(session, name="Jack-o-Latern", type=types.Item.Miscellaneous)
    result_inv = items.Inventory(result_item, quantity)
    t = u.claim_items(ctx.guild_id, [result_inv])
    u.remove_item(pumpkin_inv, transaction=t)
    session.add(t)
    session.commit()
    return f"Successfully Carved {quantity} Jack-o-Laterns!"

@fear
async def summon(ctx: Context, monster: Monsters=None, quantity: int=1, *, session: sa.orm.Session, this_user: Halloween, **kwargs):
    '''
    Summon an entity to fight for you in your army
    Params
    ------
    monster:
        Monster you want to summon. Leave empty to check prices
    quantity:
        Amount of entities you want to summon at once
    '''
    u = models.User.fetch_or_add(session, id=ctx.user_id)
    fear_item = items.Item.fetch_or_add(session, name="Fear")
    owned_fear = next(filter(lambda x: x.item_id == fear_item.id, u.items), None)
    monster_ids = {i.id: i.name for i in session.query(items.Item).filter(items.Item.name.in_(MONSTER_NAMES)).all()}
    avg_army_size = session.query(sa.func.avg(items.Inventory.quantity), items.Inventory.item_id).filter(
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
        _cooldowns = []
        from mlib.localization import secondsToText as s2t
        for _cooldown in FEAR_COOLDOWNS:
            r = FearCooldown(ctx, _cooldown.value, _cooldown.name.lower(), {"session": session, "this_user": this_user})
            if r.on_cooldown:
                _cooldowns.append((r._type, s2t(int(r.remaining.total_seconds()))))
        if _cooldowns:
            e.addField("Cooldowns", "\n".join(f"`{i[0].title()}`: `{i[1]}`" for i in _cooldowns))
        user_power = sum([monsterPower.get(k)*v for k, v in summoned_entites.items()])
        if user_power:
            e.setFooter(f"Approximate Army Power: {user_power}")

        return e
    
    adjusted = monster.value # adjust_price(monster)

    if fear_amount < adjusted*quantity:
        return "You don't have enough fear to summon that entity!"
    fear_prc = items.Inventory(fear_item, adjusted*quantity)
    item = items.Item.fetch_or_add(session, name=monster.name, type=types.Item.Entity)
    result_inv = items.Inventory(item, quantity)
    t = u.claim_items(ctx.guild_id, [result_inv])
    u.remove_item(fear_prc, transaction=t)
    session.commit()
    amount = f" x {quantity}" if quantity else ""
    return f"Successfully summoned {monster.name}{amount}"

@fear
@cooldown(hours=1, logic=FearCooldown)
async def scare(ctx: Context, target: User, *, session: sa.orm.Session, **kwargs):
    '''
    Scare user using your army!
    Params
    ------
    user:
        User you want to scare
    '''
    if target.id == ctx.user_id:
        return "You can't send your army on your own self!"

    fear_item = items.Item.fetch_or_add(session, name="Fear")
    
    u = models.User.fetch_or_add(session, id=ctx.user_id)
    user_fear = next(filter(lambda x: x.item_id == fear_item.id, u.items), 0)
    if user_fear:
        user_fear = user_fear.quantity
    user_monsters = [i for i in u.items if i.item.name in list([j.name for j in Monsters])]
    user_power = sum([monsterPower.get(i.item.name)*i.quantity for i in user_monsters])
    if user_power == 0 or user_fear == 0:
        if user_fear == 0:
            first_fear = items.Inventory(fear_item, quantity=10)
            transaction = u.claim_items(ctx.guild_id, [first_fear])
            session.add(FearLog(server_id=ctx.guild_id, target_id=target.id, user_power=user_power, target_power=None, user_id=ctx.user_id, reward=10, success=True, user_fear=0, target_fear=None))
            session.commit()
            return "You have gained 10 of fear! Summon army in order to gain more fear!"
        return "You don't have any army to send!"
    
    t = models.User.fetch_or_add(session, id=target.id)
    target_fear = next(filter(lambda x: x.item_id == fear_item.id, t.items), 0)
    if target_fear:
        target_fear = target_fear.quantity
    target_monsters = [i for i in t.items if i.item.name in list([j.name for j in Monsters])]
    target_power = sum([monsterPower.get(i.item.name)*i.quantity for i in target_monsters])
    carved_pumpkins = next(filter(lambda x: x.item.name == 'Jack-o-Latern', t.items), None)
    if carved_pumpkins:
        target_power += carved_pumpkins.quantity

    from random import SystemRandom as random
    def calculate_fear(fear_recv: int, total_fear: int) -> int:
        #power_difference = user_power - target_power
        #points = 50 * (power_difference // 100)
        #if points > _fear:
        #d = random().randint(2,5)
        #fear_recv = (_fear or 50) // d
        fear_rand = random().randint(20, 50)
        if not fear_recv:
            # There is no fear, give some
            fear_recv = fear_rand
        if total_fear // 2 <= fear_recv:
            # Limit max fear lost to half of what user currently has
            fear_recv = total_fear // 2
        if total_fear > fear_recv:
            # User has enough fear, let's go
            return fear_recv
        # Return less than calculated fear if user doesn't have enough fear 
        return random().randint(10, max(20, (total_fear or fear_rand)))
    
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
        if target_fear > 10:
            _fear = diff(user_power, target_power)
        else:
            _fear = target_fear // 1.2
        transaction, reward = award_points(u, t, target_fear, _fear)
        success = True
        result = f"<@{ctx.user_id}>'s Army, Sucessfully scared <@{target.id}> and gained {reward} of Fear!"
    elif user_power == target_power:
        return "Draw! Both Armies tried to scare each other but failed!"
    elif random().randint(0, max(user_power, target_power)) < min(user_power, target_power):
        _fear = target_fear // 4
        transaction, reward = award_points(u, t, target_fear, _fear)
        success = True
        result = f"<@{ctx.user_id}>'s Army managed to scare <@{target.id}> and gain {reward} of Fear!"
    else:
        _fear = diff(target_power, user_power)
        transaction, reward = award_points(t, u, user_fear, _fear)
        success = False
        result = f"<@{ctx.user_id}> got scared by <@{target.id}>'s army and lost {reward} of Fear!"
    
    session.add(transaction)
    session.add(FearLog(server_id=ctx.guild_id, target_id=target.id, user_power=user_power, target_power=target_power, user_id=ctx.user_id, reward=reward, success=success, user_fear=user_fear, target_fear=target_fear))
    session.commit()
    return result

@fear
@cooldown(minutes=10, logic=FearCooldown)
async def scout(ctx: Context, target: User, *, session: sa.orm.Session, **kwargs) -> Embed:
    '''
    Take a pick at someone elses army!
    Params
    ------
    target:
        User you want to scout
    '''
    e = Embed().setTitle(f"{target.username}'s Army")
    u = models.User.fetch_or_add(session, id=target.id)
    summoned_entites = [i for i in u.items if i.item.name in list([j.name for j in Monsters])]
    entities = [f"{entity.item.name} - {entity.quantity}" for entity in summoned_entites]
    if entities:
        e.setDescription("\n".join(entities))
    return e

class Bosses(Enum):
    Troll = 2500
    Moka = 5000
    Volatile = 12500
    Dracula = 30000
    Dark_Enchanter = 75000
    Wild_Moderator = 125000
    Ancient_One = 750000
    Champion = 5000000

@fear
@cooldown(hours=2, logic=FearCooldown)
async def raid(ctx: Context, boss: Bosses, *, session: sa.orm.Session, **kwargs):
    '''
    Send your army on a raid!
    Params
    ------
    boss:
        boss you want to attack
    '''
    name = boss.name.replace('_',' ')
    boss_item = items.Item.fetch_or_add(session, name=name, type=types.Item.Entity)
    if boss_item.durability == None:
        boss_item.durability = boss.value
        multipler = 0.1
        for x, _ in enumerate(Bosses):
            if _.name == boss.name:
                multipler += x * 0.1
        boss_item.damage = int(boss.value * multipler)

    if boss_item.durability == 0:
        return "This boss has already been defeated!"

    u = models.User.fetch_or_add(session, id=ctx.user_id)
    user_monsters = [i for i in u.items if i.item.name in list([j.name for j in Monsters])]
    user_power = sum([monsterPower.get(i.item.name)*i.quantity for i in user_monsters])
    if not user_power:
        return "Come back with an army!"
    if user_power > boss.value * 0.75:
        return "Your army is too strong to fight with this entity!"

    import random
    dmg = random.SystemRandom().randint(0, boss_item.damage)
    dmg_dealt = user_power - dmg
    if dmg_dealt <= 0:
        return "Sadly your army did nothing!"

    boss_item.durability -= dmg_dealt
    if boss_item.durability <= 0:
        boss_item.durability = 0
        bonus = random.SystemRandom().randint(50, 500)
        boss_remaining = f" You have Defeated {name}! Bonus: {bonus}"
    else:
        bonus = random.SystemRandom().randint(0, 50)
        boss_remaining = f" Remaining health: {boss_item.durability}"

    fear_item = items.Item.fetch_or_add(session, name="Fear")
    d = random.SystemRandom().uniform(0.1, 0.45)
    reward = items.Inventory(fear_item, int(dmg_dealt * d) + bonus)
    t = u.claim_items(ctx.guild_id, [reward])
    session.add(t)
    session.add(FearLog(server_id=ctx.guild_id, target_id=ctx.user_id, user_power=user_power, target_power=dmg, user_id=ctx.user_id, reward=reward.quantity, success=True, user_fear=dmg_dealt, target_fear=boss.value))
    session.commit()

    return f"<@{ctx.user_id}>, you have gained {reward.quantity} and dealt {dmg_dealt} to {name}!" + boss_remaining

@fear
async def sacrifice(ctx: Context, monster: Monsters, quantity: int=1, *, session: sa.orm.Session, **kwargs):
    """
    Sacrifice your Army units for Reinforced Fear™
    Params
    ------
    monster:
        Monster you want to sacrifice.
    quantity:
        Amount of entities you want to sacrifice at once
    """
    u = models.User.fetch_or_add(session, id=ctx.user_id)
    summoned_entites = {i.item.name: i for i in u.items if i.item.name in MONSTER_NAMES}
    owned = summoned_entites.get(monster.name, None)
    if owned and owned.quantity >= quantity:
        rf = items.Item.fetch_or_add(session, name="Reinforced Fear", type=types.Item.Currency)
        rf_q = (quantity*monster.value) // 10
        t = u.claim_items(ctx.guild_id, [items.Inventory(rf, quantity = rf_q)])
        m_item = items.Item.fetch_or_add(session, name=owned.item.name)
        u.remove_item(items.Inventory(m_item, quantity=quantity), transaction=t)
        session.add(t)
        session.commit()
        return f"Successfuly sacrificed {monster.name}{f' x {quantity}' if quantity > 1 else ''} and received Reinforced Fear x {rf_q}!" 
    return "You don't have enough monsters of that type!"
    
