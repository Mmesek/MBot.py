from MFramework import onDispatch, Bot, Channel

@onDispatch
async def thread_create(self: Bot, data: Channel):
    self.cache[data.guild_id].threads[data.id] = data.parent_id

@onDispatch
async def thread_update(self: Bot, data: Channel):
    if data.thread_metadata.archived:
        self.cache[data.guild_id].last_messages.pop(data.id, None)