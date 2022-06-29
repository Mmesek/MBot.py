from MFramework import Bot, Snowflake, Voice_Server_Update, Voice_State, onDispatch

from ..utils import levels, timers


async def _handle_dynamic_channel(self: Bot, data: Voice_State):
    template = self.cache[data.guild_id].dynamic_channels[data.channel_id]
    if "buffer" in template:
        await self.move_guild_member(
            data.guild_id, data.user_id, template["buffer"], f"Moved {data.member.user.username} to channel"
        )
    else:
        count = len(self.cache[data.guild_id].dynamic_channels["channels"]) + 1

        new_channel = await self.create_guild_channel(
            data.guild_id,
            template["name"] + f" #{count}",
            2,
            None,
            template["bitrate"],
            template["user_limit"],
            None,
            template["position"],
            template["permission_overwrites"],
            template["parent_id"],
            False,
            "Generated Channel",
        )
        await self.move_guild_member(
            data.guild_id, data.user_id, new_channel.id, f"Moved {data.member.user.username} to generated channel"
        )
        data.channel_id = new_channel.id
        self.cache[data.guild_id].dynamic_channels["channels"] += [new_channel.id]
    return data


async def _user_left_voice_channel(self: Bot, data: Voice_State, channel: Snowflake, track_voice: bool = False):
    if track_voice:
        t = timers.finalize(self, data.guild_id, channel, data.user_id)
        await self.cache[data.guild_id].logging["voice"](data, channel, int(t[0]))
        if t[1][1] != 0:
            _data = data
            _data.user_id = t[1][0]
            await self.cache[data.guild_id].logging["voice"](_data, channel, int(t[1][1]))
            if int(((t[1][1]) / 60) / 10) > 1:
                await levels.handle_exp(self, _data)
        if int((t[0] / 60) / 10) > 1:
            await levels.handle_exp(self, data)
    else:
        timers.checkLast(self, data.guild_id, channel, data.user_id)
        await self.cache[data.guild_id].logging["voice"](data, channel)


async def _handle_voice_activity(self: Bot, data: Voice_State):
    from MFramework.database.alchemy.types import Flags

    track_voice = self.cache[data.guild_id].is_tracking(Flags.Voice)
    v = self.cache[data.guild_id].voice
    moved = False
    if not data.channel_id:
        data.channel_id = 0

    if data.channel_id > 0:  # User is on the Voice Channel
        for channel in v:
            if data.user_id in v[channel]:  # User is in cached channel
                if channel != data.channel_id:  # Moved to another channel
                    moved = True
                    await _user_left_voice_channel(self, data, channel, track_voice)
                    # if channel in self.cache[data.guild_id].dynamic_channels['channels'] and v[channel] == {}:
                    #    await self.delete_close_channel(channel, "Deleting Empty Generated Channel")
                    #    self.cache[data.guild_id].dynamic_channels['channels'].remove(channel)
                else:  # Channel is same as before
                    if track_voice:
                        if data.self_deaf or data.self_mute:  # User is now muted
                            timers.restartTimer(self, data.guild_id, data.channel_id, data.user_id, -1)
                        elif (not data.self_deaf and not data.self_mute) and v[data.channel_id][
                            data.user_id
                        ] == -1:  # User is not muted anymore
                            if len(v[data.channel_id]) > 1:
                                timers.startTimer(self, data.guild_id, data.channel_id, data.user_id)  # Unmuted
                            else:
                                timers.restartTimer(self, data.guild_id, data.channel_id, data.user_id)  # Unmuted Alone
                    return

        if data.channel_id not in v:  # Init channel
            v[data.channel_id] = {}

        if len(v[data.channel_id]) >= 1 and data.user_id not in v[data.channel_id]:  # New person Joined channel
            if track_voice:
                if data.self_deaf or data.self_mute:
                    timers.restartTimer(self, data.guild_id, data.channel_id, data.user_id, -1)  # Muted Joined
                else:
                    timers.startTimer(self, data.guild_id, data.channel_id, data.user_id)  # Unmuted Joined
                for u in v[data.channel_id]:
                    if v[data.channel_id][u] == 0:  # There was someone on VC without Timer
                        timers.startTimer(self, data.guild_id, data.channel_id, u)
            else:
                timers.startTimer(self, data.guild_id, data.channel_id, data.user_id)
            if not moved:
                await self.cache[data.guild_id].logging["voice"](data)

        elif len(v[data.channel_id]) == 0:  # Joined empty channel
            if track_voice:
                if data.self_deaf or data.self_mute:
                    timers.restartTimer(
                        self, data.guild_id, data.channel_id, data.user_id, -1
                    )  # Joined Empty Channel Muted
                else:
                    timers.restartTimer(
                        self, data.guild_id, data.channel_id, data.user_id
                    )  # Joined Empty Channel unmuted
            else:
                timers.startTimer(self, data.guild_id, data.channel_id, data.user_id)
            if not moved:
                await self.cache[data.guild_id].logging["voice"](data)

        # else: #Not a channel switch event, possibly happening if user was already on a channel somehow.
        # pass

    else:  # User is not on Voice channel anymore
        for channel in v:
            if data.user_id in v[channel]:
                if data.channel_id == -1:
                    self.cache[data.guild_id].afk[data.user_id] = channel

                await _user_left_voice_channel(self, data, channel, track_voice)

                # if channel in self.cache[data.guild_id].dynamic_channels['channels'] and v[channel] == {}:
                #    await self.delete_close_channel(channel, "Deleting Empty Generated Channel")
                #    self.cache[data.guild_id].dynamic_channels['channels'].remove(channel)
                #    v.pop(channel)
                #    return


@onDispatch
async def voice_state_update(ctx: Bot, state: Voice_State):
    if state.member.user.bot:
        if state.user_id == ctx.user_id:
            state.cache[ctx.guild_id].connection.session_id = state.session_id
        return
    if state.channel_id in ctx.cache[state.guild_id].disabled_channels and not any(
        r in state.member.roles for r in ctx.cache[state.guild_id].disabled_roles
    ):
        if state.channel_id == ctx.cache[state.guild_id].afk_channel:
            state.channel_id = -1
        else:
            state.channel_id = 0
    # if state.channel_id in ctx.cache[state.guild_id].dynamic_channels:
    #    state = await _handle_dynamic_channel(ctx, state)
    if ctx.cache[state.guild_id].voice_link:
        r = ctx.cache[state.guild_id].voice_link
        if state.channel_id and r not in state.member.roles:
            await ctx.add_guild_member_role(state.guild_id, state.user_id, r, "Voice Role")
        elif not state.channel_id and r in state.member.roles:
            await ctx.remove_guild_member_role(state.guild_id, state.user_id, r, "Voice Role")
    await _handle_voice_activity(ctx, state)  # TODO


@onDispatch
async def voice_server_update(ctx: Bot, data: Voice_Server_Update):
    await ctx.cache[data.guild_id].connection.connect(data.token, data.guild_id, data.endpoint, ctx.user_id)
