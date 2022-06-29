from datetime import datetime, timezone

from MFramework import ChannelID, Embed, Groups, Snowflake, User, register
from MFramework.bot import Bot, Context
from mlib.converters import total_seconds
from mlib.localization import tr
from mlib.random import chance, pick
from mlib.utils import replaceMultiple

from ..database import models as db
from ..utils.scheduler import add_task, scheduledTask, wait_for_scheduled_task


@register(group=Groups.MODERATOR)
async def giveaway(ctx: Context, *, language):
    """Giveaways"""
    pass


@register(group=Groups.MODERATOR, main=giveaway, private_response=True)
async def create(
    ctx: Context,
    prize: str,
    duration: str = "1h",
    description: str = None,
    winner_count: int = 1,
    reactions: str = "🎉",
    channel: ChannelID = None,
    hidden: bool = False,
    author: User = None,
    *,
    language,
):
    """Create new giveaway
    Params
    ------
    prize:
        Giveaway's prize
    duration:
        Digits followed by either s, m, h, d or w. For example: 1d 12h 30m 45s
    description:
        [Optional] Description of the giveaway
    winner_count:
        Amount of winners, default 1
    reactions:
        Whether it should use different emoji than 🎉 or multiple (Separate using ,)
    channel:
        Channel in which giveaway should be created
    hidden:
        Whether reactions should be removed
    author:
        User in whose name this giveaway is being created
    """
    finish = datetime.now(tz=timezone.utc) + total_seconds(duration)
    msg = await ctx.bot.create_message(
        channel, embeds=[createGiveawayEmbed(language, finish, prize, winner_count, custom_description=description)]
    )
    for reaction in reactions.split(","):
        await msg.react(replaceMultiple(reaction.strip(), ["<:", ":>", ">"], ""))
    ctx.cache.giveaway_messages.append(msg.id)
    add_task(
        ctx.bot,
        ctx.guild_id,
        db.types.Task.Giveaway if not hidden else db.types.Task.Hidden_Giveaway,
        channel,
        msg.id,
        author.id or ctx.member.user.id,
        datetime.now(tz=timezone.utc),
        finish,
        prize,
        winner_count,
    )
    await ctx.reply("Created", private=True)


@register(group=Groups.MODERATOR, main=giveaway, private_response=True)
async def delete(ctx: Context, message_id: Snowflake, *args, language, **kwargs):
    """
    Deletes Giveaway
    Params
    ------
    message_id:
        ID of giveaway message to delete
    """
    task = ctx.cache.tasks.get("giveaway", {}).get(int(message_id), None)
    if task is not None:
        task.cancel()
    s = ctx.db.sql.session()
    r = (
        s.query(db.Task)
        .filter(db.Task.server_id == ctx.guild_id)
        .filter(db.Task.type == db.types.Task.Giveaway)
        .filter(db.Task.message_id == int(message_id))
        .first()
    )
    s.delete(r)
    s.commit()
    await ctx.reply("Giveaway deleted Successfully", private=True)


@register(group=Groups.MODERATOR, main=giveaway, private_response=True)
async def end(ctx: Context, message_id: Snowflake, *, language):
    """
    Ends Giveaway
    Params
    ------
    message_id:
        ID of giveaway message to finish
    """
    task = ctx.cache.tasks.get("giveaway", {}).get(int(message_id), None)
    task.cancel()
    s = ctx.db.sql.session()
    task = (
        s.query(db.Task)
        .filter(db.Task.server_id == ctx.guild_id)
        .filter(db.Task.finished == False)
        .filter(db.Task.message_id == int(message_id))
        .first()
    )
    task.TimestampEnd = datetime.now(tz=timezone.utc)
    await giveaway(ctx, task)
    await ctx.reply("Giveaway ended Successfully")


@register(group=Groups.MODERATOR, main=giveaway, private_response=True)
async def reroll(ctx: Context, message_id: Snowflake, amount: int = 0, *, language):
    """
    Rerolls giveaway
    Params
    ------
    message_id:
        ID of giveaway message to reroll
    amount:
        Amount of rewards to reroll, defaults to all
    """
    s = ctx.db.sql.session()
    task = (
        s.query(db.Task)
        .filter(db.Task.server_id == ctx.guild_id)
        .filter(db.Task.type == db.types.Task.Giveaway)
        .filter(db.Task.message_id == message_id)
        .first()
    )
    from MFramework.utils.utils import get_all_reactions

    users = await get_all_reactions(ctx, task.channel_id, task.message_id, "🎉")
    winners = [f"<@{i}>" for i in pick([i.id for i in users], amount)]
    winners = ", ".join(winners)
    await ctx.create_message(
        task.ChannelID,
        tr(
            "commands.giveaway.rerollMessage",
            language,
            count=len(winners.split(",")),
            winners=winners,
            prize=task.Prize,
            participants=len(users),
            server=task.GuildID,
            channel=task.ChannelID,
            message=task.MessageID,
        ),
    )
    await ctx.reply("Giveaway rerolled Successfully")


def createGiveawayEmbed(
    l: str,
    finish,
    prize: str,
    winner_count: int,
    finished: bool = False,
    winners: str = "",
    chance: str = "",
    custom_description: str = None,
    host_id: Snowflake = None,
) -> Embed:
    translationStrings = ["title", "description", "endTime"]
    t = {}
    for i in translationStrings:
        translation = "commands.giveaway." + i
        if finished:
            translation += "Finished"
        if i == "description" and custom_description:
            t[i] = custom_description
        else:
            t[i] = tr(
                translation, l, prize=prize, count=winner_count, winners=winners, chance=chance, host=f"<@{host_id}>"
            )
    return (
        Embed()
        .setFooter(text=t["endTime"])
        .setTimestamp(finish.isoformat())
        .setTitle(t["title"])
        .setDescription(t["description"])
    )


@scheduledTask
async def giveaway(ctx: Bot, t: db.Task):
    await wait_for_scheduled_task(t.end)
    s = ctx.db.sql.session()
    task = (
        s.query(db.Task)
        .filter(db.Task.server_id == t.server_id)
        .filter(db.Task.type == t.type)
        .filter(db.Task.timestamp == t.timestamp)
        .filter(db.Task.finished == False)
        .first()
    )
    language = ctx.cache[t.server_id].language
    if t.type is not db.types.Task.Hidden_Giveaway:
        # from MFramework.utils.utils import get_all_reactions
        from MFramework import Message

        users = await Message(_Client=ctx, channel_id=task.channel_id, id=task.message_id).get_reactions("🎉")
        # users = await get_all_reactions(ctx, task.channel_id, task.message_id, '🎉')
    else:
        users = []  # FIXME?
        # users = s.query(db.GiveawayParticipants).filter(db.GiveawayParticipants.server_id == t.server_id, db.GiveawayParticipants.message_id == task.message_id, db.GiveawayParticipants.Reaction == 'Rune_Fehu:817360053651767335').all()
    winners = [f"<@{i}>" for i in pick([i.user_id if "hidden" in task.type.name else i.id for i in users], task.count)]
    winnerCount = len(winners)
    winners = ", ".join(winners)

    e = createGiveawayEmbed(
        language, task.end, task.description, winnerCount, True, winners, chance(len(users)), host_id=task.user_id
    )
    await ctx.edit_message(task.channel_id, task.message_id, None, e, None, None)
    await ctx.create_message(
        task.channel_id,
        tr(
            "commands.giveaway.endMessage",
            language,
            count=winnerCount,
            winners=winners,
            prize=task.description,
            participants=len(users),
            server=task.server_id,
            channel=task.channel_id,
            message=task.message_id,
        ),
        allowed_mentions=None,
    )
    task.finished = True
    s.commit()


@scheduledTask
async def hidden_giveaway(ctx: Context, t: db.Task):
    await giveaway(ctx, t)
