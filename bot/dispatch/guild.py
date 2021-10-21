from MFramework import onDispatch, Bot, Guild_Member_Add, Guild_Member_Remove

@onDispatch
async def guild_member_add(self: Bot, data: Guild_Member_Add):
    _last = self.cache[data.guild_id].last_join
    from datetime import timedelta
    if _last and abs(_last.as_date - data.user.id.as_date) < timedelta(days=1):
        from ..database import types
        _ = self.cache[data.guild_id].logging.get("infraction", None)
        if _:
            await _(
                guild_id=data.guild_id,
                channel_id=None,
                message_id=None,
                moderator=self.cache[data.guild_id].bot.user,
                user_id=data.user.id,
                reason="Possible Raid",
                duration=None,
                type=types.Infraction.Kick
            )
            try:
                r = await _.log_dm(
                    type=types.Infraction.Kick, 
                    guild_id=data.guild_id,
                    user_id=data.user.id,
                    reason="Possible Raid",
                    duration=None
                )
            except Exception as ex:
                r = None
        await self.remove_guild_member(data.guild_id, data.user.id, "Possible Raid")
        self.cache[data.guild_id].last_join = data.user.id
        return True

    self.cache[data.guild_id].last_join = data.user.id
    await self.db.influx.influxMember(data.guild_id, data.user.id, True, data.joined_at)

@onDispatch
async def guild_member_remove(self: Bot, data: Guild_Member_Remove):
    await self.db.influx.influxMember(data.guild_id, data.user.id, False)
