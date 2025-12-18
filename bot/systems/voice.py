import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from MFramework import Snowflake, Voice_State, log, onDispatch

from bot import database as db
from bot.cache.voice import Voice

if TYPE_CHECKING:
    from bot import Bot


@dataclass
class Timer_State:
    _cache: Voice
    _channel: Snowflake
    _user: Snowflake
    _start: float = 0

    def _is_tracking(self) -> bool:
        """Check if tracking Voice activity is enabled"""
        if self._cache.is_tracking(db.types.Flags.Voice):
            return True

    def _is_not_empty(self) -> bool:
        """Check if Channel is not empty"""
        if len(self._cache.voice[self._channel]) > 0:
            return True

    def _is_not_muted(self) -> bool:
        """Check if User is not muted"""
        user_state = self._cache.voice_states[self._user]
        if not user_state.self_mute and not user_state.self_deaf:
            return True

    def _get_elapsed(self) -> float:
        """Get elapsed time since timer started"""
        return time.time() - self._start

    async def _save(self, ctx: "Bot", elapsed: float):
        """
        Save elapsed time to database.
        Params
        ------
        ctx:
            Bot instance with access to database & cache
        elapsed:
            Elapsed time to save
        """
        if elapsed > 0:
            session = ctx.db.sql.session()
            _user = await db.User.fetch_or_add(session, id=self._user)
            stat = await db.Statistic.get(
                session,
                db.Statistic.server_id == self._cache.guild_id,
                db.Statistic.user_id == self._user,
                db.Statistic.type == db.types.Statistic.Voice,
            )
            stat.value += int(elapsed)
            await session.commit()
            if ctx.cache[self._cache.guild_id].is_tracking(db.types.Flags.Activity):
                ctx.db.influx.commitVoiceSession(self._cache.guild_id, self._channel, self._user, elapsed)

    async def _check_remaining_users(self, ctx: "Bot"):
        """Check if there's a remaining user in a channel & restart"""
        in_channel = self._cache.voice[self._channel]
        if len(in_channel) == 1:
            last_user = list(in_channel.keys())[0]
            log.debug(f"reStarting {last_user}")
            await self._cache.voice[self._channel][last_user]._restart(ctx)

    async def _restart(self, ctx: "Bot") -> None:
        """Check eligibility again"""
        if self._user in self._cache.voice[self._channel]:
            log.debug(f"Finalizing Previous Timer for {self._user} in {self._channel}")
            await self.stop(ctx)
        log.debug(f"reStarting Timer for {self._user} in {self._channel}")
        await self.start(ctx)

    async def start(self, ctx: "Bot") -> None:
        """Start timer if eligible. Restart timer of previously alone user"""
        if self._is_tracking() and self._is_not_empty() and self._is_not_muted():
            self._start = time.time()
        else:
            self._start = 0

        if self._start > 0:
            log.debug(f"Starting Timer for {self._user} in {self._channel}")

        if self._user not in self._cache.voice[self._channel]:
            self._cache.voice[self._channel][self._user] = self
        await self._check_remaining_users(ctx)

    async def stop(self, ctx: "Bot"):
        """Stop timer and save elapsed time. Restart timer of alone user"""
        value = self._get_elapsed()
        if value > 0:
            await self._save(ctx, value)
            self._start = 0
            log.debug(f"Removed {self._user} from {self._channel} after {value}")
        self._cache.voice[self._channel].pop(self._user, None)
        await self._check_remaining_users(ctx)
        return value


@onDispatch(event="voice_state_update")
async def track_voice_state(ctx: Bot, state: Voice_State):
    """
    Checks if user is not a bot.
    Checks if channel is not disabled & user doesn't have disabled roles & channel is not AFK.
    Stops previous voice tracking Timer if user was in a different channel before.
    Restarts previous voice tracking Timer if user's mute state changed.
    Updates voice state cache.
    Starts voice tracking Timer if user wasn't in that channel before.
    Logs voice state change & elapsed time.
    """
    if state.member.user.bot:
        return

    if (
        state.channel_id in ctx.cache[state.guild_id].disabled_channels
        or any(r in state.member.roles for r in ctx.cache[state.guild_id].disabled_roles)
        or state.channel_id == ctx.cache[state.guild_id].afk_channel
    ):
        state.channel_id = 0

    voice_cache = ctx.cache[state.guild_id].voice
    if state.channel_id not in voice_cache:
        voice_cache[state.channel_id] = {}

    _channel = None
    for channel in voice_cache:
        if state.user_id in voice_cache[channel]:  # User is cached
            cached_state = ctx.cache[state.guild_id].voice_states[state.user_id]
            if channel != state.channel_id:  # Moved to another channel
                elapsed = await voice_cache[channel][state.user_id].stop(ctx)
                _channel = channel
            elif state.self_mute != cached_state.self_mute or state.self_deaf != cached_state.self_deaf:  # Mute changed
                await voice_cache[channel][state.user_id].stop()

    ctx.cache[state.guild_id].voice_states[state.user_id] = state
    elapsed = None
    if state.user_id not in voice_cache[state.channel_id]:
        voice_cache[state.channel_id][state.user_id] = Timer_State(voice_cache, state.channel_id, state.user_id)
        await voice_cache[state.channel_id][state.user_id].start()

    await ctx.cache[state.guild_id].logging["voice"](state, _channel or "", elapsed)
