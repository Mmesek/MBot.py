from MFramework import Bot, Guild, Snowflake
from sqlalchemy.orm import Query, Session

from bot.cache.channels import Channels
from bot.cache.database import fetch_or_add
from bot.cache.roles import Roles
from bot.database import models as db


class Experience(Channels, Roles):
    disabled_channels: set[Snowflake]
    """List of channels with disabled XP gain"""
    disabled_roles: set[Snowflake]
    """List of roles with disabled XP gain"""
    level_roles: list[dict[Snowflake, float]]
    """List of Role Rewards for reaching XP thresholds"""
    role_rates: dict[Snowflake, float]
    """Rate of XP gain per role"""
    channel_rates: dict[Snowflake, float]
    """Rate of XP gain in a channel"""

    def __init__(self, *, guild: Guild, **kwargs) -> None:
        self.disabled_channels = set()
        self.disabled_roles = set()
        self.level_roles = []
        self.role_rates = {}
        self.channel_rates = {}

        super().__init__(guild=guild, **kwargs)

    async def initialize(self, bot: Bot, session: Session, guild: Guild = None, **kwargs) -> None:
        await super().initialize(bot=bot, guild=guild, session=session, **kwargs)
        self.server_exp_rate = self.settings.exp_rate or 1.0

    def set_roles(self):
        for id, role in self.roles.items():
            if role.name == "No Exp":
                self.disabled_roles.add(id)
        return super().set_roles()

    def set_channels(self):
        for id, channel in self.channels.items():
            if "bot" in channel.name:
                self.disabled_channels.add(id)
        return super().set_channels()

    async def save_in_database(self, session: Session):
        for channel in self.disabled_channels:
            _channel = await fetch_or_add(db.Channel, session, server_id=self.guild_id, id=channel)
            _channel.exp_rate = 0
            session.merge(_channel)

        for role in self.disabled_roles:
            _role = await fetch_or_add(db.Role, session, server_id=self.guild_id, id=role)
            _role.exp_rate = 0
            session.merge(_role)

        return await super().save_in_database(session)

    async def get_channels(self, channels: Query[db.Channel]):
        _channels = channels.filter(db.Channel.exp_rate).all()

        self.disabled_channels.update([channel.id for channel in _channels if channel.exp_rate == 0])
        self.channel_rates = {channel.id: channel.exp_rate for channel in _channels}

        return await super().get_channels(channels)

    async def get_roles(self, roles: Query[db.Role]):
        levels = roles.filter(db.Role.exp_req).all()
        self.level_roles = sorted(
            {role.id: role.exp_req for role in levels}.items(),
            key=lambda x: x[1],
        )
        rates = roles.filter(db.Role.exp_rate).all()
        self.role_rates = {role.id: role.exp_rate for role in rates}

        return await super().get_roles(roles)
