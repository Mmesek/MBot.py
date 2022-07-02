import time
from datetime import date

from MFramework import Attachment, Context, Groups, UserID, register
from mlib.utils import truncate

from . import models
from .commands import infraction


@register(group=Groups.ADMIN, main=infraction)
async def graph(
    ctx: Context,
    type: models.Types = None,
    resample: str = "D",
    locator: str = "Week",
    interval: int = 1,
    moderator: UserID = None,
    user: UserID = None,
    growth: bool = False,
):
    """Plot infractions over days
    Params
    ------
    type:
        Type of infraction to plot. Defaults to all
    resample:
        Range to group together. D = Day, W = Week, M = Month
    locator:
        How often a locator should be placed. Minute, hour, day, week, month or year
    interval:
        Interval of locator
    moderator:
        Moderator whose actions to plot exclusively
    user:
        User whose infractions to plot exclusively
    growth:
        Whether resample should NOT be applied
    """
    b = time.time()

    import matplotlib.pyplot as plt
    import pandas as pd
    from mlib import graphing

    f = time.time()
    _s = ctx.db.sql.session()

    infractions = _s.query(models.Infraction).filter(models.Infraction.server_id == ctx.guild_id)

    if type:
        infractions = infractions.filter(models.Infraction.type == type)

    if moderator != None:
        infractions = infractions.filter(models.Infraction.moderator_id == moderator)

    if user != None:
        infractions = infractions.filter(models.Infraction.user_id == user)

    infractions: list[models.Infraction] = infractions.all()

    s = time.time()

    total = {"Total Infractions": []}
    table = {
        "warn": "Warnings",
        "tempmute": "Temp Mutes",
        "mute": "Mutes",
        "unmute": "Unmutes",
        "timeout": "Timeouts",
        "kick": "Kicks",
        "tempban": "Temp Bans",
        "ban": "Bans",
        "unban": "Unbans",
    }

    for i in table.values():
        total[i] = []

    total["Others"] = []

    for each in infractions:
        i = pd.to_datetime(each.timestamp).tz_convert(None)
        total[table.get(each.type.name, "Others")] += [i]
        total["Total Infractions"] += [i]

    sd = time.time()

    for i in total:
        total[i] = sorted(total[i])

    d = time.time()
    fig, ax = plt.subplots()

    for i in total:
        if total[i] == []:
            continue
        if not growth:
            df = pd.Series(total[i], index=total[i])

            df = df.resample(resample).count()
            idf = pd.to_datetime(df.index)
            ax.plot(idf, df, label=i)  # tr('commands.graph.infractions', language), marker='o')
        else:
            df = pd.Series(total[i])
            ax.plot(df, df.index, label=i)  # tr('commands.graph.infractions', language))

    graphing.set_locator(ax, locator, interval)
    fig.autofmt_xdate()

    # Set Names
    graphing.set_legend(
        ax,
        ctx.t("title"),
        ctx.t("legend_y"),
        ctx.t("legend_x"),
        framealpha=1,
    )
    fig.tight_layout()

    img_str = graphing.create_image(fig)
    stats = ctx.t(
        "stats",
        total=truncate(time.time() - d, 2),
        gather=truncate(s - f, 2),
        sort=truncate(d - sd, 2),
        convert=truncate(sd - s, 2),
        imp=truncate(f - b, 2),
    )

    await ctx.reply(stats, attachments=[Attachment(file=img_str, filename=f"growth-{date.today()}.png")])
