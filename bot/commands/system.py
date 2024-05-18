from MFramework import Context, Groups, log, register

from bot.database.types import Flags
from bot.utils.timers import finalize


@register(group=Groups.SYSTEM, interaction=False)
async def shutdown(ctx: Context, *args, **kwargs):
    """Shuts bot down."""
    if ctx.cache.is_tracking(Flags.Voice):
        for v in ctx.cache.voice:
            users = []
            for u in ctx.cache.voice[v]:
                users.append(u)
            for u in users:
                finalize(ctx.bot, ctx.guild_id, v, u)
    if ctx.cache.context:
        s = ""
        for channel_id, author_id in ctx.cache.context[ctx.guild_id]:
            s += f"\n<#{channel_id}> <@{author_id}>"
            # await self.message(channel_id, "Context ended. To retry type the command that started context again later.")
        if s != "":
            await ctx.reply("Ended contexts: " + s)
    await ctx.bot.close()
    log.info("Received shutdown command. Shutting down.")


@register(group=Groups.SYSTEM, interaction=False)
async def updateStatus(
    ctx: Context, status="How the World Burns", status_kind="Online", status_type=3, afk=False, *args, **kwargs
):
    """Changes Bot's status
    Params
    ------
    Kind:
        Online/dnd/idle/invisible/offline
    Type:
        0 - Playing, 1 - Streaming, 2 - Listening, 3 - Watching"""
    await ctx.bot.presence_update(status_kind, status, status_type, afk)


@register(group=Groups.SYSTEM, interaction=False)
async def reloadCommands(ctx: Context, *args, **kwargs):
    """Reloads commands files.
    This probably needs to be placed in another file but well, it's here currently FOR SCIENCE."""
    import importlib

    importlib.reload(__name__)


@register(group=Groups.SYSTEM, interaction=False)
async def update(ctx: Context, *args, language, **kwargs):
    """Pulls new commits"""
    import git

    repos = ctx.bot.cfg.get("Repos", {})
    should_reset = False
    msg = []
    for repo in repos:
        r = git.Repo(repos[repo]).remotes.origin
        previous = r.repo.head.commit.hexsha
        g = r.pull()
        if g[0].commit.hexsha == previous:
            msg.append(f"[{repo}] No new commits.")
        else:
            should_reset = True
            msg.append(f"[{repo}] Pulled `{g[0].commit.summary}`")
    await ctx.reply("\n".join(msg))
    if should_reset:
        import os
        import sys

        log.warning("Restarting bot")
        sys.stdout.flush()
        os.execl(sys.executable, sys.executable, *sys.argv)
