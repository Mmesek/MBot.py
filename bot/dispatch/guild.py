from MFramework import onDispatch, Bot, Guild_Member_Add, Guild_Member_Remove

@onDispatch
async def guild_member_add(self: Bot, data: Guild_Member_Add):
    await self.db.influx.influxMember(data.guild_id, data.user.id, True, data.joined_at)

@onDispatch
async def guild_member_remove(self: Bot, data: Guild_Member_Remove):
    await self.db.influx.influxMember(data.guild_id, data.user.id, False)
