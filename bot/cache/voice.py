import time

from MFramework import Snowflake, Voice_State, log
from MFramework.cache.guild import ObjectCollections


class Voice(ObjectCollections):
    voice: dict[Snowflake, dict[Snowflake, float]]
    """Mapping of Channel IDs to Mapping of User IDs to Unix Timestamp since user's activity is tracked"""
    voice_states: dict[Snowflake, Voice_State] = {}
    """Mapping of User IDs to Voice States data"""

    def __init__(self, **kwargs) -> None:
        # for vs in guild.voice_states:
        # from MFramework.utils.timers2 import _startTimer
        # if not vs.self_mute and not vs.self_deaf:
        #    _startTimer(self.voice_channels, vs.channel_id, vs.user_id) # Don't start if users are muted! TODO
        # self.voice_states = {i.user_id:i for i in guild.voice_states}
        self.voice = {}
        # if self.is_tracking(types.Flags.Voice):
        #    self.load_voice_states(guild.voice_states)
        super().__init__(**kwargs)

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
        join = self.voice.pop(data.user_id, None)
        if join is not None:
            return time.time() - join
        return 0
