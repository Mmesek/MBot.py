from MFramework import onDispatch, Bot, Ready, log

@onDispatch
async def ready(self: Bot, ready: Ready):
    self.session_id = ready.session_id
    self.user_id = ready.user.id
    self.username = ready.user.username
    import time
    self.start_time = time.time()
    log.info("Connected as %s", ready.user.username)

from MFramework import Presence_Update, Activity_Types, Activity

@onDispatch
async def presence_update(self: Bot, data: Presence_Update):
    if data.guild_id == 0 or data.user.bot or (data.client_status.web != ''):
        return
    from MFramework.database.alchemy.types import Flags
    if self.cache[data.guild_id].is_tracking(Flags.Presence):
        if (
            data.user.id in self.cache[data.guild_id].presence 
            and (len(data.activities) == 0 
                or data.activities[0].name != self.cache[data.guild_id].presence[data.user.id].activities[0].name)
        ):
            s = self.cache[data.guild_id].presence.pop(data.user.id)
            elapsed = 0 #TODO
            self.db.influx.commitPresence(data.guild_id, data.user.id, s[0], elapsed)
        if (
            data.user.id not in self.cache[data.guild_id].presence 
            and len(data.activities) > 0 
            and data.activities[0].type == 0 
            and data.activities[0].name is not None
        ):
            self.cache[data.guild_id].presence.store(data)

    for stream in filter(lambda x: x.type == Activity_Types.STREAMING, data.activities):
        if stream.state in self.cache[data.guild_id].tracked_streams:
            await self.cache[data.guild_id].logging["stream"](data, stream)
    
    for presence_name, role in self.cache[data.guild_id].presence_roles.items():
        if any(i.type == Activity_Types.GAME.value and i.name == presence_name for i in data.activities):
            await self.add_guild_member_role(data.guild_id, data.user.id, role, "Presence Role")
            break

from MFramework.utils.log import Log
class Stream(Log):
    username = "Stream Log"
    async def log(self, data: Presence_Update, stream: Activity):
        if not hasattr(self, 'logged_streams'):
            self.logged_streams = {}
        if self.logged_streams.get(data.user.id) == stream.created_at:
            return
        self.logged_streams[data.user.id] = stream.created_at
        await self._log(f"<@{data.user.id}> właśnie transmituje {stream.state} na [{stream.name}]({stream.url})!")