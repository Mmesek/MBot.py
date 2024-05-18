from datetime import date, datetime

from MFramework import Context, Embed, Groups, Interaction, User, register
from MFramework.utils.leaderboards import Leaderboard, Leaderboard_Entry

from bot.events.Christmas import general, snowballs  # noqa: F401
from bot.events.Halloween import fear, general  # noqa: F401
from bot.events.Valentines import general, heartbreaking, matchmaker  # noqa: F401


@register(group=Groups.GLOBAL)
async def event(ctx: Context, *, language):
    """Event related commands"""
    pass


# @register(group=Groups.GLOBAL, main=event, default=True)
async def help(ctx: Context, *, language):
    """Shows help related to Event"""
    # Possibly move to help?
    pass


async def Leaderboards(interaction: Interaction, current: str) -> list[str]:
    return [
        (i["name"], f"{i['instance_id']}&{i['starts']}&{i['ends']}")
        for i in await interaction._Client.db.supabase.rpc(
            "list_leaderboards", server_id=interaction.guild_id, name=f"%{current}%" if current else None
        )
    ]


@register(group=Groups.GLOBAL, main=event)
async def leaderboard(ctx: Context, event: Leaderboards, user: User = None, limit: int = 10, year: int = None) -> Embed:
    """Shows event Leaderboards"""
    instance_id, after, before = event.split("&")

    after = datetime.fromisoformat(after)
    before = datetime.fromisoformat(before)
    if year:
        after.year, before.year = date(year, after.month, after.day), date(year, before.month, before.day)
    after, before = after.isoformat(), before.isoformat()

    results = await ctx.db.supabase.rpc(
        "get_leaderboard", server_id=ctx.guild_id, instance_id=instance_id, limit_at=limit, after=after, before=before
    )

    if not any(x["user_id"] == user.id for x in results):
        results.extend(
            await ctx.db.supabase.rpc(
                "get_leaderboard",
                server_id=ctx.guild_id,
                user_id=user.id,
                instance_id=instance_id,
                limit_at=limit,
                after=after,
                before=before,
            )
        )

    r = set(Leaderboard_Entry(ctx, x["user_id"], x["quantity"]) for x in results)
    leaderboard = Leaderboard(ctx, user.id, r, limit)
    return [leaderboard.as_embed(f"{event.value}'s Leaderboard")]


# @register(group=Groups.GLOBAL, main=event)
async def history(ctx: Context, user: User = None, *, language):
    """Shows User's event history

    Params
    ------
    user:
        User's history to show
    """
    pass


# @register(group=Groups.GLOBAL, main=event)
async def stats(ctx: Context, *, language):
    """Shows faction statistics"""
    pass


# @register(group=Groups.GLOBAL, main=event)
async def profile(ctx: Context, user: User = None, *, language):
    """Shows User's event profile

    Params
    ------
    user:
        User's profile to show
    """
    pass


# @register(group=Groups.GLOBAL, main=event)
async def cooldown(ctx: Context, *, language):
    """Shows Current cooldowns"""
    pass


# @register(group=Groups.MODERATOR, main=event)
async def summary(ctx: Context, *, language):
    """Shows summary of Current Event"""
    pass
