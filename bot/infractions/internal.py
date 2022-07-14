from datetime import timedelta

from MFramework import Bot, Cache, Snowflake, User

from . import models


async def log_action(
    cache: Cache,
    logger: str,
    user_id: Snowflake,
    reason: str,
    type: models.Types,
    dm_reason: str = None,
    moderator: User = None,
    guild_id: Snowflake = None,
    channel_id: Snowflake = None,
    message_id: Snowflake = None,
    duration: timedelta = None,
):
    _ = cache.logging.get(logger, None)
    if not _:
        return

    await _(
        guild_id=guild_id or cache.guild_id,
        channel_id=channel_id,
        message_id=message_id,
        moderator=moderator or cache.bot.user,
        user_id=user_id,
        reason=reason,
        duration=duration,
        type=type,
    )

    await _.log_dm(
        type=type, guild_id=guild_id or cache.guild_id, user_id=user_id, reason=dm_reason or reason, duration=duration
    )


async def kick_user(bot: Bot, guild_id: int, user_id: int, reason: str = "Possible Raid", dm_reason="Possible Raid"):
    try:
        await log_action(
            cache=bot.cache[guild_id],
            logger="auto_mod",
            user_id=user_id,
            reason=reason,
            dm_reason=dm_reason,
            type=models.Types.Kick,
        )
    except:
        pass

    await bot.remove_guild_member(guild_id, user_id, reason=reason)
