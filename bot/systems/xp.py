from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from MFramework import Bot, Channel, Embed, Message, Role, onDispatch
from MFramework.database.alchemy.mixins import Snowflake
from mlib.database import Base, TimestampUpdate


class User_Experience(TimestampUpdate, Base):
    server_id: Snowflake = sa.Column(
        sa.ForeignKey("Server.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True, nullable=False, default=0
    )
    user_id: Snowflake = sa.Column(
        sa.ForeignKey("User.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True, nullable=False, default=0
    )
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
        or len(set(data.content.split(" "))) < 2
    ):
        return

    last = self.cache[data.guild_id].cooldowns.has(data.guild_id, data.author.id, "ChatExp")
    if last:
        return

    role_boosts = 0
    for role in data.member.roles:
        if role in self.cache[data.guild_id].role_rates:
            role_boosts += self.cache[data.guild_id].role_rates.get(role, 0) or 0

    rate = 1 * (
        ((self.cache[data.guild_id].exp_rates.get(data.channel_id, 1.0) or 0) + role_boosts)
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
    # FIXME: Reenable user boost on SQL side?
    exp = await self.db.supabase.increase_exp(data.guild_id, data.author.id, rate)  # * boost)
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

    from ..database import log, types

    if self.cache[data.guild_id].is_tracking(types.Flags.Chat):
        session = self.db.sql.session()
        log.Statistic.increment(session, data.guild_id, data.author.id, types.Statistic.Chat)
    if self.cache[data.guild_id].is_tracking(types.Flags.Activity):
        self.db.influx.commitMessage(data.guild_id, data.channel_id, data.author.id, len(set(data.content.split(" "))))


from MFramework import Context, Groups, User, register


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
    from ..database import models

    session = ctx.db.sql.session()
    _user = models.User.fetch_or_add(session, id=user.id)
    exp = User_Experience.fetch_or_add(session, user_id=user.id, server_id=ctx.guild_id)
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
    from MFramework.database.alchemy import Channel, Role, Server, types

    session = ctx.db.sql.session()
    result = []

    if channel:
        c = Channel.fetch_or_add(session, server_id=ctx.guild_id, id=channel.id)
        previous = c.get_setting(types.Setting.Exp) or 1.0
        c.add_setting(types.Setting.Exp, rate)
        ctx.cache.exp_rates[channel.id] = rate
        result.append(("Channel", channel.name, rate, previous))
    if role:
        r = Role.fetch_or_add(session, server_id=ctx.guild_id, id=role.id)
        previous = r.get_setting(types.Setting.Exp) or 1.0
        r.add_setting(types.Setting.Exp, rate)
        ctx.cache.role_rates[role.id] = rate
        # ctx.cache.role_rates.sort(key=lambda x: x[1])
        result.append(("Role", role.name, rate, previous))
    if user:
        from ..database import models

        _user = models.User.fetch_or_add(session, id=user.id)
        previous = _user.get_setting(types.Setting.Exp) or 1.0
        _user.add_setting(types.Setting.Exp, rate)
        result.append(("User", user.username, rate, previous))
    if server:
        s = Server.fetch_or_add(session, id=ctx.guild_id)
        previous = s.get_setting(types.Setting.Exp) or 1.0
        s.add_setting(types.Setting.Exp, rate)
        ctx.cache.server_exp_rate = rate
        result.append(("Server", ctx.cache.guild.name, rate, previous))

    if not any(channel, role, user, server):
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
    from ..database import models

    session = ctx.db.sql.session()
    _user = models.User.fetch_or_add(session, id=user_id)
    exp = User_Experience.fetch_or_add(session, user_id=user_id, server_id=ctx.guild_id)
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
    e = Embed().setDescription(progress).setAuthor(str(ctx.user), icon_url=ctx.user.get_avatar()).setColor("#8c6cff")
    if ctx.permission_group.can_use(Groups.MODERATOR) and user:
        e.addField("Current XP", str(exp.value), True)
        e.addField("Remaining XP", str(next - exp.value), True)
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
        exp = User_Experience.fetch_or_add(session, user_id=user.id, server_id=ctx.guild_id)
        exp.value = 0
        session.commit()
        return f"Reseted {user.username} XP back to 0"
    except:
        return "Couldn't find specified user"
