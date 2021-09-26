async def handle_roles(self, data, l, levelRole, x, user_id):
    await self.add_guild_member_role(data.guild_id, user_id, levelRole.Role, "EXP Role")
    try:
        previous_role = l[x+1]
    except:
        return
    if not previous_role.Stacked and previous_role.Role in data.member.roles:
        await self.remove_guild_member_role(data.guild_id, user_id, previous_role.Role, "EXP Role")

async def handle_exp(self, data, e=None):
    if e is None:
        #user_id = data.user_id
        user_id = getattr(data, "user_id", None) or getattr(data, "author").id
        session = self.db.sql.session()
        from ..database import log, types
        EXP = log.Statistic.get(session, data.guild_id, user_id, types.Statistic.Chat)
        vEXP = log.Statistic.get(session, data.guild_id, user_id, types.Statistic.Voice)

    else:
        user_id = getattr(data, "user_id", None) or getattr(data, "author").id
        #user_id = data.author.id
    l = self.cache[data.guild_id].level_roles
    if l == []:
        return
    for x, levelRole in enumerate(l):
        if levelRole.Role not in data.member.roles:
            if levelRole.ReqRoles is not None and not all(i in data.member.roles for i in levelRole.ReqRoles):
                continue
            if levelRole.Type == 'AND' and (EXP >= levelRole.ReqEXP and vEXP >= levelRole.ReqVEXP):
                await handle_roles(self, data, l, levelRole, x, user_id)
            elif levelRole.Type == 'OR' and (EXP >= levelRole.ReqEXP or vEXP >= levelRole.ReqVEXP):
                await handle_roles(self, data, l, levelRole, x, user_id)
            elif levelRole.Type == 'COMBINED' and ((EXP + vEXP) >= (levelRole.ReqEXP + levelRole.ReqVEXP)):
                await handle_roles(self, data, l, levelRole, x, user_id)
            else:
                continue
            break
        else:
            break

async def handle_activity(self, data, type="chat"):
    session = self.db.sql.session()
    if type == "chat":
        user_id = data.author.id
    else:
        user_id = data.user_id
    
    from ..database import alchemy as db
    e = session.query(db.UserLevels).filter(db.UserLevels.GuildID == data.guild_id).filter(db.UserLevels.UserID == user_id).first()
    
    #activity_roles = self.cache[data.guild_id].activityRoles
    activity_roles = session.query(db.ActivityRoles).filter(db.ActivityRoles.GuildID == data.guild_id).order_by(db.ActivityRoles.ActivityPeriod.asc()).all()
    from datetime import datetime, timedelta
    for x, activityRole in enumerate(activity_roles):
        if activityRole.ActivityPeriod <= e.TopActivityPeriod:
            continue
        if x != 0:
            delta = activity_roles[x - 1].ActivityPeriod * 60
        else:
            delta = 10
        if datetime.now() - e.LastActivityCheck >= timedelta(minutes=delta):
            if type == "chat":
                _activity = self.db.influx.get_chat_activity(data.guild_id, user_id, activityRole.ReqChatActivity)
            else:
                _activity = self.db.influx.get_voice_activity(data.guild_id, user_id, activityRole.ReqVoiceActivity)
            e.LastActivityCheck = datetime.now()
            if activityRole.RoleID not in data.member.roles and _activity != []:
                await self.add_guild_member_role(data.guild_id, user_id, activityRole.RoleID, "Activity Role")
                e.TopActivityPeriod = activityRole.ActivityPeriod
                if x != 0:
                    await self.remove_guild_member_role(data.guild_id, user_id, activity_roles[x-1].RoleID, "Activity Role")
            elif activityRole.RoleID in data.member.roles and _activity == []:
                await self.remove_guild_member_role(data.guild_id, user_id, activityRole.RoleID, "Activity Role")
                e.TopActivityPeriod = 0
            else:
                continue
            session.commit()


def task_check_activity():
    from ..database import database
    from ..database import alchemy as db
    _db = database.Database()
    s = _db.sql.session()
    activity_roles = s.query(db.ActivityRoles).order_by(db.ActivityRoles.ActivityPeriod.asc()).all()
    for x, activityRole in enumerate(activity_roles):
        chat = _db.influx.get_total_chat_activity(activityRole.ReqChatActivity)
        voice = _db.influx.get_total_voice_activity(activityRole.ReqVoiceActivity)
        users = s.query(db.UserLevels).filter(db.UserLevels.TopActivityPeriod == activityRole.ActivityPeriod).all()
        for user in users:
            if user.UserID in chat or user.UserID in voice:
                continue
            user.TopActivityPeriod += 1
            #await self.remove_guild_member_role(user.GuildID, user.UserID, activityRole.RoleID, "Activity Role Cleanup")
    s.commit()

async def exp(self, data):
    last = self.cache[data.guild_id].cooldowns.has(data.guild_id, data.author.id, "ChatExp")
    if not last and (len(set(data.content.split(' '))) >= 2):
        from ..database import models, log, types
        session = self.db.sql.session()
        user = models.User.fetch_or_add(session, id=data.author.id)
        #server = models.Server.fetch_or_add(session, id=data.guild_id)
        log.Statistic.increment(session, data.guild_id, data.author.id, types.Statistic.Chat)
        self.cache[data.guild_id].cooldowns.store(data.guild_id, data.author.id, "ChatExp")
        #await handle_exp(self, data, e)
        from MFramework.database.alchemy.types import Flags
        if self.cache[data.guild_id].is_tracking(Flags.Activity):
            self.db.influx.commitMessage(data.guild_id, data.channel_id, data.author.id, len(set(data.content.split(' '))))
