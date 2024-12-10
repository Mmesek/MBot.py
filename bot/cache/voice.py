import time

from MFramework import Guild, Snowflake, Voice_State, log

from bot import database as db
from bot.cache.settings import Settings
from bot.utils.timers import startTimer


class Voice(Settings):
    voice: dict[Snowflake, dict[Snowflake, float]]
    """Mapping of Channel IDs to Mapping of User IDs to Unix Timestamp since user's activity is tracked"""
    voice_states: dict[Snowflake, Voice_State] = {}
    """Mapping of User IDs to Voice States data"""

    def __init__(self, **kwargs) -> None:
        self.voice = {}
        super().__init__(**kwargs)

    async def initialize(self, *, bot, guild: Guild, **kwargs):
        self.voice_states = {i.user_id: i for i in guild.voice_states}
        for vs in guild.voice_states:
            if not vs.self_mute and not vs.self_deaf:
                # Don't start if users are muted! TODO
                startTimer(bot, guild, vs.channel_id, vs.user_id)
        if self.is_tracking(db.types.Flags.Voice):
            await self.load_voice_states(guild.voice_states)
        return await super().initialize(bot=bot, guild=guild, **kwargs)

    async def load_voice_states(self, voice_states: list[Voice_State]):
        for vc in voice_states:
            member = await self.members[vc.user_id]
            if member.user.bot or not vc.channel_id:
                continue
            if vc.channel_id not in self.voice:
                self.voice[vc.channel_id] = {}
            if vc.user_id not in self.voice[vc.channel_id]:
                log.debug("init of user %s", vc.user_id)
                if vc.self_deaf:
                    i = -1
                elif len(self.voice[vc.channel_id]) > 0:
                    i = time.time()
                else:
                    i = 0
                self.voice[vc.channel_id][vc.user_id] = i
        for c in self.voice:
            u = list(self.voice[c].keys())[0]
            if len(self.voice[c]) == 1 and u > 0:
                self.voice[c][u] = 0
            elif len(self.voice[c]) > 1 and u == 0:
                self.voice[c][u] = time.time()

    def cached_voice(self, data: Voice_State):
        join = self.voice[data.channel_id].pop(data.user_id, None)
        if join is not None:
            return time.time() - join
        return 0
