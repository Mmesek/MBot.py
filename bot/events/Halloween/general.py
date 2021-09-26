from datetime import timedelta, timezone, datetime
from typing import Tuple, List, Optional
from enum import Enum
from random import SystemRandom
from mlib.localization import tr

from MFramework import Context, User, Snowflake, Groups, register, Cooldown, EventBetween
from ...database.types import Statistic, HalloweenRaces as Race
from ... import database as db
def _t(key: str, language: str='en', **kwargs):
    return tr("events.halloween."+key, language, **kwargs)

class Cooldowns:
    last_action: datetime
    cooldown_ends: datetime
    current_faction: int
    target_faction: int
    remaining_factions: int
    def __init__(self, ctx: Context, user: Snowflake, target_user: Optional[Snowflake] = None) -> None:
        last_action = 0
        cooldown_ends = 0
        self.last_action = last_action
        self.cooldown_ends = cooldown_ends
        self.get_race_counts()

    @property
    def elapsed(self) -> timedelta:
        '''Elapsed since last action'''
        return datetime.now(tz=timezone.utc) - self.last_action

    @property
    def action_cooldown_left(self) -> timedelta:
        '''Remaining action cooldown'''
        return self.cooldown_ends - datetime.now(tz=timezone.utc)

    @property
    def is_top_faction(self) -> bool:
        '''Whether it's currently a top faction'''
        return (self.remaining_factions // 2) < self.current_faction

    @property
    def faction_difference(self) -> int:
        '''Difference to other factions'''
        return self.current_faction - (self.remaining_factions // 2)

    @property
    def cooldown_var(self) -> timedelta:
        '''Current Cooldown Variance based on difference to other factions'''
        difference = self.faction_difference
        if not self.is_top_faction:
            difference = difference * 2
        return timedelta(minutes=difference * 3)

    def get_race_counts(self, s, data, self_user, target_user) -> Tuple[int, int, int]:
        '''Returns count for current user faction, user's target faction and collectively remaining factions'''
        self.current_faction = 0
        self.target_faction = 0
        self.remaining_factions = 0

    def calc_cooldown_var(self, s, data, self_user) -> timedelta:
        '''Calculates cooldown variance'''
        target, current_race, others = self.get_race_counts(s, data, self_user, self_user)
        return self.cooldown_var

class Responses(Enum):
    ERROR = 0 # 
    CANT = 1 # User has wrong state
    SUCCESS = 2 # Target Bitten or Cured successfuly
    FAILED = 3 # Failed to bite or cure
    IMMUNE = 4 # Target is on the same side or is immune
    COOLDOWN = 5 # Cooldown not ready
    AVAILABLE = 6 #
    PROTECTED = 7 # Target is protected
    OTHER = 8 # Target is either not specified or wrongly specified

class COOLDOWNS(Enum):
    DEFEND = timedelta(hours=1)
    CURE = timedelta(hours=2)
    BITE = timedelta(hours=3)
    BETRAY = timedelta(hours=4)

IMMUNE_TABLE = {
    Race.Vampire: Race.Hunter,
    Race.Werewolf: Race.Huntsmen,
    Race.Zombie: Race.Enchanter
}

HUNTERS = IMMUNE_TABLE.values()

class DRINKS(Enum):
    WINE = Race.Vampire
    MOONSHINE = Race.Werewolf
    VODKA = Race.Zombie
    NIGHTMARE = Race.Human

class Guilds(Enum):
    Hunters = Race.Hunter
    Huntsmen = Race.Huntsmen
    Enchanters = Race.Enchanter

def turn(ctx: Context, server_id: Snowflake, user_id: Snowflake, target_id: Snowflake, user_race: Race, target_race: Race):
    pass

def get_total(total: List[Statistic]) -> Tuple[int, int]:
    '''Returns total bites and population'''
    pass

# Factions
#   reinforce - send reinforcments (turn x% of users on that server into that faction) to another server - only for leading faction on a server!

@EventBetween(after_month=10, after_day=14, before_month=11, before_day=7)
@register(group=Groups.GLOBAL)
async def halloween(ctx: Context, *, language):
    '''Halloween Event commands'''
    pass

@register(group=Groups.ADMIN, main=halloween)
async def settings(ctx: Context, *, language):
    '''Shows settings for Halloween Event'''
    pass

@register(group=Groups.ADMIN, main=settings)
async def roles(ctx: Context, delete:bool=False, *, language):
    '''Create and/or add roles related to Halloween Event
    Params
    ------
    delete:
        Delete Event roles (*Only ones that were made by bot)
    '''
    s = ctx.db.sql.session()
    roles = get_roles(ctx.guild_id, s)
    if roles:
        users = s.query(db.HalloweenClasses).filter(db.HalloweenClasses.GuildID == ctx.guild_id).all()
        for user in users:
            await ctx.bot.add_guild_member_role(ctx.guild_id, user.UserID, roles.get(user.CurrentClass, ""), "Halloween Minigame")
    else:
        for name in ROLES:
            role = await ctx.bot.create_guild_role(ctx.guild_id, _t(name.lower().replace(' ','_'), language, count=1).title(), 0, None, False, False, "Created Role for Halloween Minigame")
            s.merge(db.HalloweenRoles(ctx.guild_id, role.name, role.id))
        s.commit()


##########
# HUMANS #
##########

@register(group=Groups.GLOBAL, main=halloween)
async def humans(ctx: Context, *, language):
    '''Commands related to humans'''
    pass

@register(group=Groups.GLOBAL, main=humans)
async def enlist(ctx: Context, guild: Guilds, *, language):
    '''Enlist as a hunter
    Params
    ------
    guild:
        Hunter's guild you want to join'''
    user_race = None
    turn(ctx, ctx.guild_id, ctx.user_id, ctx.user_id, user_race, guild.value)

@register(group=Groups.GLOBAL, main=humans)
async def drink(ctx: Context, type: DRINKS, *, language):
    '''Drink an unknown beverage to become a monster
    Params
    ------
    type:
        Drink you want to drink'''
    user_race = None
    turn(ctx, ctx.guild_id, ctx.user_id, ctx.user_id, user_race, type.value)

############
# MONSTERS #
############

@register(group=Groups.GLOBAL, main=halloween)
async def monsters(ctx: Context, *, language):
    '''Commands related to Monster's factions'''
    pass

@Cooldown(hours=3, logic=Cooldowns)
@register(group=Groups.GLOBAL, main=monsters)
async def bite(ctx: Context, target: User, *, language):
    '''Bite your target to turn into one of your own kin
    Params
    ------
    target:
        Target you want to bite'''
    user_race = None
    target_race = None
    turn(ctx, ctx.guild_id, ctx.user_id, target.id, user_race, target_race)

###########
# HUNTERS #
###########

@register(group=Groups.GLOBAL, main=halloween)
async def hunters(ctx: Context, *, language):
    '''Commands related to Hunter's factions'''
    pass

@Cooldown(hours=2, logic=Cooldowns)
@register(group=Groups.GLOBAL, main=hunters)
async def cure(ctx: Context, target: User, *, language):
    '''Cure your target from the darkness back into human being
    Params
    ------
    target:
        Target you want to cure'''
    user_race = None
    target_race = None
    turn(ctx, ctx.guild_id, ctx.user_id, target.id, user_race, target_race)

@Cooldown(hours=1, logic=Cooldowns)
@register(group=Groups.GLOBAL, main=hunters)
async def defend(ctx: Context, target: User, *, language):
    '''Protect fellow hunter from being bitten 
    Params
    ------
    target:
        Target you want to protect'''
    s = ctx.db.sql.session()
    self_user = get_user(ctx.guild_id, ctx.user.id, s)
    if self_user is None or self_user.CurrentClass not in HUNTERS:
        return
    if user == ():
        return await ctx.reply(_t("error_generic"))

    now = datetime.now(tz=timezone.utc)
    if self_user.ActionCooldownEnd is not None:
        if now < self_user.ActionCooldownEnd:
            cooldown = self_user.ActionCooldownEnd - now
            return await ctx.reply(_t("remaining_cooldown", language, cooldown=cooldown))

    target = get_user_id(user)
    if target == ctx.user_id:
        return await ctx.reply(_t("failed_defend", language))
    target_user = s.query(db.HalloweenClasses).filter(db.HalloweenClasses.GuildID == ctx.guild_id, db.HalloweenClasses.UserID == target).first()
    
    if target_user.CurrentClass not in HUNTERS:
        return await ctx.reply(_t("cant_defend", language))
    
    if target_user.ProtectionEnds is None or target_user.ProtectionEnds < now:
        duration = SystemRandom().randint(5, 40)
        delta = now + timedelta(minutes=duration)
        target_user.ProtectedBy = ctx.user_id
        target_user.ProtectionEnds = delta
        self_user.ActionCooldownEnd = now + timedelta(hours=1)
        s.add(db.HalloweenLog(ctx.guild_id, target_user.UserID, target_user.CurrentClass, target_user.CurrentClass, self_user.UserID, now))
        s.commit()
        return await ctx.reply(_t("success_defend", language, duration=duration))

    return await ctx.reply(_t("error_defend", language))

@Cooldown(hours=4, logic=Cooldowns)
@register(group=Groups.GLOBAL, main=hunters)
async def betray(ctx: Context, target: User, *, language):
    '''Attempt to convince a monster you are hunting to join the cause and fight with the darkness instead
    Params
    ------
    target:
        Target you want to convince'''
    s = ctx.db.sql.session()
    self_user = get_user(ctx.guild_id, ctx.user.id, s)
    if self_user is None or self_user.CurrentClass not in HUNTERS:
        return
    if user == ():
        return await ctx.reply(_t("error_generic"))
    now = datetime.now(tz=timezone.utc)
    if self_user.ActionCooldownEnd is not None and now < self_user.ActionCooldownEnd:
        cooldown = self_user.ActionCooldownEnd - now
        return await ctx.reply(_t("remaining_cooldown", language, cooldown=cooldown))
    roll = SystemRandom().randint(0, 100)
    self_user.ActionCooldownEnd = now + timedelta(hours=4)
    s.commit()
    if roll > 92:
        await turning_logic(ctx, target, ctx.user, HUNTERS, True, skip_cooldown=True)
        return await ctx.reply(_t("success_betray", language))
    return await ctx.reply(_t("error_betray", language))

