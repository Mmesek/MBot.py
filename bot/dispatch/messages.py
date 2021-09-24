from MFramework import onDispatch, Bot, Message

import re
EMOJI = re.compile(r":\w+:")
@onDispatch(priority=4)
async def message_create(self: Bot, data: Message):
    if not data.is_empty:
        if any(i.id == self.user_id for i in data.mentions):
            await self.trigger_typing_indicator(data.channel_id)
        from .actions import responder
        for emoji in EMOJI.findall(data.content):
            await responder(self, data, emoji)

@onDispatch
async def direct_message_create(self: Bot, data: Message):
    await self.cache[self.primary_guild].logging["direct_message"](data)
    if data.channel_id not in self.cache[0]:
        from MFramework.database.cache import Cache
        self.cache[data.guild_id][data.channel_id] = Cache()
    self.cache[data.guild_id][data.channel_id].store(data)
