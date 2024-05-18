from typing import TypeVar

from MFramework import Bot, log
from MFramework.cache.guild import GuildCache
from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.database import models as db

T = TypeVar("T")


async def fetch_or_add(cls: T, session: Session, server_id: int, id: int) -> T:
    """Fetch from database or create new object"""
    if row := session.scalars(select(cls).where(cls.server_id == server_id, cls.id == id)).first():
        return row
    return cls(server_id=server_id, id=id)


class Database(GuildCache):
    settings: db.Server

    async def initialize(self, bot: Bot, session: Session, **kwargs) -> None:
        self.settings = await self.get_guild(session)

        await super().initialize(bot=bot, session=session, **kwargs)

    async def new_guild(self, s: Session) -> db.Server:
        """Creates new guild if it wasn't present in database"""
        log.info("Registering new guild %s", self.guild_id)
        server = db.Server(id=self.guild_id)
        s.add(server)
        await self.save_in_database(s)
        return server

    async def save_in_database(self, session: Session):
        """Saves data to Database"""
        session.commit()

    async def get_guild(self, s: Session) -> db.Server:
        """Retrieves Guild from Database"""
        if server := s.scalars(select(db.Server).where(db.Server.id == self.guild_id)).first():
            return server
        return await self.new_guild(s)
