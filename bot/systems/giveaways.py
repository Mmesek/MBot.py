import asyncio
from datetime import datetime, timezone

import sqlalchemy as sa
from MFramework import (
    Bot,
    ChannelID,
    Context,
    Embed,
    Groups,
    Guild,
    Message,
    Snowflake,
    User,
    log,
    onDispatch,
    register,
)
from MFramework.database.alchemy.mixins import ServerID
from MFramework.database.alchemy.mixins import Snowflake as db_Snowflake
from mlib.converters import total_seconds
from mlib.database import Base, Timestamp
from mlib.random import chance, pick

from bot.utils.scheduler import wait_for_scheduled_task


class Giveaway(Timestamp, ServerID, db_Snowflake, Base):
    channel_id: Snowflake = sa.Column(sa.BigInteger, nullable=False)
    """Channel in which Giveaway is being held"""
    user_id: Snowflake = sa.Column(sa.BigInteger, nullable=False)
    """User that hosts this giveaway"""
    ends_at: datetime = sa.Column(sa.TIMESTAMP(timezone=True))
    """Date when giveaway ends"""
    prize: str = sa.Column(sa.String, nullable=True)
    """Prize in a giveaway"""
    amount: int = sa.Column(sa.Integer, default=1)
    """Amount of winners"""
    finished: bool = sa.Column(sa.Boolean, default=False)
    """Whether it's finished"""

    def create_embed(
        self, ctx: Context, winners: list[str] = None, chance: float = None, t_suffix: str = "", description: str = None
    ):
        """Creates Giveaway's embed

        Parameters
        ----------
        winners:
            List of users that won
        chance:
            Chance a single user had in winning
        t_suffix:
            Suffix to add to translation key
        description:
            Custom description of embed
        """
        kwargs = {
            "prize": self.prize,
            "count": len(winners) if winners and len(winners) < self.amount else self.amount,
            "winners": ", ".join(winners) if winners else None,
            "chance": chance,
            "host": f"<@{self.user_id}>",
        }
        return (
            Embed()
            .set_title(ctx.t("title" + t_suffix, **kwargs))
            .set_description(description or ctx.t("embed_description" + t_suffix, **kwargs))
            .set_footer(ctx.t("end_time" + t_suffix, **kwargs))
            .set_timestamp(self.ends_at.isoformat())
        )

    async def create_message(self, ctx: Context, description: str = None):
        """Creates message and reacts"""
        msg = await ctx.bot.create_message(self.channel_id, embeds=[self.create_embed(ctx, description=description)])
        self.id = msg.id
        await msg.react("🎉")

    async def finish(self, ctx: Context, amount: int = None, t_key: str = "end_message"):
        """
        Chooses winners, edits original message and sends new one mentioning winners

        Parameters
        ----------
        amount:
            Overwrite to an amount of winners
        t_key:
            Translation key to use
        """
        users = await Message(_Client=ctx.bot, channel_id=self.channel_id, id=self.id).get_reactions("🎉")
        winners = [f"<@{i}>" for i in pick([i.id for i in users], amount or self.amount)]

        embed = self.create_embed(ctx, winners=winners, chance=chance(len(users)), t_suffix="_finished")
        await ctx.bot.edit_message(self.channel_id, self.id, embeds=[embed])
        self.finished = True

        await ctx.bot.create_message(
            self.channel_id,
            ctx.t(
                t_key,
                winners=", ".join(winners),
                prize=self.prize,
                count=len(users),
                server=self.server_id,
                channel=self.channel_id,
                message=self.id,
            ),
            allowed_mentions=None,
        )


@register(group=Groups.MODERATOR)
async def giveaway(
    *,
    bot: Bot,
    t: Giveaway = None,
    message_id: Snowflake = None,
    amount: int = None,
    instant_end: bool = False,
    ctx: Context = None,
    key: str = "end_message",
):
    """
    Giveaways

    Params
    ------
    t:
        Giveaway's object
    message_id:
        ID of message with a giveaway
    amount:
        Amount of winners
    instant_end:
        Whether should wait for `.ends_at` or end instantly
    key:
        Translation key to use for message
    """
    if t and not instant_end:
        await wait_for_scheduled_task(t.ends_at)

    s = bot.db.sql.session()
    t = s.query(Giveaway).filter(Giveaway.id == (message_id or t.id), Giveaway.finished == False if t else True).first()
    if instant_end:
        t.ends_at = datetime.now(tz=timezone.utc)

    ctx = ctx or Context(bot.cache, bot, Message(author=User()), giveaway._cmd)
    await t.finish(ctx, amount, key)
    s.commit()


@register(group=Groups.MODERATOR, main=giveaway, private_response=True)
async def create(
    ctx: Context,
    prize: str,
    duration: str = "1h",
    amount: int = 1,
    description: str = None,
    channel: ChannelID = None,
    user: User = None,
):
    """
    Create new giveaway

    Params
    ------
    prize:
        Giveaway's prize
    duration:
        Digits followed by either s, m, h, d or w. For example: 1d 12h 30m 45s
    amount:
        Amount of winners, default 1
    description:
        Description of the giveaway
    channel:
        Channel in which giveaway should be created
    user:
        User in whose name this giveaway is being created
    """
    finish = datetime.now(tz=timezone.utc) + total_seconds(duration)

    _giveaway = Giveaway(
        server_id=ctx.guild_id,
        channel_id=channel or ctx.channel_id,
        user_id=user.id,
        ends_at=finish,
        prize=prize,
        amount=amount,
    )
    await _giveaway.create_message(ctx, description=description)

    s = ctx.db.sql.session()
    s.add(_giveaway)
    s.commit()

    add_giveaway(ctx.bot, ctx.guild_id, _giveaway)

    return ctx.t("success")


@register(group=Groups.MODERATOR, main=giveaway, private_response=True)
async def end(ctx: Context, message_id: Snowflake):
    """
    Ends Giveaway

    Params
    ------
    message_id:
        ID of giveaway message to finish
    """
    task = ctx.cache.tasks.get("giveaways", {}).get(message_id, None)
    task.cancel()

    await giveaway(bot=ctx.bot, message_id=message_id, instant_end=True, ctx=ctx, key="end_message")
    return ctx.t("success")


@register(group=Groups.MODERATOR, main=giveaway, private_response=True)
async def reroll(ctx: Context, message_id: Snowflake, amount: int = 0):
    """
    Rerolls giveaway

    Params
    ------
    message_id:
        ID of giveaway message to reroll
    amount:
        Amount of rewards to reroll, defaults to all
    """
    await giveaway(bot=ctx.bot, message_id=message_id, amount=amount, ctx=ctx, key="reroll_message")
    return ctx.t("success")


@onDispatch(event="message_delete")
async def delete(self: Bot, data: Message):
    """Deletes Giveaway"""
    task = self.cache[data.guild_id].tasks.get("giveaways", {}).get(data.id, None)
    if not task:
        return
    task.cancel()

    s = self.db.sql.session()
    g = s.query(Giveaway).filter(Giveaway.id == data.id, Giveaway.finished == False).first()
    s.delete(g)
    s.commit()


def add_giveaway(self: Bot, guild_id: Snowflake, _giveaway: Giveaway):
    if "giveaways" not in self.cache[guild_id].tasks:
        self.cache[guild_id].tasks["giveaways"] = {}
    if _giveaway.id not in self.cache[guild_id].tasks["giveaways"]:
        log.debug("Adding Giveaway %s task to guild %s", _giveaway.id, guild_id)
        self.cache[guild_id].tasks["giveaways"][_giveaway.id] = asyncio.create_task(giveaway(bot=self, t=_giveaway))


@onDispatch(event="guild_create", priority=101)
async def add_giveaways(self: Bot, data: Guild):
    s = self.db.sql.session()
    giveaways = s.query(Giveaway).filter(Giveaway.server_id == data.id, Giveaway.finished == False).all()
    for _giveaway in giveaways:
        add_giveaway(self, data.id, _giveaway)
