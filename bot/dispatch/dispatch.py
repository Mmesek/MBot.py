from MFramework import Activity, Activity_Types, Bot, Presence_Update, onDispatch


@onDispatch
async def presence_update(self: Bot, data: Presence_Update):
    if data.guild_id == 0 or data.user.bot or (data.client_status.web != ""):
        return
    from MFramework.database.alchemy.types import Flags

    if self.cache[data.guild_id].is_tracking(Flags.Presence):
        cached = self.cache[data.guild_id].presence.get(data.user.id, None)
        if cached and (
            len(data.activities) == 0
            or (len(cached.activities) > 0 and data.activities[0].name != cached.activities[0].name)
        ):
            s = self.cache[data.guild_id].presence.pop(data.user.id)
            elapsed = 0  # TODO
            try:
                _name = s.activities[0].name
                self.db.influx.commitPresence(data.guild_id, data.user.id, _name, elapsed)
            except:
                pass
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
        if not hasattr(self, "logged_streams"):
            self.logged_streams = {}
        if self.logged_streams.get(data.user.id) == stream.created_at:
            return
        self.logged_streams[data.user.id] = stream.created_at
        await self._log(f"<@{data.user.id}> właśnie transmituje {stream.state} na [{stream.name}]({stream.url})!")
