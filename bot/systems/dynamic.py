import asyncio
from datetime import timedelta

from mdiscord.exceptions import BadRequest
from MFramework import Bot, Channel, Channel_Types, Voice_State, log, onDispatch

CHANNEL_LIMIT = 40
DYNAMIC_NAME = ["create", "créer"]
COOLDOWN_NAME = "dynamic_channel"
COOLDOWN_DELTA = timedelta(minutes=15)


@onDispatch(event="voice_state_update", priority=130)
async def cleanup_dynamic_channel(self: Bot, data: Voice_State):
    """Deletes Dynamic channel if it's empty"""
    v = self.cache[data.guild_id].voice
    removed = set()
    await asyncio.sleep(3)
    c = self.cache[data.guild_id].dynamic_channels.copy()

    for user, channel in c.items():
        if channel not in v or not v[channel] or len(v[channel]) == 0:
            log.debug("Dynamic Channel %s is empty - Cleaning up", channel)
            try:
                await self.delete_close_channel(channel, "Deleting Empty Generated Channel")
            except:
                pass
            removed.add(user)
            v.pop(channel, None)

    for user in removed:
        self.cache[data.guild_id].dynamic_channels.pop(user, None)


@onDispatch(event="voice_state_update", priority=15)
async def dynamic_channel(self: Bot, data: Voice_State) -> bool:
    """Creates Dynamic Channel"""
    channel: Channel = await self.cache[data.guild_id].channels[data.channel_id]
    if (
        not channel
        or all(NAME not in channel.name.lower() for NAME in DYNAMIC_NAME)
        or channel.id in self.cache[data.guild_id].dynamic_channels
    ):
        return

    if (
        self.cache[data.guild_id].dynamic_channels.get(data.user_id, None) in self.cache[data.guild_id].voice
        or await self.cache[data.guild_id].cooldowns.get(data.guild_id, data.user_id, COOLDOWN_NAME)
        or len(self.cache[data.guild_id].dynamic_channels) >= CHANNEL_LIMIT
    ):
        log.debug("User %s has existing cooldown or already generated channel. Moving or Disconnecting", data.user_id)
        gc = self.cache[data.guild_id].dynamic_channels.get(data.user_id, None)
        await self.modify_guild_member(data.guild_id, data.user_id, channel_id=gc, mute=None, deaf=None)
        if not gc:
            dm = await self.create_dm(data.user_id)
            await self.create_message(dm.id, "You can't currently create new Voice Channel! Try again later")
        return True

    log.debug("User %s joined template channel", data.user_id)
    gc = self.cache[data.guild_id].dynamic_channels
    if gc:
        c = [
            int(await self.cache[data.guild_id].channels.get(gc[u], Channel()).name.split(" ", 1)[0].strip("#"))
            for u in gc
        ]
        count = (sorted(set(range(1, c[-1] + 2)).difference(c)) or [1])[0]
    else:
        count = 1

    name = data.member.nick or data.member.user.username

    await self.cache[data.guild_id].cooldowns.store(data.guild_id, data.user_id, COOLDOWN_NAME, expire=COOLDOWN_DELTA)
    new_channel = await self.create_guild_channel(
        guild_id=data.guild_id,
        name=f'#{count} {channel.name.split(":",1)[-1] if ":" in channel.name else name}',
        type=Channel_Types.GUILD_VOICE.value,
        bitrate=channel.bitrate,
        user_limit=channel.user_limit,
        position=channel.position,
        permission_overwrites=channel.permission_overwrites,
        parent_id=channel.parent_id,
        reason=f"Generated Channel for user {data.member.user.username}",
    )
    self.cache[data.guild_id].dynamic_channels[data.user_id] = new_channel.id
    try:
        await self.modify_guild_member(
            data.guild_id,
            data.user_id,
            mute=None,
            deaf=None,
            channel_id=new_channel.id,
            reason=f"Moved {data.member.user.username} to generated channel",
        )
        log.debug("Moved User %s from template channel to created %s", data.user_id, new_channel.id)
    except BadRequest as ex:
        log.debug(ex)

    return True
