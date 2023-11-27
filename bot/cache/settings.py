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
        with bot.db.sql.Session() as s:
            g = self.get_guild(s)
            await self.load_settings(g)

    async def load_settings(self, guild: Server):
        self.settings = {
            setting: getattr(value, setting.annotation.__name__.lower()) for setting, value in guild.settings.items()
        }
        for setting, value in guild.settings.items():
            setattr(
                self,
                setting.name.lower(),
                getattr(value, setting.annotation.__name__.lower(), None),
            )
            if setting is types.Setting.Alias:
                self.set_alias(guild.alias)

    def is_tracking(self, flag: types.Flags) -> bool:
        """Checks if tracking is enabled on server"""
        from mlib.utils import bitflag

        return bitflag(self.flags, flag)
