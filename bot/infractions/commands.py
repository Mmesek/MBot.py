import time
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from MFramework import (
    Bot,
    Context,
    Discord_Paths,
    Embed,
    Groups,
    Guild_Member,
    Message,
    Message_Reference,
    Presence_Update,
    User,
    onDispatch,
    register,
)
from MFramework.commands._utils import detect_group
from MFramework.commands.components import LinkButton, Row, Select_Option
from MFramework.database.alchemy import types
from mlib.converters import total_seconds

from . import models
from .interactions import ExpireInfractions, instant_actions
from .internal import log_action


class UserProtected(Exception):
    pass


@register(group=Groups.GLOBAL)
async def infraction(
    ctx: Context, *, type_: models.Types, user: User, reason: str = None, duration: timedelta = None, weight: float = 1
) -> str:
    """
    Base command for infractions

    Params
    ------
    type_:
        Type of Infraction
    user:
        User to take action upon
    reason:
        Reason of action
    duration:
        Digits followed by either s, m, h, d or w. For example: 1d 12h 30m 45s
    weight:
        Weight of this infraction
    """
    session = ctx.db.sql.session()
    if type_ is models.Types.Warn:
        expire_date = datetime.now(tz=timezone.utc) + timedelta(weeks=16)
    else:
        expire_date = None
    session.add(
        models.Infraction(
            moderator_id=ctx.user_id,
            user_id=user.id,
            server_id=ctx.guild_id,
            type=type_,
            reason=reason,
            duration=duration,
            channel_id=ctx.channel_id,
            message_id=ctx.message_id,
            expires_at=expire_date,
            weight=weight,
        )
    )
    session.commit()

    try:
        await log_action(
            cache=ctx.cache,
            logger="infraction",
            channel_id=ctx.channel_id,
            message_id=ctx.message_id,
            moderator=ctx.user,
            user_id=user.id,
            reason=reason,
            duration=duration,
            type=type_,
        )
        response = ""
    except:
        response = ctx.t("error_dm") + "\n"

    if type_ is not models.Types.Warn:
        return response + ctx.t("success_add", type=ctx.t(type_.name).title(), user_id=user.id, reason=reason)

    if detect_group(ctx.bot, user.id, ctx.guild_id, ctx.cache.members.get(user.id, Guild_Member()).roles).can_use(
        Groups.HELPER
    ):
        raise UserProtected(ctx.t("error_target_moderator"))

    active = (
        session.query(sa.func.sum(models.Infraction.weight))
        .filter(
            models.Infraction.user_id == user.id,
            models.Infraction.server_id == ctx.guild_id,
            not models.Infraction.expires_at or models.Infraction.expires_at >= datetime.now(tz=timezone.utc),
        )
        .first()
    )
    if active:
        active = round(active[0] or 0)
    else:
        active = 0
    automute = ctx.cache.settings.get(types.Setting.Auto_Mute_Infractions, 4)
    autoban = ctx.cache.settings.get(types.Setting.Auto_Ban_Infractions, None)
    if autoban and active >= autoban and type_ is not models.Types.Ban:
        await ban(ctx=ctx, user=user, reason=ctx.t("active_infractions", active=active))
    elif automute and active >= automute and active <= (autoban or active + 1) and type_ is not models.Types.Timeout:
        duration = ctx.cache.settings.get(types.Setting.Auto_Mute_Duration, "12h")
        await timeout(
            ctx=ctx, user=user, duration=duration, reason=ctx.t("active_infractions", active=active), weight=0
        )

    return response + ctx.t("success_add", type=ctx.t(type_.name).title(), user_id=user.id, reason=reason)


@register(group=Groups.HELPER, main=infraction, aliases=["warn"], auto_defer=False)
# @button(style=Button_Styles.PRIMARY, emoji=Emoji(name="📖"))
# @menu_user("Warn")
async def warn(
    ctx: Context,
    user: User,
    reason: str = None,
    *,
    weight: float = 1,
    notify_channel: bool = True,
    anonymous: bool = False,
) -> str:
    """
    Warn User

    Params
    ------
    user:
        User to take action upon
    reason:
        Reason of action
    weight:
        Weight of this infraction
    notify_channel:
        Whether public message should be send in a channel
    anonymous:
        Whether confirmation should be anonymous
    """
    await ctx.deferred(not notify_channel or anonymous)

    r = await infraction(ctx, type_=models.Types.Warn, user=user, reason=reason, weight=weight)
    if anonymous:
        await ctx.reply(r)

    await ctx.send(r, channel_id=ctx.channel_id if anonymous else None)


@register(group=Groups.HELPER, main=infraction, aliases=["timeout", "mute", "tempmute"])
# @button(style=Button_Styles.SECONDARY, emoji=Emoji(name="🔕"))
async def timeout(
    ctx: Context, user: User, duration: timedelta = None, reason: str = None, *, weight: float = 1
) -> str:
    """
    Timeout user

    Params
    ------
    user:
        User to take action upon
    reason:
        Reason of action
    duration:
        Digits followed by either s, m, h, d or w. For example: 1d 12h 30m 45s
    weight:
        Weight of this infraction
    """
    if type(duration) is str:
        duration = total_seconds(duration)
    r = await infraction(ctx, type_=models.Types.Timeout, user=user, reason=reason, duration=duration, weight=weight)
    await ctx.bot.modify_guild_member(
        ctx.guild_id,
        user.id,
        mute=None,
        deaf=None,
        communication_disabled_until=datetime.utcnow() + duration,
        reason=reason or ctx.t("default_reason", moderator=ctx.user.username),
    )
    return r


@register(group=Groups.HELPER, main=infraction, aliases=["kick"])
# @button(style=Button_Styles.SECONDARY, emoji=Emoji(name="🏌️‍♂️"))
async def kick(ctx: Context, user: User, reason: str = None) -> str:
    """
    Kick User

    Params
    ------
    user:
        User to take action upon
    reason:
        Reason of action
    """
    r = await infraction(ctx, type_=models.Types.Kick, user=user, reason=reason)
    await ctx.bot.remove_guild_member(
        ctx.guild_id, user.id, reason=reason or ctx.t("default_reason", moderator=ctx.user.username)
    )
    return r


@register(group=Groups.MODERATOR, main=infraction, aliases=["ban"])
# @button(style=Button_Styles.DANGER, emoji=Emoji(name="🔨"))
async def ban(ctx: Context, user: User, reason: str = None, *, delete_messages: int = None) -> str:
    """
    Ban User

    Params
    ------
    user:
        User to take action upon
    reason:
        Reason for the ban
    delete_messages:
        Number of days to delete message for
    """
    r = await infraction(ctx, type_=models.Types.Ban, user=user, reason=reason)
    await ctx.bot.create_guild_ban(
        ctx.guild_id,
        user.id,
        reason=reason or ctx.t("default_reason", moderator=ctx.user.username),
        delete_message_days=delete_messages,
    )
    return r


@register(group=Groups.ADMIN, main=infraction, aliases=["unban"])
async def unban(ctx: Context, user: User, reason: str = None) -> str:
    """
    Unban User

    Params
    ------
    user:
        User to take action upon
    reason:
        Reason of action
    """
    r = await infraction(ctx, type_=models.Types.Unban, user=user, reason=reason)
    await ctx.bot.remove_guild_ban(
        ctx.guild_id, user.id, reason=reason or ctx.t("default_reason", moderator=ctx.user.username)
    )
    return r


@register(group=Groups.ADMIN, main=infraction)
# @select()
async def expire(ctx: Context, infraction_id: int) -> str:  # TODO: Autocomplete support
    """
    Expires an infraction

    Params
    ------
    infraction_id:
        Infraction to expire
    """
    session = ctx.db.sql.session()
    _infraction: models.Infraction = (
        session.query(models.Infraction)
        .filter(models.Infraction.server_id == ctx.guild_id, models.Infraction.id == infraction_id)
        .first()
    )

    if not _infraction:
        return ctx.t("not_found")

    now = datetime.now(tz=timezone.utc)
    if _infraction.expires_at and _infraction.expires_at <= now:
        return ctx.t("already_expired")

    _infraction.expires_at = now
    session.commit()
    return ctx.t(
        "success_expire",
        reason=_infraction.reason,
        moderator_id=_infraction.moderator_id,
        user_id=_infraction.user_id,
        id=_infraction.id,
    )


actions = [warn, timeout, kick, ban]


@register(group=Groups.GLOBAL, main=infraction, aliases=["infractions"], private_response=True)
# @menu_user("Infractions")
async def list_(ctx: Context, user: User = None) -> Embed:
    """
    Lists user's infractions

    Params
    ------
    user:
        User to display infractions of. Can only be used by Moderators
    """
    if not ctx.permission_group.can_use(Groups.HELPER):
        if user.id != ctx.user_id:
            user = ctx.user

    session = ctx.db.sql.session()
    infractions: list[models.Infraction] = (
        session.query(models.Infraction)
        .filter(models.Infraction.user_id == user.id, models.Infraction.server_id == ctx.guild_id)
        .order_by(sa.desc(models.Infraction.id))
        .all()
    )

    width, id_width, active = 0, 0, 0
    components = []
    now = datetime.now(tz=timezone.utc)

    for _infraction in infractions:
        translated = ctx.t(_infraction.type.name)

        if len(translated) > width:
            width = len(translated)

        if len(str(_infraction.id)) > id_width:
            id_width = len(str(_infraction.id))

        if (not _infraction.expires_at or _infraction.expires_at >= now) and _infraction.type not in {
            models.Types.Timeout,
            models.Types.Unban,
            models.Types.Report,
        }:
            active += _infraction.weight or 0

    str_infractions = "\n".join(i.as_string(ctx, width=width, id_width=id_width) for i in infractions[:10])

    if not str_infractions:
        return ctx.t("no_infractions")

    active = round(active)

    total = ctx.cache.settings.get(types.Setting.Auto_Ban_Infractions, 5)
    danger = ctx.cache.settings.get(types.Setting.Auto_Mute_Infractions, 3)

    remaining_to_auto_mute = danger - active
    remaining_to_auto_ban = total - danger

    currently_active = ["🔴"] * active
    currently_active += ["🟢"] * remaining_to_auto_mute
    currently_active += ["🟡"] * remaining_to_auto_ban

    colors = {
        1: "#16c60c",
        2: "#fff100",
        3: "#e87612",
        4: "#e81224",
    }
    color = colors[
        1 if remaining_to_auto_mute > 0 else 2 if remaining_to_auto_ban - 1 > 0 else 3 if remaining_to_auto_ban else 4
    ]

    e = (
        Embed()
        .set_description(str_infractions)
        .set_author(ctx.t("title", username=user.username), icon_url=user.get_avatar())
        .set_color(color)
        .set_footer(
            ctx.t(
                "counter",
                currently_active="-".join(currently_active),
                active=active,
                total=len(infractions),
            )
        )
    )

    if ctx.permission_group.can_use(Groups.MODERATOR):
        # TODO: Version based on decorated functions instead of helper function
        # components.append([action.button(custom_id=user.id, label=ctx.t(action.name)) for action in actions])
        components.append(instant_actions(user.id))

    if ctx.permission_group.can_use(Groups.ADMIN):
        _ = [
            Select_Option(label=f"#{i.id}", value=i.id, description=i.reason[:50] if i.reason else ctx.t("no_reason"))
            for i in infractions[:25]
            if not i.expires_at or i.expires_at >= now
        ]
        if _:
            # TODO: Version based on decorated functions instead of helper class
            # components.append(Row(expire.select(*_, placeholder=ctx.t("expire_placeholder"))))
            components.append(Row(ExpireInfractions(*_, placeholder=ctx.t("expire_placeholder"))))

    return Message(embeds=[e], components=components)


@register(group=Groups.GLOBAL)
# @menu_message("Report")
async def report(ctx: Context, msg: str) -> str:
    """
    Report situation on server to Moderators

    Params
    ------
    msg:
        Message about what's happening
    """
    _msg = await ctx.reply(ctx.t("processing"))

    link = Discord_Paths.MessageLink.link.format(
        guild_id=ctx.guild_id, channel_id=ctx.channel_id, message_id=ctx.data.id
    )
    embeds = []
    e = (
        Embed()
        .set_title(ctx.t("report_author", username=ctx.data.author.username))
        .set_color("#C29D60")
        .set_author(str(ctx.data.author), icon_url=ctx.data.author.get_avatar())
        .set_url(link)
    )
    if msg:
        e.set_description(msg)
    embeds.append(e)
    if ctx.data.referenced_message:
        ref = ctx.data.referenced_message
        ref_url = Discord_Paths.MessageLink.link.format(
            guild_id=ref.guild_id, channel_id=ref.channel_id, message_id=ref.id
        )
        e = (
            Embed()
            .set_title(ctx.t("reference_author", username=ref.author.username))
            .set_description(ref.content)
            .set_color("#a52f37")
            .set_author(str(ref.author), icon_url=ref.author.get_avatar())
            .set_url(ref_url)
        )
        if ref.attachments:
            e.add_field(
                ctx.t("attachments"),
                "\n".join([f"[{i.filename}.{i.content_type.split('/')[-1]}]({i.url})" for i in ref.attachments]),
            )
        embeds.append(e)
    components = [Row(LinkButton(ctx.t("jump_to_message"), link))]

    start = time.time()
    # for moderator in filter(lambda x: ctx.data.channel_id in x["moderated_channels"] or language in x["languages"], ctx.cache.moderators): # TODO: Support for per channel moderation
    mod_roles = ctx.cache.groups[Groups.MODERATOR]
    reported_to = 0
    for moderator in list(
        filter(lambda x: any(role in ctx.cache.members[x].roles for role in mod_roles), ctx.cache.members)
    ):
        # for moderator in list(filter(lambda x: ctx.cache.cachedRoles(ctx.cache.members[x].roles).can_use(Groups.MODERATOR), ctx.cache.members)):
        if ctx.cache.members[moderator].user.bot or (
            moderator not in ctx.cache.moderators or ctx.cache.moderators[moderator].status not in ["online", "idle"]
        ):
            continue

        # await ctx.cache.logging["report"].log_dm(moderator, embeds, components) # TODO: Make it possible to log via logger instead of here
        dm = await ctx.bot.create_dm(moderator)
        await ctx.bot.create_message(dm.id, embeds=embeds, components=components)
        reported_to += 1

    end = time.time()
    if reported_to:
        await _msg.edit(ctx.t("result", amount=reported_to, duration=f"{end-start:.2}"))
        await ctx.data.react(ctx.bot.emoji.get("success"))
    else:
        await _msg.edit(ctx.t("no_online"))
        await ctx.bot.create_message(
            ctx.channel_id,
            ctx.t("report_waiting", moderator_id=496201383524171776),  # TODO: Dehardcode role ID!
            embeds=embeds,
            message_reference=ctx.data.message_reference
            or Message_Reference(message_id=ctx.data.id, channel_id=ctx.data.channel_id, guild_id=ctx.data.guild_id),
            allowed_mentions=None,
        )


@onDispatch
async def presence_update(self: Bot, data: Presence_Update):
    member = self.cache[data.guild_id].members.get(data.user.id)
    if member and self.cache[data.guild_id].cachedRoles(member.roles).can_use(Groups.MODERATOR):
        self.cache[data.guild_id].moderators[data.user.id] = data
