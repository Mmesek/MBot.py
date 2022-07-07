from datetime import timedelta

from MFramework import Bot, Guild_Member_Add, Message, onDispatch

from . import models
from .internal import log_action


@onDispatch
async def guild_member_add(self: Bot, data: Guild_Member_Add):
    _last = self.cache[data.guild_id].last_join
    self.cache[data.guild_id].last_join = data.user.id

    if _last and abs(_last.as_date - data.user.id.as_date) < timedelta(days=1):
        try:
            log_action(
                cache=self.cache[data.guild_id],
                logger="auto_mod",
                user_id=data.user.id,
                reason="Possible Raid: Account Age",
                dm_reason="Possible Raid",
                type=models.Types.Kick,
            )
        except:
            pass

        await self.remove_guild_member(data.guild_id, data.user.id, "Possible Raid")
        try:
            await self.remove_guild_member(data.guild_id, _last, "Possible Raid")
        except:
            pass
        return True


@onDispatch
async def direct_message_create(self: Bot, data: Message):
    guilds = list(
        filter(
            lambda x: data.author.id in x.members,
            [
                cache
                for cache in self.cache.values()
                if type(cache) is not dict and cache.logging.get("direct_message", None)
            ],
        )
    )

    guild_id = guilds[0].guild_id if len(guilds) == 1 else self.primary_guild

    if "find this life-changing" in data.content:
        try:
            log_action(
                cache=self.cache[guild_id],
                logger="auto_mod",
                user_id=data.author.id,
                reason="Possible Raid: Modmail",
                dm_reason="Possible Raid",
                type=models.Types.Kick,
            )
        except:
            pass

        await self.remove_guild_member(guild_id, data.author.id, reason="Possible Raid")
        return True
