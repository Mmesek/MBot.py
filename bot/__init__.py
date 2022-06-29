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

from MFramework.bot import Bot
from MFramework.database.cache.listeners import create_cache_listeners

from . import database  # noqa: F401
from .cache import Cache

Bot._Cache = Cache

create_cache_listeners(Cache)
