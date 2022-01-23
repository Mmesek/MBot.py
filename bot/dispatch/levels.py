import sqlalchemy as sa

from mlib.database import Base, TimestampUpdate

from MFramework import Bot, Message, onDispatch
from MFramework.database.alchemy.mixins import Snowflake

class User_Experience(TimestampUpdate, Base):
    server_id: Snowflake = sa.Column(sa.ForeignKey("Server.id", ondelete='Cascade', onupdate='Cascade'), primary_key=True, nullable=False, default=0)
    user_id: Snowflake = sa.Column(sa.ForeignKey("User.id", ondelete='Cascade', onupdate='Cascade'), primary_key=True, nullable=False, default=0)
    type: int = sa.Column(sa.Integer, nullable=False, default=0)
    value: float = sa.Column(sa.Float, nullable=False, default=0)
    def __init__(self, server_id: Snowflake, user_id: Snowflake, type: int = 0, value: float = 0) -> None:
        self.server_id = server_id
        self.user_id = user_id
        self.type = type
        self.value = value


@onDispatch(event="message_create")
async def exp(self: Bot, data: Message):
    if (
        data.channel_id in self.cache[data.guild_id].disabled_channels 
        or any(r in data.member.roles for r in self.cache[data.guild_id].disabled_roles)
        or len(set(data.content.split(' '))) < 2
    ):
        return

    last = self.cache[data.guild_id].cooldowns.has(data.guild_id, data.author.id, "ChatExp")
    if last:
        return

    session = self.db.sql.session()
    from ..database import models, types, log
    user = models.User.fetch_or_add(session, id=data.author.id)
    exp = User_Experience.fetch_or_add(session, user_id=data.author.id, server_id=data.author.id)

    role_boosts = 0
    for role in data.member.roles:
        if role in self.cache[data.guild_id].role_rates:
            role_boosts += self.cache[data.guild_id].role_rates.get(role, 0)

    rate = 1 * (self.cache[data.guild_id].exp_rates.get(data.channel_id, 1.0) + role_boosts)

    from MFramework.database import alchemy as db
    boost = user.get_setting(db.types.Setting.Exp) or 1.0
    exp.value += rate * boost
    self.cache[data.guild_id].cooldowns.store(data.guild_id, data.author.id, "ChatExp")

    previous_level = None
    level_up = None

    for role, req in self.cache[data.guild_id].level_roles.items():
        if role in data.member.roles:
            if exp.value < req:
                await self.remove_guild_member_role(data.guild_id, data.author.id, role, "Level Role")
            previous_level = role
        if exp.value >= req:
            level_up = role

    if level_up == previous_level:
        return

    if level_up:
        await self.add_guild_member_role(data.guild_id, data.author.id, level_up, "Level Role")
    if previous_level:
        await self.remove_guild_member_role(data.guild_id, data.author.id, previous_level, "Level Role")
        
    log.Statistic.increment(session, data.guild_id, data.author.id, types.Statistic.Chat)
    if self.cache[data.guild_id].is_tracking(db.types.Flags.Activity):
        self.db.influx.commitMessage(data.guild_id, data.channel_id, data.author.id, len(set(data.content.split(' '))))
