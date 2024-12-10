import time
from typing import TYPE_CHECKING, Tuple

from MFramework import Snowflake, log

from bot import database as db

if TYPE_CHECKING:
    from bot import Bot


def checkLast(ctx: "Bot", guild: Snowflake, channel: Snowflake, user: Snowflake) -> float:
    j = ctx.cache[guild].voice[channel].pop(user)
    if j > 0:
        n = time.time()
    else:
        return 0
    return n - j


async def finalize(
    ctx: "Bot", guild: Snowflake, channel: Snowflake, user: Snowflake
) -> Tuple[float, Tuple[Snowflake, float]]:
    _v = 0
    v = checkLast(ctx, guild, channel, user)
    if v != 0:
        session = ctx.db.sql.session()
        _user = await db.User.fetch_or_add(session, id=user)
        # TODO
        stat = await db.Statistic.get(
            session,
            db.Statistic.server_id == guild,
            db.Statistic.user_id == user,
            db.Statistic.type == db.types.Statistic.Voice,
        )
        stat.value += int(v)
        session.commit()
        if ctx.cache[guild].is_tracking(db.types.Flags.Activity):
            ctx.db.influx.commitVoiceSession(guild, channel, user, v)
    log.debug(f"Removed {user} from {channel} after {v}")
    in_channel = ctx.cache[guild].voice[channel]
    if len(in_channel) == 1:
        user = list(in_channel.keys())[0]
        log.debug(f"reStarting alone {user}")
        # finalize(self, guild, channel, user)
        _v = await restartTimer(ctx, guild, channel, user)
    return v, (user, _v)


def startTimer(ctx: "Bot", guild: Snowflake, channel: Snowflake, user: Snowflake) -> None:
    if ctx.cache[guild].is_tracking(db.types.Flags.Voice):
        t = time.time()
    else:
        t = 0
    ctx.cache[guild].voice[channel][user] = t
    if t > 0:
        log.debug(f"Starting Timer for {user} in {channel}")


async def restartTimer(ctx: "Bot", guild: Snowflake, channel: Snowflake, user: Snowflake, flag: int = 0) -> float:
    c = ctx.cache[guild].voice[channel]
    v = (0, 0)
    if user in c:
        if c[user] > 0:
            log.debug(f"Finalizing Previous Timer for {user} in {channel}")
            v = await finalize(ctx, guild, channel, user)
    c[user] = flag
    log.debug(f"reStarting Timer for {user} in {channel} with {flag}")
    return v[0]
