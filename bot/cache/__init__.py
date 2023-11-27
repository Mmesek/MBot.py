from MFramework.cache import Cache as mCache

from MFramework import Guild

from . import cache, responses


class Cache(
    cache.Tasks,
    cache.Safety,
    cache.Modmail,
    responses.Responses,
    mCache,
):
    def __init__(self, bot, guild: Guild, rds=None):
        super().__init__(bot=bot, guild=guild, rds=rds)
