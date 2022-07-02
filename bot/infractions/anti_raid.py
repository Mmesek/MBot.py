from datetime import timedelta

from MFramework import Bot, Guild_Member_Add, onDispatch

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
