from MFramework import onDispatch, Bot, Channel

@onDispatch
async def thread_create(self: Bot, data: Channel):
    self.cache[data.guild_id].threads[data.id] = data.parent_id
