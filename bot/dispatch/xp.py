import sqlalchemy as sa

from mlib.database import Base, TimestampUpdate

from MFramework import Bot, Message, onDispatch, Embed
from MFramework.database.alchemy.mixins import Snowflake

class User_Experience(TimestampUpdate, Base):
    server_id: Snowflake = sa.Column(sa.ForeignKey("Server.id", ondelete='Cascade', onupdate='Cascade'), primary_key=True, nullable=False, default=0)
    user_id: Snowflake = sa.Column(sa.ForeignKey("User.id", ondelete='Cascade', onupdate='Cascade'), primary_key=True, nullable=False, default=0)
    type: int = sa.Column(sa.Integer, nullable=False, default=0)
    value: float = sa.Column(sa.Float, nullable=False, default=0)
    def __init__(self, server_id: Snowflake, user_id: Snowflake, type: int = 0, value: float = 0) -> None:
        self.server_id = server_id
        self.user_id = user_id
        self.type = type
        self.value = value


@onDispatch(event="message_create")
async def exp(self: Bot, data: Message):
    if (
        data.channel_id in self.cache[data.guild_id].disabled_channels
        or any(r in data.member.roles for r in self.cache[data.guild_id].disabled_roles)
        or len(set(data.content.split(' '))) < 2
    ):
        return

    last = self.cache[data.guild_id].cooldowns.has(data.guild_id, data.author.id, "ChatExp")
    if last:
        return

    role_boosts = 0
    for role in data.member.roles:
        if role in self.cache[data.guild_id].role_rates:
            role_boosts += self.cache[data.guild_id].role_rates.get(role, 0) or 0

    rate = 1 * ((self.cache[data.guild_id].exp_rates.get(data.channel_id, 1.0) or 0) + role_boosts)

    from MFramework.database import alchemy as db

    #user = models.User.fetch_or_add(session, id=data.author.id)
    #boost = user.get_setting(db.types.Setting.Exp) or 1.0
    # FIXME: Reenable user boost on SQL side?
    exp = await self.db.supabase.increase_exp(data.guild_id, data.author.id, rate)# * boost)
    self.cache[data.guild_id].cooldowns.store(data.guild_id, data.author.id, "ChatExp")

    previous_level = None
    level_up = None

    for role, req in self.cache[data.guild_id].level_roles:
        if role in data.member.roles:
            if exp < req:
                await self.remove_guild_member_role(data.guild_id, data.author.id, role, "Level Role")
            previous_level = role
        if exp >= req:
            level_up = role

    if level_up == previous_level:
        return

    if level_up:
        await self.add_guild_member_role(data.guild_id, data.author.id, level_up, "Level Role")
    if previous_level:
        await self.remove_guild_member_role(data.guild_id, data.author.id, previous_level, "Level Role")

    from ..database import types, log
    if self.cache[data.guild_id].is_tracking(types.Flags.Chat):
        session = self.db.sql.session()
        log.Statistic.increment(session, data.guild_id, data.author.id, types.Statistic.Chat)
    if self.cache[data.guild_id].is_tracking(db.types.Flags.Activity):
        self.db.influx.commitMessage(data.guild_id, data.channel_id, data.author.id, len(set(data.content.split(' '))))

from MFramework import register, Groups, Context, User

@register(group=Groups.ADMIN)
async def xp(ctx: Context):
    '''Management of user XP'''
    pass

@register(group=Groups.ADMIN, main=xp)
async def add(ctx: Context, user: User, xp: float) -> str:
    '''
    Add xp to user
    Params
    ------
    user:
        User that recieves XP
    xp:
        XP to add
    '''
    new = await ctx.db.supabase.increase_exp(ctx.guild_id, user.id, xp)
    return f"Added {xp} XP for a total of {new} to user {user.username}"

@register(group=Groups.ADMIN, main=xp)
async def remove(ctx: Context, user: User, xp: float) -> str:
    '''
    Remove xp from user
    Params
    ------
    user:
        Affected User
    xp:
        XP to remove
    '''
    from ..database import models
    session = ctx.db.sql.session()
    _user = models.User.fetch_or_add(session, id=user.id)
    exp = User_Experience.fetch_or_add(session, user_id=user.id, server_id=ctx.guild_id)
    exp.value -= xp
    session.commit()
    return f"Removed {xp} XP from user {user.username}"

@register(group=Groups.ADMIN, main=xp)
async def rate(ctx: Context, user: User, rate: float) -> str:
    '''
    Modify User's XP gain
    Params
    ------
    user:
        User whose gain should be modified
    rate:
        New Rate Modifier. Formula: CurrentRate * UserRate
    '''
    from ..database import models, types
    session = ctx.db.sql.session()
    _user = models.User.fetch_or_add(session, id=user.id)
    _user.add_setting(types.Setting.Exp, rate)
    session.commit()
    return f"New rate for {user.username}: {rate}"

@register(group=Groups.GLOBAL, main=xp, private_response=True, only_interaction=True)
async def progress(ctx: Context) -> Embed:
    '''
    Shows XP progress to next rank
    '''
    from ..database import models
    session = ctx.db.sql.session()
    _user = models.User.fetch_or_add(session, id=ctx.user_id)
    exp = User_Experience.fetch_or_add(session, user_id=ctx.user_id, server_id=ctx.guild_id)
    exp.value
    last = 0
    next = 0
    for x, (role, req) in enumerate(list(ctx.cache.level_roles)):
        if exp.value < req:
            if x > 0:
                last = list(ctx.cache.level_roles)[x-1][1]
            next = req
            break
    if next == 0:
        return "You have gained highest rank! Congratulations."
    required = next - last
    gained = exp.value - last
    percent = (gained / required) * 100
    progress = f"`[{'🔴' * int(percent / 5):🟢<20}]` {percent:.1f}%".replace('.0', '')
    e = (
        Embed()
        .setDescription(progress)
        .setAuthor(str(ctx.user), icon_url=ctx.user.get_avatar())
        .setColor("#8c6cff")
    )
    return e
