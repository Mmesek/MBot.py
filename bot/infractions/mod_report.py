from collections import Counter
from datetime import datetime, timedelta, timezone
from io import StringIO

import pandas as pd
from MFramework import Attachment, Context, Groups, register
from MFramework.utils.utils import get_usernames

from . import models
from .commands import infraction


@register(group=Groups.ADMIN, main=infraction)
async def mod_summary(ctx: Context, month: int = None) -> Attachment:
    """
    Summary of actions taken by moderators in specified month
    Params
    ------
    month:
        Number of Month to summarize. 0 to create summary of entire year
    """
    s = ctx.db.sql.session()
    now = datetime.now(tz=timezone.utc)
    now = datetime(now.year, now.month, 1)

    if not month:
        last_month = now - timedelta(days=28)
        last_month = datetime(last_month.year, last_month.month, 1)
        next_month = datetime(last_month.year, last_month.month + 1, 1)
    else:
        last_month = datetime(now.year, month, 1)
        next_month = datetime(now.year, month + 1, 1)  # NOTE: Possible issue with December

    infractions = s.query(models.Infraction).filter(models.Infraction.server_id == int(ctx.guild_id))

    if month != 0:
        infractions = infractions.filter(
            models.Infraction.timestamp >= last_month,
            models.Infraction.timestamp < next_month,
        )

    infractions: list[models.Infraction] = infractions.all()
    moderators: dict[int, Counter] = {}

    columns = {"Infractions", "Commands Used"}
    stats = {}

    for infraction in infractions:
        if infraction.moderator_id not in moderators:
            moderators[infraction.moderator_id] = Counter()

        moderators[infraction.moderator_id].update([infraction.type.name])
        moderators[infraction.moderator_id].update(["Infractions"])
        columns.add(infraction.type.name)

    commands_used = ctx.db.influx.get_command_usage(ctx.guild_id)

    for _table in commands_used:
        for record in _table.records:
            user_id = record.values.get("user")
            if user_id in moderators:
                moderators[user_id].update({"Commands Used": record.get_value() or 0})

    for moderator_id in moderators.keys():
        try:
            uname = await get_usernames(ctx.bot, ctx.guild_id, moderator_id)
        except:
            uname = moderator_id
        stats[uname] = moderators[moderator_id]

    buffered = StringIO()

    data = pd.DataFrame.from_dict(moderators, orient="index", columns=columns)
    data.sort_values(by="Infractions")
    data.to_csv(buffered)

    img_str = "moderator" + buffered.getvalue()

    return Attachment(file=img_str, filename=f"moderation-report{last_month.year}-{last_month.month}.csv")
