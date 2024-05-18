"""
MBot.py
-------

:copyright: (c) 2019-2021 Mmesek
"""

# Do any additional bot initialization (like loading data or setting things up once) as well as GLOBALLY available variables/constants here
import logging

log = logging.getLogger("Bot")
from mlib import logger

log.setLevel(logger.log_level)

from MFramework.bot import Bot as BaseBot
from MFramework.bot import Snowflake
from MFramework.cache.listeners import create_cache_listeners

from bot import database  # noqa: F401
from bot.cache import Cache

BaseBot._Cache = Cache


class Bot(BaseBot):
    _Cache = Cache
    cache: dict[Snowflake, Cache]


create_cache_listeners(Cache)
