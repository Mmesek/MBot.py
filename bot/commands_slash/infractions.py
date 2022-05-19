from typing import List, Tuple, Union, Optional
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from mlib.database import Base, ID, Timestamp

from MFramework import register, Groups, Context, User, Embed, shortcut, Guild_Member, Snowflake, Message, Attachment, Guild_Ban_Add, Guild_Ban_Remove, Discord_Paths, Guild_Member_Update, Message_Reference
from MFramework.commands.components import LinkButton, Row
from MFramework.utils.log import Log
from MFramework.database.alchemy.types import Permissions
from MFramework.database.alchemy.mixins import Snowflake, ServerID

from ..database.mixins import UserID
from ..database import types, models
check_type = type # #HACK alias so we can use type as argument name

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
# - Infraction "expiration time" (After how long it becomes expired/inactive)

class InfractionTypes(Permissions):
    '''Infractions'''
    Warn: Groups.HELPER = (0, "Warns user")
    Mute: Groups.MODERATOR = (1, "Mutes user")
    Kick: Groups.MODERATOR = (2, "Kicks user")
    Ban: Groups.MODERATOR = (3, "Bans user")
    Temp_Mute: Groups.HELPER = (4, "Temporarly mutes user")
    Temp_Ban: Groups.HELPER = (5, "Temporarly bans user")
    Unban: Groups.ADMIN = (6, "Unbans user")
    Unmute: Groups.MODERATOR = (7, "Unmutes user")
    Limbo: Groups.ADMIN = (8, "Throws user to Limbo")
    DM_Mute: Groups.MODERATOR = (9, "Mutes DMs from user in Modmail")
    DM_Unmute: Groups.MODERATOR = (10, "Unmutes DMs from user in Modmail")
    Report: Groups.GLOBAL = (11, "Reports user")
    Timeout: Groups.HELPER = (12, "Timeouts user")


class Infraction(Timestamp, UserID, ServerID, ID, Base):
    '''Infractions Table

    Columns
    -------
    id: `int`
        Autoincremented ID of infraction
    server_id: `Snowflake`
        ID of server there this infraction happen
    user_id: `Snowflake`
        ID of User that is infracted
    timestamp: `datetime.datetime`
        Timestamp when this infraction happened
    moderator_id: `Snowflake`
        ID of Moderator that issued this infraction
    type : `InfractionTypes`
        `Infractions` type of this infraction
    reason : `str`
        Reason of this infraction
    duration : `datetime.timedelta`
        How long this infraction should be valid/active
    channel_id : `Snowflake`
        Channel where this infraction happened
    message_id : `Snowflake`
        Message that caused this infraction (or moderator message that issued infraction)
    active : `bool`
        Whether this Infraction should be counted as active

    Relations
    -------------
    moderator: `User`
        Moderator `User` relationship
    user : `User`
        Infracted `User` relationship
    '''
    user_id: Snowflake = sa.Column(sa.ForeignKey("User.id", ondelete='SET DEFAULT', onupdate='Cascade'), nullable=False, default=0)
    user = sa.orm.relationship("User", foreign_keys="Infraction.user_id")
    moderator_id: Optional[Snowflake] = sa.Column(sa.ForeignKey("User.id", ondelete='SET DEFAULT', onupdate='Cascade'), nullable=True, default=0)
    moderator = sa.orm.relationship("User", foreign_keys="Infraction.moderator_id")

    type: InfractionTypes = sa.Column(sa.Enum(InfractionTypes))
    reason: Optional[str] = sa.Column(sa.UnicodeText, nullable=True)
    duration: Optional[timedelta] = sa.Column(sa.Interval, nullable=True)

    channel_id: Optional[Snowflake] = sa.Column(sa.BigInteger, nullable=True)
    message_id: Optional[Snowflake] = sa.Column(sa.BigInteger, nullable=True)
    expires_at: Optional[datetime] = sa.Column(sa.TIMESTAMP(timezone=True), nullable=True)

db_Infraction = Infraction

#TODO:
# Each infraction as separate command instead of choice type?
# move everything to infraction command group?
# or make infraction list an info subcommand or some other?
# Perhaps alias interaction?
# List recently joined users and provide filter/sorter
@register(group=Groups.HELPER, main_only=True)
#@shortcut(name="warn", group=Groups.HELPER, type=InfractionTypes.Warn, help="Warns user")
#@shortcut(name="mute", group=Groups.MODERATOR, type=InfractionTypes.Mute, help="Mutes user")
#@shortcut(name="kick", group=Groups.MODERATOR, type=InfractionTypes.Kick, help="Kicks user")
#@shortcut(name="ban", group=Groups.MODERATOR, type=InfractionTypes.Ban, help="Bans user")
#@shortcut(name="tempmute", group=Groups.HELPER, type=InfractionTypes.Temp_Mute, help="Temporarly mutes user")
#@shortcut(name="tempban", group=Groups.HELPER, type=InfractionTypes.Temp_Ban, help="Temporarly bans user")
#@shortcut(name="unmute", group=Groups.MODERATOR, type=InfractionTypes.Unban, help="Unmutes user")
#@shortcut(name="unban", group=Groups.ADMIN, type=InfractionTypes.Unmute, help="Unbans user")
async def infraction(ctx: Context, *, type: InfractionTypes, user: User=None, reason:str="", duration:timedelta=None, increase_counter: bool=True, expire_date: datetime = None):
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
    if duration and check_type(duration) is str:
        from mlib.converters import total_seconds
        duration = total_seconds(duration)

    session = ctx.db.sql.session()
    u = models.User.filter(session, id=user.id).first()
    active = False
    from MFramework.commands._utils import detect_group
    if (
        (
            ctx.bot.emoji.get('fake_infraction', '😜') not in reason or 
            type not in {InfractionTypes.Unban, InfractionTypes.Unmute, InfractionTypes.DM_Unmute, InfractionTypes.Report}
        ) and 
        increase_counter and
        not detect_group(ctx.bot, user.id, ctx.guild_id, ctx.cache.members.get(user.id, Guild_Member()).roles).can_use(Groups.MODERATOR)
    ):
        active = True
    should_commit = True
    if not u:
        u = models.User(id = user.id)
        if type not in {InfractionTypes.Ban}:
            session.add(u)
            session.commit()
        else:
            increase_counter = False
            should_commit = False
    if not expire_date and type is InfractionTypes.Warn:
        expire_date = datetime.now(tz=timezone.utc) + timedelta(weeks=16)
    infractions = u.add_infraction(server_id=ctx.guild_id, moderator_id=ctx.user.id, type=type.name, reason=reason, duration=duration, expire=expire_date, channel_id=ctx.channel_id, message_id=ctx.message_id) # TODO Add overwrites if it references another message
    if should_commit:
        session.commit()
    ending = "ned" if type.name.endswith('n') and type is not InfractionTypes.Warn else "ed" if not type.name.endswith("e") else "d"
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
    
    if active and type not in {InfractionTypes.Timeout, InfractionTypes.Mute, InfractionTypes.Kick, InfractionTypes.Ban, InfractionTypes.Unmute, InfractionTypes.Unban}:
        return await auto_moderation(ctx, session, user, type, infractions)
    elif active or type in {InfractionTypes.Unban, InfractionTypes.Unmute, InfractionTypes.DM_Unmute}:
        return True

async def auto_moderation(ctx: Context, session, user: User, type: InfractionTypes, infractions: List[Infraction]=[]):
    active_infractions = list(filter(lambda x: x.server_id == ctx.guild_id and (not x.expires_at or x.expires_at >= datetime.now(tz=timezone.utc)), infractions))
    active = len(active_infractions)
    automute = ctx.cache.settings.get(types.Setting.Auto_Mute_Infractions, None)
    autoban = ctx.cache.settings.get(types.Setting.Auto_Ban_Infractions, None)
    if automute and active == automute and type is not InfractionTypes.Mute:
        #MUTED_ROLE = list(ctx.cache.groups.get(Groups.MUTED, [None]))
        duration = ctx.cache.settings.get(types.Setting.Auto_Mute_Duration, '12h')
        from mlib.converters import total_seconds
        #if MUTED_ROLE:
        #    await ctx.bot.add_guild_member_role(ctx.guild_id, user.id, MUTED_ROLE[0], reason=f"{active} active infractions")
        #else:
        await ctx.bot.modify_guild_member(ctx.guild_id, user.id, mute=None, deaf=None, communication_disabled_until=datetime.utcnow()+total_seconds(duration), reason=f"{active} active infractions")
        await infraction(ctx, type=InfractionTypes.Timeout, user=user, reason=f"{active} active infractions", duration=duration, increase_counter=False)
    elif autoban and active >= autoban and type is not InfractionTypes.Ban:
        await ctx.bot.create_guild_ban(ctx.guild_id, user.id, reason=f"{active} active infractions")
        reason = "\n" + "\n".join([f"- {i.reason}" for i in active_infractions if i.type not in {InfractionTypes.Unmute, InfractionTypes.Unban}])
        await infraction(ctx, type=InfractionTypes.Ban, user=user, reason=reason, increase_counter=False)
    else:
        return True


@register(group=Groups.GLOBAL, main=infraction, aliases=["infractions"])
async def list_(ctx: Context, user: User=None):
    '''Lists user's infractions'''
    from MFramework import Discord_Paths
    await ctx.deferred()
    language = ctx.language
    dm_response = False
    if not ctx.permission_group.can_use(Groups.HELPER):
        dm_response = True
        if user.id != ctx.user_id:
            user = ctx.user
    session = ctx.db.sql.session()
    u = models.User.fetch_or_add(session, id = user.id)
    _infractions = u.infractions
    if not False:#show_all:
        _infractions = list(filter(lambda x: x.server_id == ctx.guild_id, u.infractions))
    width, id_width, active = 0, 0, 0
    user_infractions = []
    from collections import namedtuple
    _Row = namedtuple("Row", ['id', 'link', 'timestamp', 'type', 'reason', 'moderator_id', 'duration', 'active'])
    from mlib.localization import tr, secondsToText
    for infraction in _infractions:
        translated = tr(f"commands.infractions.types.{infraction.type.name}", language)
        if len(translated) > width:
            width = len(translated)
        if len(str(infraction.id)) > id_width:
            id_width = len(str(infraction.id))
        user_infractions.append(
            _Row(
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
                active="~~" if (infraction.expires_at and infraction.expires_at <= datetime.now(tz=timezone.utc)) else ""
            )
        )
        if (not infraction.expires_at or infraction.expires_at >= datetime.now(tz=timezone.utc)) and infraction.type not in {
            InfractionTypes.Unban,
            InfractionTypes.Unmute,
            InfractionTypes.DM_Unmute,
            InfractionTypes.Report
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
            components = []
            if ctx.permission_group.can_use(Groups.MODERATOR):
                components.append(instant_actions(user.id))
            if ctx.permission_group.can_use(Groups.ADMIN):
                _ = [Select_Option(label=f"#{i[0]}", value=i[0], description=i[4][:50] if i[4] else "No reason specified") for i in user_infractions if not i[-1]][:25]
                if _:
                    components.append(Row(ExpireInfractions(*_, placeholder="Expire Infractions")))
            await ctx.reply(embeds=[e], components=components)
            return
    return tr("commands.infractions.no_infractions", language)

from MFramework.commands.components import Select, Select_Option
class ExpireInfractions(Select):
    @classmethod
    async def execute(cls, ctx: 'Context', data: str, values: List[str], not_selected: List[Select_Option]):
        if ctx.permission_group.can_use(Groups.ADMIN):
            return await expire(ctx, values[0])
        return "Only Admins can expire infractions!"


#@register(group=Groups.MODERATOR, main=infraction)
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

    i = Infraction(server_id=ctx.guild_id, user_id=user.id, moderator_id=ctx.user.id, type=InfractionTypes.Counter, reason=reason)
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
async def warn(ctx: Context, user: User, reason: str = ""):
    '''Warns user'''
    await infraction(ctx, type=InfractionTypes.Warn, user=user, reason=reason)

@register(group=Groups.MODERATOR, main=infraction, aliases=["mute"])
async def mute(ctx: Context, user: User, reason: str = ""):
    '''Mutes user'''
    if await infraction(ctx, type=InfractionTypes.Mute, user=user, reason=reason):
        MUTED = list(ctx.cache.groups.get(Groups.MUTED, [None]))
        if MUTED:
            await ctx.bot.add_guild_member_role(ctx.guild_id, user.id, role_id=MUTED[0], reason=reason or f"User Muted by {ctx.user.username}")
        else:
            await ctx.bot.modify_guild_member(ctx.guild_id, user.id, mute=None, deaf=None, communication_disabled_until=datetime.utcnow()+timedelta(weeks=4), reason=reason)

@register(group=Groups.MODERATOR, main=infraction, aliases=["kick"])
async def kick(ctx: Context, user: User, reason: str = ""):
    '''Kicks user'''
    if await infraction(ctx, type=InfractionTypes.Kick, user=user, reason=reason):
        await ctx.bot.remove_guild_member(ctx.guild_id, user.id, reason=reason or f"User Kicked by {ctx.user.username}")

@register(group=Groups.MODERATOR, main=infraction, aliases=["ban"])
async def ban(ctx: Context, user: User, reason: str = ""):
    '''Bans user'''
    if await infraction(ctx, type=InfractionTypes.Ban, user=user, reason=reason):
        await ctx.bot.create_guild_ban(ctx.guild_id, user.id, None, reason=reason or f"User banned by {ctx.user.username}")

@register(group=Groups.HELPER, main=infraction, aliases=["tempmute"])
async def tempmute(ctx: Context, user: User, duration: timedelta=None, reason: str = ""):
    '''Temporarly mutes user'''
    if await infraction(ctx, type=InfractionTypes.Temp_Mute, user=user, reason=reason, duration=duration):
        MUTED = list(ctx.cache.groups.get(Groups.MUTED, [None]))
        if MUTED:
            await ctx.bot.add_guild_member_role(ctx.guild_id, user.id, role_id=MUTED[0], reason=reason or f"User temporarly muted by {ctx.user.username} for {str(duration)}")
            # TODO
            import asyncio
            await asyncio.sleep(duration.total_seconds())
            await ctx.bot.remove_guild_member_role(ctx.guild_id, user.id, MUTED[0], reason="Unmuted as timer ran out")
        else:
            await ctx.bot.modify_guild_member(ctx.guild_id, user.id, mute=None, deaf=None, communication_disabled_until=datetime.utcnow()+duration, reason=reason)

@register(group=Groups.HELPER, main=infraction, aliases=["tempban"])
async def tempban(ctx: Context, user: User, duration: timedelta=None, reason: str = ""):
    '''Temporarly bans user'''
    if await infraction(ctx, type=InfractionTypes.Temp_Ban, user=user, reason=reason, duration=duration):
        await ctx.bot.create_guild_ban(ctx.guild_id, user.id, None, reason=reason or f"User temporarly banned by {ctx.user.username} for {str(duration)}")
        # TODO
        import asyncio
        await asyncio.sleep(duration.total_seconds())
        await ctx.bot.remove_guild_ban(ctx.guild_id, user.id, reason="Unbanned as timer ran out")

@register(group=Groups.MODERATOR, main=infraction, aliases=["unmute"])
async def unmute(ctx: Context, user: User, reason: str = ""):
    '''Unmutes user'''
    if await infraction(ctx, type=InfractionTypes.Unmute, user=user, reason=reason):
        MUTED = list(ctx.cache.groups.get(Groups.MUTED, [None]))
        if MUTED:
            await ctx.bot.remove_guild_member_role(ctx.guild_id, user.id, MUTED[0], reason=f"Unmuted by {ctx.user.username}")
        else:
            await ctx.bot.modify_guild_member(ctx.guild_id, user.id, mute=None, deaf=None, communication_disabled_until=None, reason=f"Unmuted by {ctx.user.username}")

@register(group=Groups.ADMIN, main=infraction, aliases=["unban"])
async def unban(ctx: Context, user: User, reason: str = "") -> str:
    '''Unbans user'''
    if await infraction(ctx, type=InfractionTypes.Unban, user=user, reason=reason):
        try:
            await ctx.bot.remove_guild_ban(ctx.guild_id, user.id, reason=f"Unbanned by {ctx.user.username}")
        except:
            return "User is probably not banned"

from MFramework import Presence_Update, onDispatch, Bot

@onDispatch
async def presence_update(self: Bot, data: Presence_Update):
    member = self.cache[data.guild_id].members.get(data.user.id)
    if member and self.cache[data.guild_id].cachedRoles(member.roles).can_use(Groups.MODERATOR):
        self.cache[data.guild_id].moderators[data.user.id] = data

@register(group=Groups.GLOBAL, interaction=False, aliases=["op"])
async def report(ctx: Context, msg: str = None):
    '''
    Report situation on server to Moderators
    Params
    ------
    msg:
        optional message about what's happening
    '''
    if not ctx.data.referenced_message and not msg:
        return "Either reply to a message you want to have reported and/or state a reason of your report while using command."
    #await ctx.cache.logging["report"](ctx.data)
    reported_to = 0
    _msg = await ctx.reply("I'm on my way to notify moderators!")

    link = Discord_Paths.MessageLink.link.format(guild_id=ctx.guild_id, channel_id=ctx.channel_id, message_id=ctx.data.id)
    embeds = []
    e = Embed().setTitle(f"Report made by {ctx.data.author.username}").setColor("#C29D60").setAuthor(str(ctx.data.author), icon_url=ctx.data.author.get_avatar()).setUrl(link)
    if msg:
        e.setDescription(msg)
    embeds.append(e)
    if ctx.data.referenced_message:
        ref = ctx.data.referenced_message
        ref_url = Discord_Paths.MessageLink.link.format(guild_id=ref.guild_id, channel_id=ref.channel_id, message_id=ref.id)
        e = Embed().setTitle(f"Referenced Message from {ref.author.username}").setDescription(ref.content).setColor("#a52f37").setAuthor(str(ref.author), icon_url=ref.author.get_avatar()).setUrl(ref_url)
        if ref.attachments:
            e.addField("Attachments", "\n".join([f"[{i.filename}.{i.content_type.split('/')[-1]}]({i.url})" for i in ref.attachments]))
        embeds.append(e)
    components = [Row(LinkButton(f"Jump to Message", link))]

    import time
    start = time.time()
    #for moderator in filter(lambda x: ctx.data.channel_id in x["moderated_channels"] or language in x["languages"], ctx.cache.moderators):
    mod_roles = ctx.cache.groups[Groups.MODERATOR]
    for moderator in list(filter(lambda x: any(role in ctx.cache.members[x].roles for role in mod_roles), ctx.cache.members)):
    #for moderator in list(filter(lambda x: ctx.cache.cachedRoles(ctx.cache.members[x].roles).can_use(Groups.MODERATOR), ctx.cache.members)):
        if ctx.cache.members[moderator].user.bot or (moderator not in ctx.cache.moderators or ctx.cache.moderators[moderator].status not in ["online", "idle"]):
            continue

        #await ctx.cache.logging["report"].log_dm(moderator, embeds, components)
        dm = await ctx.bot.create_dm(moderator)
        await ctx.bot.create_message(dm.id, embeds=embeds, components=components)
        reported_to += 1

    end = time.time()
    if reported_to:
        await _msg.edit(f"Notified {reported_to} Moderator{'s' if reported_to > 1 else ''} in {end-start:.2}s!")
        await ctx.data.react(ctx.bot.emoji.get("success"))
    else:
        await _msg.edit(f"Couldn't find any moderator online, falling back to regular ping")
        await ctx.bot.create_message(ctx.channel_id, "<@&496201383524171776>, There is a report waiting!", embeds=embeds, message_reference=ctx.data.message_reference or Message_Reference(message_id=ctx.data.id, channel_id=ctx.data.channel_id, guild_id=ctx.data.guild_id), allowed_mentions=None)

class Report(Log):
    username = "User Report Log"
    async def log(self, data: Message) -> Message:
        await self._log()
    async def log_dm(self, user_id: Snowflake, embeds: Embed, compontents) -> Message:
        await self._log_dm(user_id, embeds=embeds, components=compontents)

@register(group=Groups.ADMIN, main=infraction)
async def expire(ctx: Context, infraction_id: int) -> str:
    '''
    Expires an infraction
    Params
    ------
    infraction_id:
        Infraction to expire
    '''
    session = ctx.db.sql.session()
    infraction = db_Infraction.filter(session, server_id=ctx.guild_id, id=infraction_id).first()
    if not infraction:
        return "Couldn't find infraction with provided id"
    infraction.expires_at = datetime.utcnow()
    session.commit()
    return f"Successfully expired infraction with reason `{infraction.reason}` added by <@{infraction.moderator_id}>"


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
        "unmute": "unmuted",
        "timeout": "timed out"
    } #HACK
    async def log(self, guild_id: Snowflake, channel_id: Snowflake, message_id: Snowflake, moderator: User, user_id: Snowflake, reason: str, type: InfractionTypes, duration: int=0, attachments: List[Attachment]=None) -> Message:
        from MFramework import Discord_Paths
        channel = self.bot.cache[guild_id].channels.get(channel_id)
        channel_name = channel.name if channel else channel_id
        string = f'{moderator.username} [{self._types.get(type.name.lower(), type.name)}](<{Discord_Paths.MessageLink.link.format(guild_id=guild_id, channel_id=channel_id, message_id=message_id)}> "{channel_name}") '
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
    async def log_dm(self, type: InfractionTypes, guild_id: Snowflake, user_id: Snowflake, reason: str="", duration: int=None) -> Message:
        s = f"You've been {self._types[type.name.lower()]} in {self.bot.cache[guild_id].guild.name} server"
        if reason != '':
            s+=f" for {reason}"
        if duration:
            from mlib.localization import secondsToText
            s += f" ({secondsToText(duration)})"
        return await self._log_dm(user_id, s)


class Infraction_Event(Infraction):
    username = "Infraction Event Log"
    async def log(self, data: Union[Guild_Ban_Add, Guild_Ban_Remove, Guild_Member_Update], type: str, reason: str="", by_user: str="") -> Message:
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
            infractions = db_Infraction.filter(s, server_id=self.guild_id, user_id=data.user.id).all()
            if infractions:
                string += " for:\n" + "\n".join([f"- {infraction.reason}" for infraction in infractions])
            else:
                string += f' for "{reason}"'
        elif reason != '' and reason != 'Unspecified':
            string += f' for "{reason}"'
        if type == "timed out":
            string += f" until <t:{int(data.communication_disabled_until.timestamp())}>"
        await self._log(string)

    async def get_ban_data(self, data: Union[Guild_Ban_Add, Guild_Ban_Remove, Guild_Member_Update], type: InfractionTypes, audit_type: str) -> Tuple[bool, bool]:
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
        if reason is None and type is InfractionTypes.Ban:
            #Fall back to fetching ban manually
            reason = await self.bot.get_guild_ban(data.guild_id, data.user.id)
            reason = reason.reason
        s = self.bot.db.sql.session()
        r = db_Infraction.filter(s, server_id=self.guild_id, user_id=data.user.id, reason=reason, type=type).first()
        if r is None:
            if reason and not "Massbanned by" in reason:
                u = models.User.fetch_or_add(s, id=data.user.id)
                duration = None
                if type is InfractionTypes.Timeout:
                    duration = data.communication_disabled_until - datetime.now(tz=timezone.utc)
                    if duration.total_seconds() < 0:
                        return False, False
                u.add_infraction(data.guild_id, moderator, type, reason, duration)
                s.commit()
            return reason, moderator
        return False, False

class Guild_Ban_Add(Infraction_Event):
    async def log(self, data: Guild_Ban_Add):
        reason, moderator = await self.get_ban_data(data, InfractionTypes.Ban, 22)
        # TODO: Hey! Idea, maybe make decorator like @onDispatch, but like @log or something to make it a logger and register etc?
        if reason is not False:
            await super().log(data, type="banned", reason=reason, by_user=moderator)

class Guild_Ban_Remove(Infraction_Event):
    async def log(self, data: Guild_Ban_Remove):
        reason, moderator = await self.get_ban_data(data, InfractionTypes.Unban, 23)
        if reason is not False:
            await super().log(data, type="unbanned", reason=reason, by_user=moderator)

class Timeout_Event(Infraction_Event):
    async def log(self, data: Guild_Member_Update):
        if data.communication_disabled_until and data.communication_disabled_until > datetime.now(timezone.utc):
            reason, moderator = await self.get_ban_data(data, InfractionTypes.Timeout, 24)
            await super().log(data, type="timed out", reason=reason, by_user=moderator)
            await super().log_dm(InfractionTypes.Timeout, data.guild_id, data.user.id, reason)

@onDispatch
async def guild_member_update(self: Bot, data: Guild_Member_Update):
    await self.cache[data.guild_id].logging["timeout_event"](data)

class Auto_Mod(Infraction):
    pass


from MFramework.commands.components import Button, Row, Modal, TextInput, Button_Styles, Emoji
'''
class InstantActions(Row):
    def __init__(self, id: Snowflake):
        super().__init__(i.custom_id + f"-{id}" for i in InstantActions.components)

    async def get_user(self, ctx: Context, data: str) -> User:
        member: Guild_Member = ctx.cache.members.get(int(data))
        if member:
            return member.user
        return User(id=data)

    @button(style=Button_Styles.PRIMARY, auto_defer=False)
    async def warn(self, ctx: Context, data: str):
        inputs = ctx.modal(TextInput("Reason"))
        await warn(ctx, self.get_user(ctx, data), inputs.get("Reason", ""))

    @button(style=Button_Styles.SECONDARY, auto_defer=False)
    async def mute(self, ctx: Context, data: str):
        inputs = ctx.modal(TextInput("Reason"))
        await mute(ctx, self.get_user(ctx, data), inputs.get("Reason", ""))

    @button(style=Button_Styles.SECONDARY, auto_defer=False)
    async def kick(self, ctx: Context, data: str):
        inputs = ctx.modal(TextInput("Reason"))
        await kick(ctx, self.get_user(ctx, data), inputs.get("Reason", ""))

    @button(style=Button_Styles.DANGER, auto_defer=False)
    async def ban(self, ctx: Context, data: str):
        inputs = ctx.modal(TextInput("Reason"))
        await ban(ctx, self.get_user(ctx, data), inputs.get("Reason", ""))
'''

class Reason(Modal):
    private_response = False
    @classmethod
    async def execute(cls, ctx: Context, data: str, inputs: dict[str, str]):
        action, id = data.split("-")
        member: Guild_Member = ctx.cache.members.get(int(id))
        if member:
            user = member.user
        else:
            user = User(id=data)
        if action == "Warn":
            return await warn(ctx, user, inputs.get("Reason", "Instant Action"))
        elif action == "Mute":
            return await mute(ctx, user, inputs.get("Reason", "Instant Action"))
        elif action == "Kick":
            return await kick(ctx, user, inputs.get("Reason", "Instant Action"))
        elif action == "Ban":
            return await ban(ctx, user, inputs.get("Reason", "Instant Action"))

class InstantAction(Button):
    auto_deferred: bool = False
    def __init__(self, label: str, custom_id: str = None, style: Button_Styles = ..., emoji: Emoji = None, disabled: bool = False):
        super().__init__(label, custom_id or label, style, emoji, disabled)
    @classmethod
    async def execute(cls, ctx: Context, data: str):
        return Reason(Row(TextInput("Reason", placeholder="Reason of this action")), title="Infraction", custom_id=data)


def instant_actions(id: Snowflake):
    _instant_actions = Row(
        InstantAction("Warn", style=Button_Styles.PRIMARY, emoji=Emoji(name="📖")), 
        InstantAction("Mute", style=Button_Styles.SECONDARY, emoji=Emoji(name="🔕")), 
        InstantAction("Kick", style=Button_Styles.SECONDARY, emoji=Emoji(name="🏌️‍♂️")), 
        InstantAction("Ban", style=Button_Styles.DANGER, emoji=Emoji(name="🔨"))
    )
    for ia in _instant_actions.components:
        ia.custom_id += f"-{id}"
    return _instant_actions
