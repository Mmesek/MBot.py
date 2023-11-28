from MFramework.cache.base import Commands
from MFramework.cache.guild import ObjectCollections

from MFramework import Bot, Guild

from ..database import Server
from ..database.alchemy import types
from .database import Database


class Settings(Database, ObjectCollections, Commands):
    flags: int = 0
    """Toggled setting flags"""
    permissions: int = 0
    """Bot's current permissions based on roles"""
    language: str = "en-US"
    """Current guild's locale"""

    async def initialize(self, *, bot: Bot, guild: Guild, **kwargs) -> None:
        await super().initialize(bot=bot, guild=guild, **kwargs)
        await self.load_settings(self.settings)

    async def load_settings(self, guild: Server):
        if guild.alias:
            self.set_alias(guild.alias)
        self.flags = guild.flags or 0

    def is_tracking(self, flag: types.Flags) -> bool:
        """Checks if tracking is enabled on server"""
        from mlib.utils import bitflag

        return bitflag(self.flags, flag)
