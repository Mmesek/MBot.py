from datetime import timedelta

from MFramework import Bot, Guild
from MFramework.cache.base import Commands
from MFramework.cache.guild import ObjectCollections

from bot.cache.database import Database
from bot.database import Server, types


class Settings(Database, ObjectCollections, Commands):
    flags: int = 0
    """Toggled setting flags"""
    permissions: int = 0
    """Bot's current permissions based on roles"""
    language: str = "en-US"
    """Current guild's locale"""

    async def initialize(self, *, bot: Bot, guild: Guild, **kwargs) -> None:
        await super().initialize(bot=bot, guild=guild, **kwargs)
        await self.load_settings(bot, self.settings)

    async def load_settings(self, bot: Bot, guild: Server):
        if guild.alias:
            self.set_alias(bot, guild.alias)
        self.auto_ban = guild.auto_ban
        self.auto_mute = guild.auto_mute
        self.premium = guild.premium
        self.flags = guild.flags or 0
        self.mute_duration = guild.mute_duration or timedelta(hours=12)
        self.server_exp_rate = guild.exp_rate or 1.0

    def is_tracking(self, flag: types.Flags) -> bool:
        """Checks if tracking is enabled on server"""
        from mlib.utils import bitflag

        return bitflag(self.flags, flag)
