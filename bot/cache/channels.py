from MFramework import Bot, Guild, Snowflake
from MFramework.cache.guild import ObjectCollections
from sqlalchemy import Select, select

from bot import database as db
from bot.cache.database import Database


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

    async def initialize(self, bot: Bot, session: db.Session, guild: Guild, **kwargs) -> None:
        await super().initialize(bot=bot, guild=guild, session=session, **kwargs)
        channels = select(db.Channel).filter(db.Channel.server_id == self.guild_id)
        await self.get_channels(session, channels)

        self.set_channels()

    async def get_channels(self, session: db.Session, channels: Select[tuple[db.Channel]]):
        pass

    async def save_in_database(self, session: db.Session):
        if self.nitro_channel:
            nitro_channel = await db.Channel.fetch_or_add(session, server_id=self.guild_id, id=self.nitro_channel)
            nitro_channel.flags |= db.types.Flags.Nitro
            await session.merge(nitro_channel)

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

    async def get_channels(self, session: db.Session, channels: Select[tuple[db.Channel]]):
        rpg_channels = channels.filter(db.Channel.type == "RPG")
        rpg_channels = await session.query(rpg_channels)
        self.rpg_channels = {channel.id for channel in rpg_channels}

        return await super().get_channels(session, channels)
