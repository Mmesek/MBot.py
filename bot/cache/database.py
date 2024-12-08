from MFramework import Bot, log
from MFramework.cache.guild import GuildCache
from sqlalchemy import select

from bot import database as db


class Database(GuildCache):
    settings: db.Server

    async def initialize(self, bot: Bot, session: db.Session, **kwargs) -> None:
        self.settings = await self.get_guild(session)

        await super().initialize(bot=bot, session=session, **kwargs)

    async def new_guild(self, s: db.Session) -> db.Server:
        """Creates new guild if it wasn't present in database"""
        log.info("Registering new guild %s", self.guild_id)
        server = db.Server(id=self.guild_id)
        s.add(server)
        await self.save_in_database(s)
        return server

    async def save_in_database(self, session: db.Session):
        """Saves data to Database"""
        await session.commit()

    async def get_guild(self, s: db.Session) -> db.Server:
        """Retrieves Guild from Database"""
        if server := await s.scalar(select(db.Server).where(db.Server.id == self.guild_id)):
            return server
        return await self.new_guild(s)
