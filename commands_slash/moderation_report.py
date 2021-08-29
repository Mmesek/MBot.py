from MFramework import *
import MFramework.database.alchemy as db
from MFramework.utils.utils import get_usernames
from datetime import datetime, timedelta, timezone
from MFramework import register, Groups

@register(group=Groups.SYSTEM, interaction=False)
async def mod_report(ctx: Context, month: int=None, guild_id: Snowflake = 0, *args, **kwargs):
    await ctx.deferred()
    s = ctx.db.sql.session()
    now = datetime.now(tz=timezone.utc)
    now = datetime(now.year, now.month, 1)
    if not month:
        last_month = now - timedelta(days=28)
        last_month = datetime(last_month.year, last_month.month, 1)
        next_month = datetime(last_month.year, last_month.month + 1, 1)
    else:
        last_month = datetime(now.year, month, 1)
        next_month = datetime(now.year, month + 1, 1) # Possible issue with December
    if guild_id == 0:
        guild_id = ctx.guild_id
    infractions = s.query(db.log.Infraction).filter(db.log.Infraction.server_id == int(guild_id), db.log.Infraction.timestamp >= last_month, db.log.Infraction.timestamp < next_month).all()
    moderators = {}
    table = ["Warn", "Temp_Mute", "Mute", "Unmute",
        "Kick", "Temp_Ban", "Ban", "Unban"] #, "chat", "voice"]
    uids = {}
    for infraction in infractions:
        if infraction.moderator_id not in uids:
            try:
                uname = await get_usernames(ctx.bot, infraction.server_id, infraction.moderator_id)
            except:
                uname = infraction.moderator_id
            uids[infraction.moderator_id] = uname
        else:
            uname = uids.get(infraction.moderator_id)
        if uname not in moderators:
            moderators[uname] = {i:0 for i in table}
        try:
            moderators[uname][infraction.type.name] += 1
        except:
            pass
    #for uid in uids:
        #activity = s.query(db.log.Activity).filter(db.log.Activity.server_id == int(guild_id), db.log.Activity.user_id == uid, db.log.Activity.timestamp >= last_month, db.log.Activity.timestamp <= now).first()
        #moderators[uids.get(uid)]["chat"] = activity.Chat if activity else 0
        #moderators[uids.get(uid)]["voice"] = activity.Voice if activity else 0
    import pandas as pd
    from io import StringIO
    buffered = StringIO()

    data = pd.DataFrame.from_dict(moderators, orient='index', columns=table)
    data.to_csv(buffered)

    img_str = 'moderator'+buffered.getvalue()

    msg = await ctx.reply(file=img_str, filename=f"moderation-report{last_month.year}-{last_month.month}.csv")