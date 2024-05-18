from MFramework import Bot, Guild, Snowflake
from MFramework.cache.guild import ObjectCollections
from sqlalchemy.orm import Query, Session

from bot.cache.database import Database, fetch_or_add
from bot.database import models as db
from bot.database import types


class Channels(Database, ObjectCollections):
    nitro_channel: Snowflake = None
    """Server's channel for Nitro users"""
    afk_channel: Snowflake = None
    """AFK channel on server"""
    dynamic_channels: dict[Snowflake, Snowflake]
    """List of ephemeral Voice Channels"""

    def __init__(self, *, guild: Guild, **kwargs) -> None:
        self.dynamic_channels = {}
        super().__init__(guild=guild, **kwargs)

    async def initialize(self, bot: Bot, session: Session, guild: Guild, **kwargs) -> None:
        await super().initialize(bot=bot, guild=guild, session=session, **kwargs)
        channels = session.query(db.Channel).filter(db.Channel.server_id == self.guild_id)
        await self.get_channels(channels)

        self.set_channels()

    async def get_channels(self, channels: Query):
        pass

    async def save_in_database(self, session: Session):
        if self.nitro_channel:
            nitro_channel = await fetch_or_add(db.Channel, session, server_id=self.guild_id, id=self.nitro_channel)
            nitro_channel.flags |= types.Flags.Nitro
            session.merge(nitro_channel)

        return await super().save_in_database(session)

    def set_channels(self):
        for id, channel in self.channels.items():
            if "nitro" in channel.name:
                self.nitro_channel = id
            elif channel.type == 2 and channel.name.startswith("#"):
                self.dynamic_channels[id] = id  # Wtf is this?


class RPG(Channels):
    rpg_channels: set[Snowflake]
    """List of RPG channels in guild where auto dice roll is enabled"""
    rpg_dices: list[str]
    """List of emojis to use in a Dice roll"""

    def __init__(self, *, guild: Guild, **kwargs) -> None:
        self.rpg_channels = set()
        self.rpg_dices = []

        super().__init__(guild=guild, **kwargs)

    async def get_channels(self, channels: Query):
        rpg_channels = channels.filter(db.Channel.type == "RPG").all()
        self.rpg_channels = {channel.id for channel in rpg_channels}

        return await super().get_channels(channels)
