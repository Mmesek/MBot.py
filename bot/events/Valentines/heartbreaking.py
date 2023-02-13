import enum

import sqlalchemy as sa
from MFramework import Allowed_Mentions, Context, Embed, User, register
from MFramework.commands.cooldowns import CacheCooldown, cooldown
from MFramework.commands.decorators import Chance, Event
from mlib.database import Base, Timestamp

from .general import valentines


class Heart_Log(Timestamp, Base):
    guild_id = sa.Column(sa.BigInteger, primary_key=True)
    user_id = sa.Column(sa.BigInteger, primary_key=True)
    target_id = sa.Column(sa.BigInteger, primary_key=True)
    state = sa.Column(sa.String)


@register(main=valentines)
async def heart():
    """Heartbreaking Event commands"""
    pass


class Arrows(enum.Enum):
    Heartbreaker = 0
    Cupid = 1


@register(main=heart)
@Event(month=2, day=14)
@cooldown(minutes=10, logic=CacheCooldown)
@Chance(50, "You've missed! Their heart remains unchanged")
async def shoot(ctx: Context, user: User, arrow: Arrows):
    """
    Break someone's heart! Or pair them. Only if they are not protected
    Params
    ------
    user:
        User whose heart you want to shoot at
    arrow:
        Which arrow to use
    """
    session = ctx.db.sql.session()

    target_state = (
        session.query(Heart_Log)
        .filter(Heart_Log.guild_id == ctx.guild_id, Heart_Log.target_id == user.id)
        .order_by(Heart_Log.timestamp.desc())
        .first()
    )

    if target_state:
        if target_state.state in {"protected", "mended"}:
            return "Your target is protected! You can't change their heart now."
        elif arrow == Arrows.Heartbreaker and target_state.state == "broken":
            return "Your target is already heartbroken!"

    session.add(
        Heart_Log(
            guild_id=ctx.guild_id,
            user_id=ctx.user_id,
            target_id=user.id,
            state="broken" if arrow == Arrows.Heartbreaker else "butterflies",
        )
    )
    session.commit()
    await ctx.reply(f"You've hit <@{user.id}> with {arrow.name}!", allowed_mentions=Allowed_Mentions(users=[user.id]))


@register(main=heart)
@Event(month=2, day=14)
@cooldown(minutes=10, logic=CacheCooldown)
@Chance(50, "You've failed! Their heart remains unprotected")
async def protect(ctx: Context, user: User):
    """
    Protect someone's heart!
    Params
    ------
    user:
        User whose heart you want to protect
    """
    session = ctx.db.sql.session()
    last_state = (
        session.query(Heart_Log)
        .filter(Heart_Log.guild_id == ctx.guild_id, Heart_Log.target_id == ctx.user_id)
        .order_by(Heart_Log.timestamp.desc())
        .first()
    )

    if last_state and last_state.state == "broken":
        return "You can't protect someone else's heart while your own is broken!"

    target_state = (
        session.query(Heart_Log)
        .filter(Heart_Log.guild_id == ctx.guild_id, Heart_Log.target_id == user.id)
        .order_by(Heart_Log.timestamp.desc())
        .first()
    )

    if target_state:
        if target_state.state == "broken":
            return "You are too late, Target's heart is already broken!"
        elif target_state == "protected":
            return "Target's heart is already protected by someone else!"

    previous = (
        session.query(Heart_Log)
        .filter(Heart_Log.guild_id == ctx.guild_id, Heart_Log.user_id == ctx.user_id, Heart_Log.state == "protected")
        .order_by(Heart_Log.timestamp.desc())
        .first()
    )
    note = ""

    if previous:
        session.add(Heart_Log(guild_id=ctx.guild_id, user_id=ctx.user_id, target_id=user.id, state="broken"))
        note = f"<@{previous.target_id}> is now left heartbroken!"

    session.add(Heart_Log(guild_id=ctx.guild_id, user_id=ctx.user_id, target_id=user.id, state="protected"))
    session.commit()

    if not last_state or last_state.state == "protected":
        if last_state.user_id == user.id:
            await ctx.reply(
                f"<@{ctx.user_id}> and <@{user.id}> are now in a relationship! {note}",
                allowed_mentions=Allowed_Mentions(users=[user.id]),
            )
            return

    await ctx.reply(
        f"<@{ctx.user_id}> is now protecting <@{user.id}>'s heart! {note}",
        allowed_mentions=Allowed_Mentions(users=[user.id]),
    )


@register(main=heart)
@Event(month=2, day=14)
@cooldown(minutes=10, logic=CacheCooldown)
@Chance(50, "You've failed! Their heart remains broken")
async def mend(ctx: Context, user: User):
    """
    Mend someone's broken heart, if you have a broken heart too
    Params
    ------
    user:
        User whose heart you want to mend
    """
    session = ctx.db.sql.session()
    last_state = (
        session.query(Heart_Log)
        .filter(Heart_Log.guild_id == ctx.guild_id, Heart_Log.target_id == ctx.user_id)
        .order_by(Heart_Log.timestamp.desc())
        .first()
    )

    if not last_state or last_state.state != "broken":
        return "You can only mend fellow broken hearts!"

    target_state = (
        session.query(Heart_Log)
        .filter(Heart_Log.guild_id == ctx.guild_id, Heart_Log.target_id == user.id)
        .order_by(Heart_Log.timestamp.desc())
        .first()
    )

    if target_state:
        if target_state.state != "broken":
            return "Target's heart is not broken!"

    previous = (
        session.query(Heart_Log)
        .filter(Heart_Log.guild_id == ctx.guild_id, Heart_Log.user_id == ctx.user_id, Heart_Log.state == "mended")
        .order_by(Heart_Log.timestamp.desc())
        .first()
    )
    note = ""

    if previous:
        session.add(Heart_Log(guild_id=ctx.guild_id, user_id=ctx.user_id, target_id=user.id, state="broken"))
        note = f"<@{previous.target_id}> is now left heartbroken once again!"

    session.add(Heart_Log(guild_id=ctx.guild_id, user_id=ctx.user_id, target_id=user.id, state="mended"))
    session.commit()

    if not last_state or last_state.state == "protected":
        if last_state.user_id == user.id:
            await ctx.reply(
                f"<@{ctx.user_id}> and <@{user.id}> are now in a relationship! {note}",
                allowed_mentions=Allowed_Mentions(users=[user.id]),
            )
            return

    await ctx.reply(
        f"<@{ctx.user_id}> has mended <@{user.id}>'s heart! {note}",
        allowed_mentions=Allowed_Mentions(users=[user.id]),
    )
