from MFramework import onDispatch, Bot, Channel, Thread_Members_Update

@onDispatch
async def thread_create(self: Bot, data: Channel):
    self.cache[data.guild_id].threads[data.id] = data.parent_id

@onDispatch
async def thread_update(self: Bot, data: Channel):
    if data.thread_metadata.archived:
        self.cache[data.guild_id].last_messages.pop(data.id, None)

@onDispatch
async def thread_members_update(self: Bot, data: Thread_Members_Update):
    if getattr(self.cache[data.guild_id], 'thread_clean', False):
        return
    if data.id not in [938932336513396767, 938932406935773276, 938932482743627816]:
        return
    from datetime import timedelta, timezone, datetime
    members = await self.list_thread_members(data.id)
    x = 0
    if len(members) > 950:
        self.cache[data.guild_id].thread_clean = True
        for member in members:
            if x == 10:
                break
            if datetime.now(tz=timezone.utc) - member.join_timestamp > timedelta(days=1):
                await self.remove_thread_member(data.id, member.user_id, "User is too long in a thread")
                import asyncio
                await asyncio.sleep(0.8)
                x += 1
        self.cache[data.guild_id].thread_clean = False
