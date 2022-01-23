from MFramework import onDispatch, Bot, Message

@onDispatch
async def direct_message_create(self: Bot, data: Message):
    await self.cache[self.primary_guild].logging["direct_message"](data)
    if data.channel_id not in self.cache[0]:
        from MFramework.database.cache_internal.models import Collection
        self.cache[data.guild_id][data.channel_id] = Collection()
    self.cache[data.guild_id][data.channel_id].store(data)
