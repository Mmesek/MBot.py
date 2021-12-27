from typing import List, Tuple, Union
from datetime import datetime, timedelta, timezone

from MFramework import register, Groups, Context, User, Embed, shortcut, Guild_Member, Snowflake, Message, Attachment, Guild_Ban_Add, Guild_Ban_Remove
from MFramework.utils.log import Log
from ..database import types, models
#/infraction 
#  | | |---- InfractionType
#  | |           |--------- [User] [reason] [duration]
#  | |------ list           [User]
#  |-------- counter
#                |--------- [User] increase [reason]
#                |--------- [User] decrease [reason]
#TODO:
# - Timeouts
# - Timeouts instead of mutes
# - Infraction "weight" (0.1, 0.5, 1.0, 1.5, 2, etc)
#TODO:
# Each infraction as separate command instead of choice type?
# move everything to infraction command group?
# or make infraction list an info subcommand or some other?
# Perhaps alias interaction?
# List recently joined users and provide filter/sorter
@register(group=Groups.HELPER, main_only=True)
#@shortcut(name="warn", group=Groups.HELPER, type=types.Infraction.Warn, help="Warns user")
#@shortcut(name="mute", group=Groups.MODERATOR, type=types.Infraction.Mute, help="Mutes user")
#@shortcut(name="kick", group=Groups.MODERATOR, type=types.Infraction.Kick, help="Kicks user")
#@shortcut(name="ban", group=Groups.MODERATOR, type=types.Infraction.Ban, help="Bans user")
#@shortcut(name="tempmute", group=Groups.HELPER, type=types.Infraction.Temp_Mute, help="Temporarly mutes user")
#@shortcut(name="tempban", group=Groups.HELPER, type=types.Infraction.Temp_Ban, help="Temporarly bans user")
#@shortcut(name="unmute", group=Groups.MODERATOR, type=types.Infraction.Unban, help="Unmutes user")
#@shortcut(name="unban", group=Groups.ADMIN, type=types.Infraction.Unmute, help="Unbans user")
async def infraction(ctx: Context, *, type: types.Infraction, user: User=None, reason:str="", duration:timedelta=None, increase_counter: bool=True):
    '''Base command for infractions
    Params
    ------
    type:
        Type of Infraction
    user:
        User to take action upon
    reason:
        Reason of action
    duration:
        [Optional] Digits followed by either s, m, h, d or w. For example: 1d 12h 30m 45s
    increase_counter:
        Whether this infraction should increase currently active infractions
    '''
    await ctx.deferred()
    if duration:
        from mlib.converters import total_seconds
        duration = total_seconds(duration)

    session = ctx.db.sql.session()
    u = models.User.filter(session, id=user.id).first()
    active = False
    from MFramework.commands._utils import detect_group
    if (
        (
            ctx.bot.emoji.get('fake_infraction', '😜') not in reason or 
            type not in {types.Infraction.Unban, types.Infraction.Unmute, types.Infraction.DM_Unmute, types.Infraction.Report}
        ) and 
        increase_counter and
        not detect_group(ctx.bot, user.id, ctx.guild_id, ctx.cache.members.get(user.id, Guild_Member()).roles).can_use(Groups.MODERATOR)
    ):
        active = True
    should_commit = True
    if not u:
        u = models.User(id = user.id)
        if type not in {types.Infraction.Ban}:
            session.add(u)
            session.commit()
        else:
            increase_counter = False
            should_commit = False
    infractions = u.add_infraction(server_id=ctx.guild_id, moderator_id=ctx.user.id, type=type.name, reason=reason, duration=duration, active=active, channel_id=ctx.channel_id, message_id=ctx.message_id) # TODO Add overwrites if it references another message
    if should_commit:
        session.commit()
    ending = "ned" if type.name.endswith('n') and type is not types.Infraction.Warn else "ed" if not type.name.endswith("e") else "d"
    if ctx.is_interaction:
        await ctx.reply(f"{user.username} has been {type.name.replace('_',' ').lower()+ending}{' for ' if reason else ''}{reason}")
    else:
        await ctx.data.react(ctx.bot.emoji["success"])

    _ = ctx.cache.logging.get("infraction", None)
    if _:
        await _(
            guild_id=ctx.guild_id,
            channel_id=ctx.channel_id,
            message_id=ctx.message_id or 0,
            moderator=ctx.user,
            user_id=user.id,
            reason=reason,
            duration=duration,
            type=type
        )
        if ctx.bot.user_id:
            try:
                r = await _.log_dm(
                    type=type, 
                    guild_id=ctx.guild_id,
                    user_id=user.id,
                    reason=reason,
                    duration= duration
                )
            except Exception as ex:
                r = None
            if not r:
                if ctx.is_message:
                    await ctx.data.react(ctx.bot.emoji.get("failure"))
                else:
                    await ctx.send("Couldn't deliver DM message")
    
    if active and type not in {types.Infraction.Mute, types.Infraction.Kick, types.Infraction.Ban}:
        return await auto_moderation(ctx, session, user, type, infractions)
    elif type in {types.Infraction.Unban, types.Infraction.Unmute, types.Infraction.DM_Unmute}:
        return True

async def auto_moderation(ctx: Context, session, user: User, type: types.Infraction, infractions: List=[]):
    active = len(list(filter(lambda x: x.server_id == ctx.guild_id and x.active, infractions)))
    automute = ctx.cache.settings.get(types.Setting.Auto_Mute_Infractions, None)
    autoban = ctx.cache.settings.get(types.Setting.Auto_Ban_Infractions, None)
    if automute and active == automute and type is not types.Infraction.Mute:
        MUTED_ROLE = list(ctx.cache.groups.get(Groups.MUTED, [None]))
        if MUTED_ROLE:
            await ctx.bot.add_guild_member_role(ctx.guild_id, user.id, MUTED_ROLE[0], reason=f"{active} active infractions")
            await infraction(ctx, types.Infraction.Mute, user, reason=f"{active} active infractions", duration=ctx.cache.settings.get(types.Setting.Auto_Mute_Duration, '12h'), increase_counter=False)
    elif autoban and active >= autoban and type is not types.Infraction.Ban:
        await ctx.bot.create_guild_ban(ctx.guild_id, user.id, reason=f"{active} active infractions")
        await infraction(ctx, types.Infraction.Ban, user, reason=f"{active} active infractions", increase_counter=False)
    else:
        return True


@register(group=Groups.GLOBAL, main=infraction, aliases=["infractions"])
async def list_(ctx: Context, user: User=None):
    '''Lists user's infractions'''
    from MFramework import Discord_Paths
    await ctx.deferred()
    language = ctx.language
    dm_response = False
    if not ctx.permission_group.can_use(Groups.HELPER) and user.id != ctx.user_id:
        dm_response = True
        user = ctx.user
    session = ctx.db.sql.session()
    u = models.User.fetch_or_add(session, id = user.id)
    _infractions = u.infractions
    if not False:#show_all:
        _infractions = list(filter(lambda x: x.server_id == ctx.guild_id, u.infractions))
    width, id_width, active = 0, 0, 0
    user_infractions = []
    from collections import namedtuple
    Row = namedtuple("Row", ['id', 'link', 'timestamp', 'type', 'reason', 'moderator_id', 'duration', 'active'])
    from mlib.localization import tr, secondsToText
    for infraction in _infractions:
        translated = tr(f"commands.infractions.types.{infraction.type.name}", language)
        if len(translated) > width:
            width = len(translated)
        if len(str(infraction.id)) > id_width:
            id_width = len(str(infraction.id))
        if infraction.active and infraction.duration and infraction.timestamp + infraction.duration < datetime.now(tz=timezone.utc):
            infraction.active = False
        user_infractions.append(
            Row(
                id=infraction.id,
                link="[#](<{}>)".format(
                        Discord_Paths.MessageLink.link.format(guild_id=infraction.server_id, channel_id=infraction.channel_id, message_id=infraction.message_id)
                    ) if infraction.message_id else "#",
                timestamp=int(infraction.timestamp.timestamp()),
                type=translated,
                reason=infraction.reason,
                moderator_id=infraction.moderator_id,
                duration=tr("commands.infractions.for_duration", language, 
                        duration=secondsToText(int(infraction.duration.total_seconds()), language)) 
                        if infraction.duration else "",
                active="~~" if not infraction.active else ""
            )
        )
        if infraction.active and infraction.type not in {
            types.Infraction.Unban,
            types.Infraction.Unmute,
            types.Infraction.DM_Unmute,
            types.Infraction.Report
        }:
            active+=1
    session.commit()
    str_infractions = '\n'.join(tr("commands.infractions.row", language, width=width, id_width=id_width, **i._asdict()).format(type=i.type, id=i.id).strip() for i in user_infractions[:10])
    if str_infractions != "":
        from mlib.colors import get_main_color
        e = Embed()
        e.setDescription(str_infractions).setAuthor(tr("commands.infractions.title", language, username=user.username), icon_url=user.get_avatar()).setColor(get_main_color(user.get_avatar()))
        total = ctx.cache.settings.get(types.Setting.Auto_Ban_Infractions, 5)
        danger = ctx.cache.settings.get(types.Setting.Auto_Mute_Infractions, 3)
        currently_active = ["🔴"] * active
        remaining_to_auto_mute = (danger-active)
        if remaining_to_auto_mute > 0:
            currently_active += ["🟢"] * remaining_to_auto_mute
        remaining_to_auto_ban = (total-active)
        if remaining_to_auto_mute > 0:
            remaining_to_auto_ban -= remaining_to_auto_mute
        if remaining_to_auto_ban > 0:
            currently_active += ["🟡"] * remaining_to_auto_ban
        e.setFooter(tr("commands.infractions.counter", language, currently_active="-".join(currently_active), active=active, total=len(user_infractions)))
        if dm_response:
            await ctx.send_dm(embeds=[e])
            return "Check your DM"
        else:
            return e
    return tr("commands.infractions.no_infractions", language)


@register(group=Groups.MODERATOR, main=infraction)
async def counter(ctx: Context, type: str, user: User, number: int=1, reason: str=None, affect_total: bool=False):
    '''
    Manages infraction counter
    Params
    ------
    type:
        Whether to increase or decrease currently active infractions
        Choices:
            Increase = Increase
            Decrease = Decrease
    user:
        User to modify
    number:
        Amount to change
    reason:
        Reason why it's being modified
    affect_total:
        Whether it should affect total count as well
    '''
    from ..database import log, types, models
    session = ctx.db.sql.session()
    #TODO: Save reason somewhere!
    u = models.User.fetch_or_add(session, id=user.id)

    i = models.Infraction(server_id=ctx.guild_id, user_id=user.id, moderator_id=ctx.user.id, type=types.Infraction.Counter, reason=reason)
    ctx.db.sql.add(i)
    active_infractions = log.Statistic.get(session, ctx.guild_id, user, types.Statistic.Infractions_Active)
    total_infractions = log.Statistic.get(session, ctx.guild_id, user, types.Statistic.Infractions_Total)
    if type == 'Increase':
        active_infractions.value += number
        if affect_total:
            total_infractions.value += number
        await auto_moderation(ctx, session, user, increase_counters=False)
    else:
        active_infractions.value -= number
        if affect_total:
            total_infractions.value -= number
    session.commit()
    await ctx.reply(f"Successfully changed. New count is {active_infractions.value}/{total_infractions.value}")


@register(group=Groups.HELPER, main=infraction, aliases=["warn"])
async def warn(ctx: Context, user: User, reason: str = "", *, language):
    '''Warns user'''
    await infraction(ctx, type=types.Infraction.Warn, user=user, reason=reason)

@register(group=Groups.MODERATOR, main=infraction, aliases=["mute"])
async def mute(ctx: Context, user: User, reason: str = "", *, language):
    '''Mutes user'''
    if await infraction(ctx, type=types.Infraction.Mute, user=user, reason=reason):
        MUTED = list(ctx.cache.groups.get(Groups.MUTED, [None]))
        if MUTED:
            await ctx.bot.add_guild_member_role(ctx.guild_id, user.id, role_id=MUTED[0], reason=reason or f"User Muted by {ctx.user.username}")

@register(group=Groups.MODERATOR, main=infraction, aliases=["kick"])
async def kick(ctx: Context, user: User, reason: str = "", *, language):
    '''Kicks user'''
    if await infraction(ctx, type=types.Infraction.Kick, user=user, reason=reason):
        await ctx.bot.remove_guild_member(ctx.guild_id, user.id, reason=reason or f"User Kicked by {ctx.user.username}")

@register(group=Groups.MODERATOR, main=infraction, aliases=["ban"])
async def ban(ctx: Context, user: User, reason: str = "", *, language):
    '''Bans user'''
    if await infraction(ctx, type=types.Infraction.Ban, user=user, reason=reason):
        await ctx.bot.create_guild_ban(ctx.guild_id, user.id, None, reason=reason or f"User banned by {ctx.user.username}")

@register(group=Groups.HELPER, main=infraction, aliases=["tempmute"])
async def tempmute(ctx: Context, user: User, duration: timedelta=None, reason: str = "", *, language):
    '''Temporarly mutes user'''
    if await infraction(ctx, type=types.Infraction.Temp_Mute, user=user, reason=reason, duration=duration):
        MUTED = list(ctx.cache.groups.get(Groups.MUTED, [None]))
        if MUTED:
            await ctx.bot.add_guild_member_role(ctx.guild_id, user.id, role_id=MUTED[0], reason=reason or f"User temporarly muted by {ctx.user.username} for {str(duration)}")
            import asyncio
            await asyncio.sleep(duration.total_seconds())
            await ctx.bot.remove_guild_member_role(ctx.guild_id, user.id, MUTED[0], reason="Unmuted as timer ran out")

@register(group=Groups.HELPER, main=infraction, aliases=["tempban"])
async def tempban(ctx: Context, user: User, duration: timedelta=None, reason: str = "", *, language):
    '''Temporarly bans user'''
    if await infraction(ctx, type=types.Infraction.Temp_Ban, user=user, reason=reason, duration=duration):
        await ctx.bot.create_guild_ban(ctx.guild_id, user.id, None, reason=reason or f"User temporarly banned by {ctx.user.username} for {str(duration)}")
        import asyncio
        await asyncio.sleep(duration.total_seconds())
        await ctx.bot.remove_guild_ban(ctx.guild_id, user.id, reason="Unbanned as timer ran out")

@register(group=Groups.MODERATOR, main=infraction, aliases=["unmute"])
async def unmute(ctx: Context, user: User, reason: str = "", *, language):
    '''Unmutes user'''
    if await infraction(ctx, type=types.Infraction.Unmute, user=user, reason=reason):
        MUTED = list(ctx.cache.groups.get(Groups.MUTED, [None]))
        if MUTED:
            await ctx.bot.remove_guild_member_role(ctx.guild_id, user.id, MUTED[0], reason=f"Unmuted by {ctx.user.username}")

@register(group=Groups.ADMIN, main=infraction, aliases=["unban"])
async def unban(ctx: Context, user: User, reason: str = "", *, language):
    '''Unbans user'''
    if await infraction(ctx, type=types.Infraction.Unban, user=user, reason=reason):
        await ctx.bot.remove_guild_ban(ctx.guild_id, user.id, reason=f"Unbanned by {ctx.user.username}")

@register(group=Groups.GLOBAL, interaction=False)
async def report(ctx: Context, msg: str, *, language, **kwargs):
    '''
    Report situation on server to Moderators
    Params
    ------
    msg:
        optional message about what's happening
    '''
    await ctx.cache.logging["report"](ctx.data)
    for moderator in filter(lambda x: ctx.data.channel_id in x["moderated_channels"] or language in x["languages"], ctx.cache.moderators):
        await ctx.cache.logging["report"].log_dm(ctx.data)
    await ctx.data.react(ctx.bot.emoji.get("success"))

class Report(Log):
    username = "User Report Log"
    async def log(self, data: Message) -> Message:
        await self._log()
    async def log_dm(self, data: Message, user_id: Snowflake) -> Message:
        await self._log_dm()

@register(group=Groups.ADMIN, main=infraction)
async def expire(ctx: Context, infraction_id: int, *, language):
    '''
    Expires an infraction
    Params
    ------
    infraction_id:
        Infraction to expire
    '''
    session = ctx.db.sql.session()
    from ..database import Infraction
    infraction = Infraction.filter(session, server_id=ctx.guild_id, id=infraction_id).first()
    if not infraction:
        return await ctx.reply("Couldn't find infraction with provided id")
    infraction.active = False
    session.commit()
    await ctx.reply(f"Successfully expired infraction with reason `{infraction.reason}` added by {infraction.moderator_id}")


class Infraction(Log):
    username = "Infraction Log"
    _types = {
        "warn": "warned",
        "tempmute":"temporarily muted",
        "mute": "muted",
        "kick": "kicked",
        "tempban":"temporarily banned",
        "ban": "banned",
        "unban": "unbanned",
        "unmute": "unmuted"
    } #HACK
    async def log(self, guild_id: Snowflake, channel_id: Snowflake, message_id: Snowflake, moderator: User, user_id: Snowflake, reason: str, type: types.Infraction, duration: int=0, attachments: List[Attachment]=None) -> Message:
        from MFramework import Discord_Paths
        string = f'{moderator.username} [{self._types.get(type.name.lower(), type.name)}](<{Discord_Paths.MessageLink.link.format(guild_id=guild_id, channel_id=channel_id, message_id=message_id)}>) '
        u = f'[<@{user_id}>'
        try:
            user = self.bot.cache[guild_id].members[user_id].user
            u += f' | {user.username}#{user.discriminator}'
        except:
            pass
        u += ']'
        string += u
        if reason != '':
            string += f' for "{reason}"'
        if duration:
            from mlib.localization import secondsToText
            string += f" (Duration: {secondsToText(duration)})"
        embeds = []
        if attachments is not None:
            for attachment in attachments:
                if len(embeds) == 10:
                    break
                embeds.append(Embed().setImage(attachment.url).setTitle(attachment.filename).embed)
        await self._log(content=string, embeds=embeds)
    async def log_dm(self, type: types.Infraction, guild_id: Snowflake, user_id: Snowflake, reason: str="", duration: int=None) -> Message:
        s = f"You've been {self._types[type.name.lower()]} in {self.bot.cache[guild_id].guild.name} server"
        if reason != '':
            s+=f" for {reason}"
        if duration:
            from mlib.localization import secondsToText
            s += f" ({secondsToText(duration)})"
        return await self._log_dm(user_id, s)


class Infraction_Event(Infraction):
    username = "Infraction Event Log"
    async def log(self, data: Union[Guild_Ban_Add, Guild_Ban_Remove], type: str, reason: str="", by_user: str="") -> Message:
        if by_user != '':
            try:
                by_user = self.bot.cache[data.guild_id].members[int(by_user)].user.username
            except:
                pass
            string = f'{by_user} {type} [<@{data.user.id}> | {data.user.username}#{data.user.discriminator}]'
        else:
            string = f'[<@{data.user.id}> | {data.user.username}#{data.user.discriminator}] has been {type}'
        if reason and reason == "Too many infractions":
            s = self.bot.db.sql.session()
            from ..database import Infraction as db_Infraction
            infractions = db_Infraction.filter(s, server_id=self.guild_id, user_id=data.user.id, active=True).all()
            if infractions:
                string += " for:\n" + "\n".join([f"- {infraction.reason}" for infraction in infractions])
            else:
                string += f' for "{reason}"'
        elif reason != '' and reason != 'Unspecified':
            string += f' for "{reason}"'
        await self._log(string)

    async def get_ban_data(self, data: Union[Guild_Ban_Add, Guild_Ban_Remove], type: types.Infraction, audit_type: str) -> Tuple[bool, bool]:
        import asyncio
        await asyncio.sleep(3)
        audit = await self.bot.get_guild_audit_log(data.guild_id, action_type=audit_type)
        reason = None
        moderator = None
        for obj in audit.audit_log_entries:
            #Try to find ban in Audit Log
            if int(obj.target_id) == data.user.id:
                moderator = obj.user_id
                reason = obj.reason
                break
        if reason is None and type is types.Infraction.Ban:
            #Fall back to fetching ban manually
            reason = await self.bot.get_guild_ban(data.guild_id, data.user.id)
            reason = reason.reason
        s = self.bot.db.sql.session()
        from ..database import Infraction as db_Infraction
        r = db_Infraction.filter(s, server_id=self.guild_id, user_id=data.user.id, reason=reason, type=type).first()
        if r is None:
            if reason and not "Massbanned by" in reason:
                u = models.User.fetch_or_add(s, id=data.user.id)
                u.add_infraction(data.guild_id, moderator, type, reason)
                s.commit()
            return reason, moderator
        return False, False

class Guild_Ban_Add(Infraction_Event):
    async def log(self, data: Guild_Ban_Add):
        reason, moderator = await self.get_ban_data(data, types.Infraction.Ban, 22)
        # TODO: Hey! Idea, maybe make decorator like @onDispatch, but like @log or something to make it a logger and register etc?
        if reason is not False:
            await super().log(data, type="banned", reason=reason, by_user=moderator)

class Guild_Ban_Remove(Infraction_Event):
    async def log(self, data: Guild_Ban_Remove):
        reason, moderator = await self.get_ban_data(data, types.Infraction.Unban, 23)
        if reason is not False:
            await super().log(data, type="unbanned", reason=reason, by_user=moderator)

class Auto_Mod(Infraction):
    pass