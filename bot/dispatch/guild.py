from MFramework import onDispatch, Bot, Guild_Member_Add, Guild_Member_Remove, log

@onDispatch
async def guild_member_add(self: Bot, data: Guild_Member_Add):
    _last = self.cache[data.guild_id].last_join
    from datetime import timedelta
    if _last and abs(_last.as_date - data.user.id.as_date) < timedelta(days=1):
        from ..commands_slash.infractions import InfractionTypes
        _ = self.cache[data.guild_id].logging.get("auto_mod", None)
        if _:
            await _(
                guild_id=data.guild_id,
                channel_id=None,
                message_id=None,
                moderator=self.cache[data.guild_id].bot.user,
                user_id=data.user.id,
                reason="Possible Raid",
                duration=None,
                type=InfractionTypes.Kick
            )
            try:
                r = await _.log_dm(
                    type=InfractionTypes.Kick, 
                    guild_id=data.guild_id,
                    user_id=data.user.id,
                    reason="Possible Raid",
                    duration=None
                )
            except Exception as ex:
                r = None
        await self.remove_guild_member(data.guild_id, data.user.id, "Possible Raid")
        try:
            await self.remove_guild_member(data.guild_id, _last, "Possible Raid")
        except:
            pass
        self.cache[data.guild_id].last_join = data.user.id
        return True

    self.cache[data.guild_id].last_join = data.user.id
    await self.db.influx.influxMember(data.guild_id, data.user.id, True, data.joined_at)

@onDispatch
async def guild_member_remove(self: Bot, data: Guild_Member_Remove):
    await self.db.influx.influxMember(data.guild_id, data.user.id, False)

@onDispatch(event='guild_member_add')
async def initial_welcome_message(self: Bot, data: Guild_Member_Add):
    if data.guild_id != 289739584546275339:
        return
    welcome_message = '''
Hey! Welcome to *the official Dying Light server*! I'm a **community**-made bot that forwards messages you send to me directly to __Server Moderation__ Team! 

Feel free to message me whenever you have an issue, suggestion or really anything related to the Discord **server**. 
Please do not DM moderation directly for these matters.

Note however, that currently __no member of server moderation or administration works for Techland__. 
Only people with `_Techland` in their names *and* role Techland work there.

However, If you need to reach Techland, either contact the Community Manager <@210060521238560768> directly; send them an email to `support@techland.pl` or use their website https://support.techland.pl/

Under any circumstances, do **not** DM or @ping ANY other Techland employees than <@210060521238560768> on server.
'''
    try:
        channel = await self.create_dm(data.user.id)
        await self.create_message(channel.id, welcome_message)
    except:
        log.debug("Couldn't DM welcome message to %s. Possibly due to user blocking DMs from non-friends")
