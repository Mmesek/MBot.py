from MFramework import Guild_Member_Add, Guild_Member_Remove, log, onDispatch
from bot import Bot


@onDispatch
async def guild_member_add(self: Bot, data: Guild_Member_Add):
    await self.db.influx.influxMember(data.guild_id, data.user.id, True, data.joined_at)


@onDispatch
async def guild_member_remove(self: Bot, data: Guild_Member_Remove):
    await self.db.influx.influxMember(data.guild_id, data.user.id, False)


@onDispatch(event="guild_member_add")
async def initial_welcome_message(self: Bot, data: Guild_Member_Add):
    welcome_message = self.cache[data.guild_id].welcome_message
    try:
        channel = await self.create_dm(data.user.id)
        await self.create_message(channel.id, welcome_message)
    except:
        log.debug("Couldn't DM welcome message to %s. Possibly due to user blocking DMs from non-friends", data.user.id)


@onDispatch(event="guild_member_add")
async def ban_appeal(self: Bot, data: Guild_Member_Add):
    if data.guild_id == 1104062636892639262:
        try:
            ban = await self.get_guild_ban(289739584546275339, data.user.id)
        except:
            try:
                channel = await self.create_dm(data.user.id)
                await self.create_message(channel.id, "You don't seem to be banned! discord.gg/dyinglight")
            except:
                log.debug("Couldn't DM kick reason to %s", data.user.id)
            await self.remove_guild_member(data.guild_id, data.user.id, "User is not Banned")
