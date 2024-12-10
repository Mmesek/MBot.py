"""
MBot.py
-------

:copyright: (c) 2019-2021 Mmesek
"""

# Do any additional bot initialization (like loading data or setting things up once) as well as GLOBALLY available variables/constants here
import logging

import MFramework
from MFramework import Context as BaseContext
from MFramework.bot import Bot as BaseBot
from MFramework.bot import Snowflake
from MFramework.cache.listeners import create_cache_listeners
from mlib import logger

from bot import database  # noqa: F401
from bot.cache import Cache

log = logging.getLogger("Bot")
log.setLevel(logger.log_level)


class Context(BaseContext):
    cache: Cache = Cache


class Bot(BaseBot):
    _Cache: Cache = Cache
    _Context: Context = Context
    cache: dict[Snowflake, Cache]

    async def init(self):
        await self.db.sql.extend_enums(self.db.sql.session, database.types)


MFramework.Bot = Bot

create_cache_listeners(Cache)
