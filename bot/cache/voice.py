from MFramework import Guild, Snowflake, Voice_State

from bot.cache.settings import Settings
from bot.systems.voice import Timer_State


class Voice(Settings):
    voice: dict[Snowflake, dict[Snowflake, Timer_State]]
    """Mapping of Channel IDs to Mapping of User IDs to Unix Timestamp since user's activity is tracked"""
    voice_states: dict[Snowflake, Voice_State] = {}
    """Mapping of User IDs to Voice States data"""

    def __init__(self, **kwargs) -> None:
        self.voice = {}
        super().__init__(**kwargs)

    async def initialize(self, *, bot, guild: Guild, **kwargs):
        self.voice_states = {i.user_id: i for i in guild.voice_states}
        await self.load_voice_states(self.voice_states)

        return await super().initialize(bot=bot, guild=guild, **kwargs)

    async def load_voice_states(self, voice_states: list[Voice_State]):
        for vc in voice_states:
            member = await self.members[vc.user_id]
            if member.user.bot or not vc.channel_id:
                # Skip if User is either a bot, or channel is not set
                continue
            if vc.channel_id not in self.voice:
                # Preinitialize channel
                self.voice[vc.channel_id] = {}
            self.voice[vc.channel_id][vc.user_id] = Timer_State(self, vc.channel_id, vc.user_id)

        for channel in self.voice:
            for user in self.voice[channel]:
                await self.voice[channel][user].start()
