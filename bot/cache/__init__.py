from MFramework import Bot
from MFramework import Cache as DefaultCache
from MFramework import Guild

from bot.cache import cache, channels, experience, responses, roles, voice


class Cache(
    experience.Experience,
    # roles.ReactionRoles,
    roles.PresenceRoles,
    channels.RPG,
    cache.Tasks,
    cache.Safety,
    cache.Modmail,
    responses.Responses,
    voice.Voice,
    DefaultCache,
):
    def __init__(self, bot: Bot, guild: Guild, **kwargs):
        super().__init__(bot=bot, guild=guild)
