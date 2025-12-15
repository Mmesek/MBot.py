from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from MFramework import Channel, Embed, Groups, Message, Role, User, onDispatch, register
from MFramework.database.alchemy.mixins import Snowflake
from mlib.database import Base, TimestampUpdate
from sqlalchemy.orm import Mapped, mapped_column as Column

from bot import Bot, Context
from bot.database import models


class User_Experience(TimestampUpdate, Base):
    server_id: Mapped[Snowflake] = Column(
        sa.ForeignKey("Server.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True, nullable=False, default=0
    )
    user_id: Mapped[Snowflake] = Column(
        sa.ForeignKey("User.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True, nullable=False, default=0
    )
    type: Mapped[int] = Column(nullable=False, default=0)
    value: Mapped[float] = Column(nullable=False, default=0)


@onDispatch(event="message_create")
async def exp(self: Bot, data: Message):
    if (
        data.channel_id in self.cache[data.guild_id].disabled_channels
        or any(r in data.member.roles for r in self.cache[data.guild_id].disabled_roles)
        or len(set(data.content.split(" "))) < 2
    ):
        return

    last = await self.cache[data.guild_id].cooldowns.has(data.guild_id, data.author.id, "ChatExp")
    if last:
        return

    role_boosts = 0
    for role in data.member.roles:
        if role in self.cache[data.guild_id].role_rates:
            role_boosts += self.cache[data.guild_id].role_rates.get(role, 0) or 0

    rate = 1 * (
        ((self.cache[data.guild_id].channel_rates.get(data.channel_id, 1.0) or 0) + role_boosts)
        * self.cache[data.guild_id].server_exp_rate
    )
    if (
        hasattr(self.cache[data.guild_id], "boosted_until")
        and datetime.now(timezone.utc) <= self.cache[data.guild_id].boosted_until
    ):
        rate *= self.cache[data.guild_id].boosted_rate

    # from MFramework.database import alchemy as db

    # user = models.User.fetch_or_add(session, id=data.author.id)
    # boost = user.get_setting(db.types.Setting.Exp) or 1.0
    # FIXME: Re-enable user boost on SQL side?
    exp = await self.db.supabase.increase_exp(data.guild_id, data.author.id, rate)  # * boost)
    await self.cache[data.guild_id].cooldowns.store(data.guild_id, data.author.id, "ChatExp")

    previous_level = None
    level_up = None

    for role, req in self.cache[data.guild_id].level_roles:
        if role in data.member.roles:
            if exp < req:
                await self.remove_guild_member_role(data.guild_id, data.author.id, role, "Level Role")
            previous_level = role
        if exp >= req:
            level_up = role
    from bot.database import log, types

    if self.cache[data.guild_id].is_tracking(types.Flags.Chat):
        session = self.db.sql.session()
        log.Statistic.increment(session, data.guild_id, data.author.id, types.Statistic.Chat)
    if self.cache[data.guild_id].is_tracking(types.Flags.Activity):
        self.db.influx.commitMessage(data.guild_id, data.channel_id, data.author.id, len(set(data.content.split(" "))))

    if level_up == previous_level:
        return

    if level_up:
        await self.add_guild_member_role(data.guild_id, data.author.id, level_up, "Level Role")
    if previous_level:
        await self.remove_guild_member_role(data.guild_id, data.author.id, previous_level, "Level Role")


@register(group=Groups.ADMIN)
async def xp(ctx: Context):
    """Management of user XP"""
    pass


@register(group=Groups.ADMIN, main=xp)
async def add(ctx: Context, user: User, xp: float) -> str:
    """
    Add xp to user
    Params
    ------
    user:
        User that recieves XP
    xp:
        XP to add
    """
    new = await ctx.db.supabase.increase_exp(ctx.guild_id, user.id, xp)
    return f"Added {xp} XP for a total of {new} to user {user.username}"


@register(group=Groups.ADMIN, main=xp)
async def remove(ctx: Context, user: User, xp: float) -> str:
    """
    Remove xp from user
    Params
    ------
    user:
        Affected User
    xp:
        XP to remove
    """

    session = ctx.db.sql.session()
    _user = await models.User.fetch_or_add(session, id=user.id)
    exp = await User_Experience.fetch_or_add(session, user_id=user.id, server_id=ctx.guild_id)
    exp.value -= xp
    session.commit()
    return f"Removed {xp} XP from user {user.username}"


@register(group=Groups.ADMIN, main=xp)
async def rate(
    ctx: Context, rate: float, channel: Channel = None, role: Role = None, user: User = None, server: bool = False
) -> str:
    """
    Manage XP Rate gains
    Params
    ------
    rate:
        XP Rate Modifier
    channel:
        Channel to modify. Formula: CurrentMultipler = DefaultRate * ChannelRate
    role:
        Role to modify. Formula: Rate = CurrentMultipler + sum(OwnedRoleRates)
    user:
        User whose gain should be modified. Formula: FinalRate = Rate * UserRate
    server:
        Whether this should affect server instead. Formula: Rate = Rate * ServerRate
    """
    session = ctx.db.sql.session()
    result = []

    if channel:
        c = await models.Channel.fetch_or_add(session, server_id=ctx.guild_id, id=channel.id)
        previous = c.exp_rate or 1.0
        c.exp_rate = rate
        ctx.cache.channel_rates[channel.id] = rate
        result.append(("Channel", channel.name, rate, previous))
    if role:
        r = await models.Role.fetch_or_add(session, server_id=ctx.guild_id, id=role.id)
        previous = r.exp_rate or 1.0
        r.exp_rate = rate
        ctx.cache.role_rates[role.id] = rate
        # ctx.cache.role_rates.sort(key=lambda x: x[1])
        result.append(("Role", role.name, rate, previous))
    if user:
        _user = await models.User.fetch_or_add(session, id=user.id)
        previous = _user.exp_rate or 1.0
        _user.exp_rate = rate
        result.append(("User", user.username, rate, previous))
    if server:
        s = await models.Server.fetch_or_add(session, id=ctx.guild_id)
        previous = s.exp_rate or 1.0
        s.exp_rate = rate
        ctx.cache.server_exp_rate = rate
        result.append(("Server", ctx.cache.guild.name, rate, previous))

    if not any([channel, role, user, server]):
        if ctx.cache.exp_rates:
            result.extend([f"[Channel] <#{k}>: {v}" for k, v in ctx.cache.exp_rates.items()])
        if ctx.cache.role_rates:
            result.extend([f"[Role] <@&{k}>: {v}" for k, v in ctx.cache.role_rates.items()])
        if ctx.cache.server_exp_rate and ctx.cache.server_exp_rate != 1.0:
            result.extend([f"[Server] {ctx.cache.guild.name}: {ctx.cache.server_exp_rate}"])
        return "\n".join(result)

    session.commit()
    return "\n".join(["Rate for [{}] {} changed: {} from {}".format(*i) for i in result]) or "Nothing selected"


@register(group=Groups.GLOBAL, main=xp, private_response=True, only_interaction=True)
async def progress(ctx: Context, user: User = None) -> Embed:
    """
    Shows XP progress to next rank
    Params
    ------
    user:
        User's XP progress to show
    """
    user_id = ctx.user_id if not user else user.id
    user = ctx.user if not user else user

    session = ctx.db.sql.session()
    _user = await models.User.fetch_or_add(session, id=user_id)
    exp = await User_Experience.fetch_or_add(session, user_id=user_id, server_id=ctx.guild_id)
    last = 0
    next = 0
    for x, (role, req) in enumerate(list(ctx.cache.level_roles)):
        if exp.value < req:
            if x > 0:
                last = list(ctx.cache.level_roles)[x - 1][1]
            next = req
            break
    if next == 0:
        return "You have gained highest rank! Congratulations."
    required = next - last
    gained = exp.value - last
    percent = (gained / required) * 100
    progress = f"`[{'🔴' * int(percent / 6.5):🟢<15}]` {percent:.1f}%".replace(".0", "")
    e = Embed().set_description(progress).set_author(str(user), icon_url=user.get_avatar()).set_color("#8c6cff")

    role_boosts = []
    _boost = 0
    for role in ctx.member.roles:
        if role in ctx.cache.role_rates:
            _role = ctx.cache.role_rates.get(role, 0) or 0
            _boost += _role
            if _role:
                role_boosts.append(f"<@&{role}>: {_role}")

    if len(role_boosts):
        e.add_field(f"Current Role Boosts ({_boost})", "\n".join(role_boosts))

    if ctx.permission_group.can_use(Groups.MODERATOR) and user:
        e.add_field("Current XP", str(exp.value), True)
        e.add_field("Remaining XP", str(next - exp.value), True)
    e.set_timestamp(exp.timestamp)
    return e


@register(group=Groups.ADMIN, main=xp, only_interaction=True)
async def boost(ctx: Context, duration: timedelta = timedelta(hours=1), rate: float = 2.0):
    """
    Boost XP gain for a period of time
    Params
    ------
    duration:
        Duration for how long boost should last. Default is 1 hour.
    rate:
        Boosted rate. Default is x2.
    """
    # TODO: Add config to boost per channel/server and reflect in cache properly
    ctx.cache.boosted_until = datetime.now(timezone.utc) + duration
    ctx.cache.boosted_rate = rate
    return f"Boosted all XP gains on server by {rate} for {duration}!"


@register(group=Groups.ADMIN, main=xp, only_interaction=True)
async def reset(ctx: Context, user: User):
    """
    Reset user XP
    Params
    ------
    user:
        User's XP you want to reset
    """
    session = ctx.db.sql.session()
    try:
        exp = await User_Experience.fetch_or_add(session, user_id=user.id, server_id=ctx.guild_id)
        exp.value = 0
        session.commit()
        return f"Reset {user.username} XP back to 0"
    except:
        return "Couldn't find specified user"
